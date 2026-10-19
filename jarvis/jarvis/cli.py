"""Terminal loop for JARVIS: typed mode, and hands-free voice mode (--voice)."""

from __future__ import annotations

import sys
import time
from datetime import datetime

from .assistant import Assistant
from .config import Settings
from .voice import listen, missing_packages, speak
from .wake import extract_command, is_stop_request


def _greeting(name: str) -> str:
    part = "morning" if datetime.now().hour < 12 else "day"
    return f"JARVIS online. Good {part}, {name}."


def text_loop(assistant: Assistant, name: str) -> None:
    print(_greeting(name))
    print("Type /help for commands, /listen to speak a command, /quit to exit.\n")
    while True:
        try:
            line = input("you > ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        reply = assistant.handle(line)
        if reply.text:
            print(f"jarvis > {reply.text}\n")
        if reply.quit:
            break


def voice_loop(assistant: Assistant, name: str) -> None:
    """Hands-free mode. Acts only on speech that starts with 'Jarvis'."""
    print(_greeting(name))
    print("Hands-free mode: say 'Jarvis, <command>'. Say 'stop listening' or press Ctrl+C to end.\n")
    speak(f"{_greeting(name)} Say Jarvis, followed by your command.")
    while True:
        try:
            heard = listen()
        except KeyboardInterrupt:
            break
        if not heard:
            time.sleep(0.2)  # no mic or nothing said: avoid a busy loop
            continue
        command = extract_command(heard)
        if command is None:
            continue  # not addressed to JARVIS
        if command == "":
            speak("Yes?")
            print("jarvis > Yes?")
            try:
                command = listen() or ""
            except KeyboardInterrupt:
                break
            if not command:
                continue
        print(f'you (voice) > {command}')
        if is_stop_request(command):
            speak("Goodbye.")
            print("jarvis > Goodbye.")
            break
        reply = assistant.handle(command)
        if reply.text:
            print(f"jarvis > {reply.text}\n")
            speak(reply.text)
        if reply.quit:
            break


def run(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    settings = Settings.from_env()
    assistant = Assistant(settings)
    if "--voice" in argv:
        missing = missing_packages()
        if missing:
            print("Voice needs these packages first: pip install " + " ".join(missing))
            print("(Continuing in text mode.)\n")
            text_loop(assistant, settings.user_name)
        else:
            voice_loop(assistant, settings.user_name)
    else:
        text_loop(assistant, settings.user_name)
