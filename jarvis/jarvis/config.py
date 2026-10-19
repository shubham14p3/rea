"""Runtime settings, read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL = "claude-haiku-5-5"
DEFAULT_USER = "Shubham"
DEFAULT_BRAIN_DIR = Path.home() / "jarvis-brain"
REA_PACKAGE = "rea-agents@latest"


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    user_name: str
    brain_dir: Path

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        brain = env.get("JARVIS_BRAIN_DIR")
        return cls(
            api_key=env.get("ANTHROPIC_API_KEY") or None,
            model=env.get("JARVIS_MODEL", DEFAULT_MODEL),
            user_name=env.get("JARVIS_USER", DEFAULT_USER),
            brain_dir=Path(brain).expanduser() if brain else DEFAULT_BRAIN_DIR,
        )
