# JARVIS

A personal AI assistant that talks to Claude and drives [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) to analyze apps, binaries and websites you're authorized to examine. Each analysis is saved as a note in a local "second brain" folder.

JARVIS uses only the Python standard library. No packages to install.

## Requirements

- Python 3.10+
- Node.js 22.19+, 24.11+, or 26+ (for REA)
- An Anthropic API key

## Setup

```bash
cd jarvis
export ANTHROPIC_API_KEY=sk-ant-...   # PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
python jarvis.py
```

Optional environment variables:

| Variable          | Default                  | Purpose                              |
| ----------------- | ------------------------ | ------------------------------------ |
| `ANTHROPIC_API_KEY` | (required for chat)    | Your Claude API key                  |
| `JARVIS_MODEL`    | `claude-haiku-5-5`       | Claude model to use                  |
| `JARVIS_USER`     | `Shubham`                | Name JARVIS addresses you by         |
| `JARVIS_BRAIN_DIR`| `~/jarvis-brain`         | Folder where teardown notes are saved |

## Commands

| Command                  | What it does                                               |
| ------------------------ | ---------------------------------------------------------- |
| `/help`                  | List commands                                              |
| `/node`                  | Check Node.js is new enough for REA                        |
| `/rea-setup`             | Register REA with your coding agents (asks for approval)   |
| `/rea <args>`            | Run the REA CLI, e.g. `/rea --help`                        |
| `/teardown <path>`       | Analyze an extracted JS/Electron app, save the report      |
| `/voice on\|off`         | Read replies aloud (needs `pyttsx3`)                       |
| `/time`                  | Local date and time                                        |
| `/reset`                 | Clear conversation memory                                  |
| `/quit`                  | Exit                                                       |

Anything without a leading `/` is a conversation with Claude.

## Voice

Typed mode works with no extra installs. Voice needs three packages on your machine:

```powershell
pip install pyttsx3 SpeechRecognition PyAudio
python jarvis.py --voice
```

- **Hands-free:** say "Jarvis, open calculator" or "Jarvis, what can you do". JARVIS ignores speech that doesn't start with its name. Say "stop listening" or press Ctrl+C to end.
- **One command:** type `/listen` in typed mode to speak a single command.
- **Speech out:** `/voice on` reads every reply aloud.
- **Offline recognition (optional):** `pip install faster-whisper`, then set `JARVIS_STT=whisper`. The first run downloads a model.

Tips:
- Use headphones. Otherwise JARVIS can hear its own voice and respond to it.
- The default recognizer, Google's web service, needs internet access.

## Opening apps

`/open <app>` and "Jarvis, open <app>" open apps from a fixed list. `/apps` shows the list. Windows: notepad, calculator, explorer. macOS: notes, calculator, finder, safari. JARVIS never runs other commands.

## Example: teardown to notes

```text
you > /teardown /absolute/path/to/extracted-app
jarvis > Teardown saved to /home/you/jarvis-brain/2026-10-19-js-teardown-extracted-app.md
```

The report includes modules, imports, and Electron boundaries, each with the evidence REA found.

## Using REA through your coding agent

`/rea-setup` registers REA's MCP server with Claude Code, Codex, Cursor and others. Restart your agent afterward, then ask it, for example:

> Understand how search works in the Notes app, show me the evidence, and build a similar feature for my project.

## Safety

- Analysis runs locally. Only analyze software you own or have permission to examine.
- REA does not provide licenses for commercial tools such as Hopper, IDA or JEB.
- JARVIS passes REA arguments as a list, not through a shell, so paths can't inject commands.

## Development

```bash
cd jarvis
python -m unittest discover -s tests -t .
```

## Layout

```
jarvis.py            entry point
jarvis/config.py     settings from environment variables
jarvis/assistant.py  commands, conversation memory, chat
jarvis/llm.py        Claude Messages API client (stdlib only)
jarvis/rea.py        REA helpers: Node check, argv, teardown notes
jarvis/voice.py      optional speech in/out
jarvis/cli.py        terminal loop
tests/               unit tests (no network needed)
```

## Roadmap

- Wake word and a desktop or tray UI
- Local actions: open apps, read and write notes
- Web teardown through REA's browser analysis
