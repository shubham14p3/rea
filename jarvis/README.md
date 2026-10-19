# JARVIS

A personal AI assistant CLI powered by Claude, with [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) wired in for analyzing apps, binaries and websites you're authorized to examine.

## Setup

Requirements: Python 3.10+, Node.js 22.19+ (for REA), and an Anthropic API key.

```bash
cd jarvis
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...  # Windows (PowerShell): $env:ANTHROPIC_API_KEY="sk-ant-..."
python jarvis.py
```

Optional environment variables:

| Variable        | Default          | Purpose                    |
| --------------- | ---------------- | -------------------------- |
| `JARVIS_MODEL`  | `claude-haiku-5-5` | Claude model to use      |
| `JARVIS_USER`   | `Shubham`        | Name JARVIS addresses you by |

## Commands

| Command                 | What it does                                             |
| ----------------------- | -------------------------------------------------------- |
| `/rea-setup`            | Registers REA's MCP server with your coding agents       |
| `/rea <args>`           | Runs the REA CLI, e.g. `/rea --help`                     |
| `/rea analyze-javascript-application ./app --json` | Inspects an extracted Electron/JS app |
| `/time`                 | Local date and time                                      |
| `/reset`                | Clears conversation memory                               |
| `/quit`                 | Exits                                                    |

Anything without a leading `/` is a conversation with Claude.

## Using REA

REA is most useful through your coding agent (Claude Code, Codex, Cursor, etc.). Run `/rea-setup` once, restart the agent, then ask it things like:

> Understand how search works in the Notes app, show me the evidence, and build a similar feature for my project.

Analysis runs locally. Only analyze software you own or have permission to examine. REA does not grant any commercial tool licenses (Hopper, IDA, JEB).

## Roadmap ideas

- Voice input/output (e.g. `speech_recognition` + `pyttsx3`)
- Local tools: open apps, read/write notes, system status
- Save teardown reports into a "second brain" folder
- Wake word and a desktop/tray UI
