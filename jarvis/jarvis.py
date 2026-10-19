#!/usr/bin/env python3
"""JARVIS - a personal AI assistant CLI built on Claude, with REA reverse-engineering tools.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python jarvis.py

Commands inside the prompt:
    /rea-setup              register REA (rea-agents) with your coding agents
    /rea <args...>          run the REA CLI directly, e.g. /rea analyze-javascript-application ./app --json
    /time                   show local time
    /reset                  clear conversation memory
    /quit                   exit
Anything else is sent to Claude as a conversation.
"""

from __future__ import annotations

import datetime as dt
import os
import platform
import shutil
import subprocess
import sys

try:
    import anthropic
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency. Run: pip install -r requirements.txt")

MODEL = os.environ.get("JARVIS_MODEL", "claude-haiku-5-5")
USER_NAME = os.environ.get("JARVIS_USER", "Shubham")

SYSTEM_PROMPT = f"""You are JARVIS, a calm, precise, and quietly witty personal AI assistant.
You address the user as {USER_NAME}. Keep answers short and direct unless detail is requested.
You can suggest shell commands; never run destructive commands without explicit confirmation.
You have access to REA (Reverse Engineer Anything) through the /rea command, which inspects
apps, binaries and websites locally. Use REA only for software the user owns or is authorized to analyze.
"""

REA_PACKAGE = "rea-agents@latest"


def run(cmd: list[str], timeout: int = 600) -> int:
    """Run a command, streaming output to the terminal. Returns exit code."""
    if shutil.which(cmd[0]) is None:
        print(f"[jarvis] '{cmd[0]}' not found on PATH.")
        return 127
    try:
        return subprocess.run(cmd, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print("[jarvis] command timed out.")
        return 124


def rea(args: list[str]) -> None:
    """Forward arguments to the REA CLI via npx."""
    if not args:
        print("Usage: /rea <command> [args]   (e.g. /rea --help)")
        return
    run(["npx", "-y", REA_PACKAGE, *args])


def rea_setup() -> None:
    """Register REA with your agents. Node.js 22.19+ / 24.11+ / 26+ is required."""
    print("[jarvis] Launching REA setup (you will be asked to approve changes)...")
    run(["npx", "-y", REA_PACKAGE, "setup"])


def local_time() -> str:
    return dt.datetime.now().strftime("%A %d %B %Y, %H:%M:%S")


def handle_command(line: str, history: list[dict]) -> bool:
    """Return True if the line was a slash command and was handled."""
    parts = line.strip().split()
    cmd, args = parts[0].lower(), parts[1:]

    if cmd == "/quit":
        print("Goodbye, " + USER_NAME + ".")
        raise SystemExit(0)
    if cmd == "/reset":
        history.clear()
        print("[jarvis] Memory cleared.")
        return True
    if cmd == "/time":
        print(local_time())
        return True
    if cmd == "/rea-setup":
        rea_setup()
        return True
    if cmd == "/rea":
        rea(args)
        return True
    return False


def chat(client: anthropic.Anthropic, history: list[dict], user_text: str) -> str:
    history.append({"role": "user", "content": user_text})
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT + f"\nCurrent local time: {local_time()}. OS: {platform.system()}.",
        messages=history,
    )
    reply = "".join(block.text for block in response.content if block.type == "text")
    history.append({"role": "assistant", "content": reply})
    return reply


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")

    client = anthropic.Anthropic()
    history: list[dict] = []
    print(f"JARVIS online. Good {'morning' if dt.datetime.now().hour < 12 else 'day'}, {USER_NAME}.")
    print("Type /quit to exit, /rea-setup to connect REA.\n")

    while True:
        try:
            line = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.startswith("/"):
            if handle_command(line, history):
                continue
            print(f"[jarvis] Unknown command: {line.split()[0]}")
            continue
        try:
            print(f"jarvis > {chat(client, history, line)}\n")
        except anthropic.APIError as exc:
            history.pop()  # drop the unanswered user turn
            print(f"[jarvis] API error: {exc}")


if __name__ == "__main__":
    main()
