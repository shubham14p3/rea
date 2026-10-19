"""The assistant: slash commands, conversation memory, and Claude chat."""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from . import desktop, llm, rea
from .config import Settings
from .voice import listen, speak

SYSTEM_PROMPT = """You are JARVIS, a calm, precise, and quietly witty personal AI assistant.
You address the user as {user}. Keep answers short and direct unless detail is requested.
Never suggest destructive shell commands without flagging them clearly first.
You can run REA (Reverse Engineer Anything) via /teardown and /rea. Use REA only on software
the user owns or is authorized to examine, and say so if a request looks otherwise.
Current local time: {now}. OS: {os}."""

HELP = """Commands:
  /help                   show this list
  /time                   local date and time
  /reset                  clear conversation memory
  /node                   check Node.js version for REA
  /rea-setup              register REA with your coding agents
  /rea <args>             run the REA CLI, e.g. /rea --help
  /teardown <path>        analyze an extracted JS/Electron app and save the report
  /voice on|off           read replies aloud (needs pyttsx3)
  /listen                 take one spoken command from the microphone
  /open <app>             open an allowlisted app (see /apps)
  /apps                   list the apps JARVIS may open
  /quit                   exit
Anything else is a conversation with Claude."""


@dataclass
class Reply:
    text: str
    quit: bool = False


@dataclass
class Assistant:
    settings: Settings
    sender: Callable[[dict], str] | None = None  # override for tests
    runner: Callable[[list[str]], rea.RunResult] = rea.run_rea
    clock: Callable[[], datetime] = datetime.now
    node_version: Callable[[], str] | None = None
    speaker: Callable[[str], bool] = speak
    listener: Callable[[], str | None] = listen
    opener: Callable[[str], str] = desktop.open_app
    history: list[dict] = field(default_factory=list)
    voice_out: bool = False

    # -- public -----------------------------------------------------------

    def handle(self, line: str) -> Reply:
        line = line.strip()
        if not line:
            return Reply("")
        if line.startswith("/"):
            return self._command(line)
        return self._chat(line)

    # -- commands ---------------------------------------------------------

    def _command(self, line: str) -> Reply:
        parts = line.split()
        cmd, args = parts[0].lower(), parts[1:]
        handlers: dict[str, Callable[[list[str]], Reply]] = {
            "/help": lambda a: Reply(HELP),
            "/quit": lambda a: Reply(f"Goodbye, {self.settings.user_name}.", quit=True),
            "/reset": self._reset,
            "/time": lambda a: Reply(self.clock().strftime("%A %d %B %Y, %H:%M:%S")),
            "/node": lambda a: self._node(),
            "/rea-setup": lambda a: self._rea(["setup"]),
            "/rea": self._rea_passthrough,
            "/teardown": self._teardown,
            "/voice": self._voice,
            "/listen": self._listen,
            "/open": self._open,
            "/apps": lambda a: Reply("Allowed apps: " + (", ".join(desktop.available_apps()) or "none")),
        }
        handler = handlers.get(cmd)
        if handler is None:
            return Reply(f"Unknown command: {cmd}. Type /help.")
        return handler(args)

    def _reset(self, _args: list[str]) -> Reply:
        self.history.clear()
        return Reply("Memory cleared.")

    def _node(self) -> Reply:
        version = self.node_version() if self.node_version else self._detect_node()
        if version is None:
            return Reply("Node.js not found. REA needs Node 22.19+, 24.11+, or 26+.")
        if rea.node_supported(version):
            return Reply(f"Node {version} is supported by REA.")
        return Reply(f"Node {version} is too old for REA. Need 22.19+, 24.11+, or 26+.")

    def _rea_passthrough(self, args: list[str]) -> Reply:
        if not args:
            return Reply("Usage: /rea <command> [args], e.g. /rea --help")
        return self._rea(args)

    def _rea(self, args: list[str]) -> Reply:
        result = self.runner(rea.build_argv(args))
        return self._format_run(result)

    def _teardown(self, args: list[str]) -> Reply:
        if not args:
            return Reply("Usage: /teardown <path to extracted app folder>")
        target = " ".join(args)
        try:
            argv = rea.analyze_js_argv(target)
        except ValueError as exc:
            return Reply(str(exc))
        result = self.runner(argv)
        if result.exit_code != 0:
            return self._format_run(result)
        title = f"JS teardown: {target.rstrip('/').split('/')[-1]}"
        body = "```json\n" + result.stdout.strip() + "\n```"
        path = rea.save_teardown(self.settings.brain_dir, title, body, self.clock())
        return Reply(f"Teardown saved to {path}")

    def _voice(self, args: list[str]) -> Reply:
        if args and args[0].lower() in ("on", "off"):
            self.voice_out = args[0].lower() == "on"
            return Reply(f"Voice output {'on' if self.voice_out else 'off'}.")
        return Reply("Usage: /voice on|off")

    def _listen(self, _args: list[str]) -> Reply:
        heard = self.listener()
        if not heard:
            return Reply("I didn't catch that.")
        reply = self.handle(heard)
        return Reply(f'Heard: "{heard}"\n{reply.text}', quit=reply.quit)

    def _open(self, args: list[str]) -> Reply:
        if not args:
            return Reply("Usage: /open <app>. See /apps.")
        return Reply(self.opener(" ".join(args)))

    @staticmethod
    def _format_run(result: rea.RunResult) -> Reply:
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        if result.exit_code == 0:
            return Reply(out or "Done.")
        return Reply(f"REA exited with code {result.exit_code}.\n{err or out}")

    @staticmethod
    def _detect_node() -> str | None:
        if shutil.which("node") is None:
            return None
        try:
            return subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=10
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

    # -- chat -------------------------------------------------------------

    def _chat(self, text: str) -> Reply:
        if not self.settings.api_key:
            return Reply("Set ANTHROPIC_API_KEY to talk with me.")
        self.history.append({"role": "user", "content": text})
        system = SYSTEM_PROMPT.format(
            user=self.settings.user_name,
            now=self.clock().strftime("%A %d %B %Y, %H:%M"),
            os=platform.system(),
        )
        payload = llm.build_payload(self.settings.model, system, self.history)
        try:
            answer = self.sender(payload) if self.sender else llm.send(self.settings.api_key, payload)
        except llm.LLMError as exc:
            self.history.pop()  # keep history consistent: no unanswered user turn
            return Reply(f"API error: {exc}")
        self.history.append({"role": "assistant", "content": answer})
        if self.voice_out:
            self.speaker(answer)
        return Reply(answer)
