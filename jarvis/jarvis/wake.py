"""Wake-word detection for hands-free use.

JARVIS only acts on speech that starts with its name, e.g. "Jarvis, what time is it".
A bare "Jarvis" returns an empty command, which means "I'm listening".
"""

from __future__ import annotations

import re

WAKE_WORD = "jarvis"
# Words that may come right before the wake word ("hey jarvis", "ok jarvis").
_LEAD_INS = {"hey", "ok", "okay", "yo", "hello"}
STOP_PHRASES = ("stop listening", "go to sleep", "goodbye")


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def extract_command(transcript: str, wake: str = WAKE_WORD) -> str | None:
    """Return the text after the wake word, "" for a bare wake word, or None if not addressed to JARVIS."""
    words = _words(transcript)
    if not words:
        return None
    # Addressed only if the name opens the sentence, optionally after "hey"/"ok".
    if words[0] == wake:
        return " ".join(words[1:])
    if len(words) > 1 and words[0] in _LEAD_INS and words[1] == wake:
        return " ".join(words[2:])
    return None


def is_stop_request(command: str) -> bool:
    lowered = " ".join(_words(command))
    return any(lowered == phrase or lowered.startswith(phrase + " ") for phrase in STOP_PHRASES)
