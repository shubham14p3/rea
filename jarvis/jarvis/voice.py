"""Speech input and output.

Output uses `pyttsx3` (offline; SAPI5 on Windows, NSSpeechSynthesizer on macOS,
espeak on Linux). Input uses `SpeechRecognition` with a microphone.

Both are optional. Every function degrades gracefully: if a package is missing,
`missing_packages()` says which one, and speak/listen return a clear failure
instead of crashing the assistant.
"""

from __future__ import annotations

import importlib
import os
from typing import Optional

REQUIRED = {"pyttsx3": "pyttsx3", "speech_recognition": "SpeechRecognition"}


def missing_packages() -> list[str]:
    """Return pip package names that are not importable (empty list = all good)."""
    missing = []
    for module, pip_name in REQUIRED.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(pip_name)
    return missing


def speak(text: str) -> bool:
    """Speak text aloud. Returns False if speech output is unavailable."""
    if not text.strip():
        return False
    try:
        import pyttsx3  # type: ignore[import-not-found]
    except ImportError:
        return False
    try:
        engine = pyttsx3.init()
        rate = int(os.environ.get("JARVIS_VOICE_RATE", "180"))
        engine.setProperty("rate", rate)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception:  # no audio device, engine failure
        return False


def listen(timeout: float = 6.0, phrase_limit: float = 12.0) -> Optional[str]:
    """Record one phrase from the microphone and return its text, or None.

    Returns None on timeout, silence, unrecognized speech, or a missing
    microphone. Recognition uses Google's web API by default. Set
    JARVIS_STT=whisper to use a local faster-whisper model instead
    (needs `pip install faster-whisper`).
    """
    try:
        import speech_recognition as sr  # type: ignore[import-not-found]
    except ImportError:
        return None
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
    except Exception:  # no microphone, or nothing said before timeout
        return None
    try:
        if os.environ.get("JARVIS_STT", "google").lower() == "whisper":
            model = os.environ.get("JARVIS_WHISPER_MODEL", "base")
            text = recognizer.recognize_faster_whisper(audio, model=model)
        else:
            text = recognizer.recognize_google(audio)
    except Exception:  # unintelligible audio or recognizer error
        return None
    text = (text or "").strip()
    return text or None
