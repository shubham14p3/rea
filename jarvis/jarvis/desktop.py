"""Open apps on your computer, from a fixed allowlist only.

JARVIS never runs arbitrary commands. You can only open the apps listed
here, and each one maps to a fixed argument list (no shell), so speech or
text input cannot inject commands. Add entries deliberately.
"""

from __future__ import annotations

import platform
import subprocess
from typing import Callable, Optional

APPS: dict[str, dict[str, list[str]]] = {
    "Windows": {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "explorer": ["explorer.exe"],
    },
    "Darwin": {
        "notes": ["open", "-a", "Notes"],
        "calculator": ["open", "-a", "Calculator"],
        "finder": ["open", "-a", "Finder"],
        "safari": ["open", "-a", "Safari"],
    },
    "Linux": {
        "calculator": ["gnome-calculator"],
        "text editor": ["gedit"],
    },
}


def available_apps(system: Optional[str] = None) -> list[str]:
    system = system or platform.system()
    return sorted(APPS.get(system, {}))


def resolve(name: str, system: Optional[str] = None) -> Optional[list[str]]:
    """Return the fixed argument list for an allowlisted app, or None."""
    system = system or platform.system()
    key = name.strip().lower()
    return APPS.get(system, {}).get(key)


def open_app(
    name: str,
    system: Optional[str] = None,
    launcher: Callable[..., object] = subprocess.Popen,
) -> str:
    """Open an allowlisted app. Returns a message for the user."""
    argv = resolve(name, system)
    if argv is None:
        choices = ", ".join(available_apps(system)) or "none on this system"
        return f"I can't open '{name}'. Allowed here: {choices}."
    try:
        launcher(argv)
    except OSError as exc:
        return f"Could not open {name}: {exc}"
    return f"Opening {name}."
