"""Helpers for REA (Reverse Engineer Anything).

REA ships as the `rea-agents` npm package. JARVIS never runs it through a shell:
arguments are passed as a list so user input cannot inject shell syntax.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import REA_PACKAGE

# REA requires Node.js 22.19+, 24.11+, or 26+ (see the REA README).
_NODE_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def node_supported(version: str) -> bool:
    """True if a `node --version` string (e.g. 'v22.22.0') meets REA's requirement."""
    match = _NODE_VERSION.match(version.strip())
    if not match:
        return False
    major, minor = int(match.group(1)), int(match.group(2))
    if major == 22:
        return minor >= 19
    if major == 24:
        return minor >= 11
    return major >= 26


def build_argv(args: list[str]) -> list[str]:
    """Argument vector for running the REA CLI through npx. No shell involved."""
    return ["npx", "-y", REA_PACKAGE, *args]


def analyze_js_argv(target: str) -> list[str]:
    """Argument vector for the JavaScript/Electron analysis workflow, as JSON output."""
    if not target.strip():
        raise ValueError("A target path is required.")
    return build_argv(["analyze-javascript-application", target, "--json"])


@dataclass
class RunResult:
    exit_code: int
    stdout: str
    stderr: str


def run_rea(argv: list[str], timeout: int = 900) -> RunResult:
    """Run an argument vector and capture its output."""
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return RunResult(127, "", f"'{argv[0]}' not found on PATH. Install Node.js and npm.")
    except subprocess.TimeoutExpired:
        return RunResult(124, "", "REA timed out.")
    return RunResult(proc.returncode, proc.stdout, proc.stderr)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60] or "teardown"


def save_teardown(brain_dir: Path, title: str, body: str, now: datetime | None = None) -> Path:
    """Write a report into the second-brain folder. Never overwrites an existing file."""
    now = now or datetime.now()
    brain_dir.mkdir(parents=True, exist_ok=True)
    base = f"{now:%Y-%m-%d}-{slugify(title)}"
    path = brain_dir / f"{base}.md"
    counter = 2
    while path.exists():
        path = brain_dir / f"{base}-{counter}.md"
        counter += 1
    header = f"# {title}\n\nSaved {now:%Y-%m-%d %H:%M}. Analysis by REA via JARVIS.\n\n"
    path.write_text(header + body + "\n", encoding="utf-8")
    return path
