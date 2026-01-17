# clipai

Clipboard-triggered (and CLI-friendly) OpenAI helper. Copy `ai{{ your prompt }}` and the watcher will replace your clipboard with the model response — or just run `clipai "your prompt"` from any shell to get the answer straight into your clipboard.

## Install (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/clipai/main/install.sh | bash
```

Requires Linux x86_64 and `wl-clipboard` (`wl-copy`, `wl-paste`).

## Config

The app reads `~/.config/clipai/config.json` (XDG). If missing, the installer creates a template:

```json
{
  "openai_api_key": "",
  "model": "gpt-5.2",
  "system_instruction": "Your role is to simply return a concise code snippet",
  "strip_code_fences": true
}
```

Set your API key and `chmod 600 ~/.config/clipai/config.json`.

### Optional notifications

You can ask ClipAI to run your own commands when a response finishes:

- `success_notification_command` runs after the clipboard is updated successfully
- `failure_notification_command` runs if the OpenAI call fails, the clipboard write fails, or the model returns an empty string
- `hide_notification_command` runs after `duration_in_seconds`

Each command is configured as a JSON array of **strings**. Pass every argument as a string (e.g. `"6"`, not `6`). Commands run without a shell by default; if you need shell features, wrap them with `bash -lc` explicitly.

Example using a generic notification script:

```json
{
  "openai_api_key": "",
  "model": "gpt-5.2",
  "system_instruction": "Your role is to simply return a concise code snippet",
  "strip_code_fences": true,
  "notifications": {
    "success_notification_command": ["notify.sh", "success"],
    "failure_notification_command": ["notify.sh", "failure"],
    "duration_in_seconds": 5,
    "hide_notification_command": ["notify.sh", "hide"]
  }
}
```

Need shell tricks (like redirects or aliases)?

```json
"success_notification_command": ["bash", "-lc", "notify.sh success >> /tmp/clipai_notify.log 2>&1"]
```

### CLI behaviour

The CLI spawns a background worker for prompts by default so the command returns immediately. Use `--wait` if you want it to block until the response (handy for debugging).

## Service

Installer installs a user service:

- Unit: `~/.config/systemd/user/clipai-clipboard-watcher.service`
- Logs: `journalctl --user -u clipai-clipboard-watcher -f`

It runs: `wl-paste --watch ~/.clipai/bin/clipai`

## Usage

### Clipboard trigger (Wayland)
Copy `ai{{ your prompt }}` to the clipboard — the service sees it, sends it to OpenAI, and swaps the clipboard with the response. The first line of the reply is left unindented (even if you copied from a nested block), so you can hit `o` in Vim or paste anywhere without fighting indentation; subsequent lines mirror whatever indent was before `ai{{ ... }}`.

### Direct CLI mode
Need the answer in code right now? Run:

```bash
clipai "give me the command to search for lines of .py files in which the word 'orchestrator' appears"
```

…and your clipboard is immediately loaded with something like:

```bash
grep -RIn --include='*.py' 'orchestrator' .
```

Paste it wherever you want.

## Development

- Entry: `python main.py` (reads stdin, emits to clipboard)
- Requirements: `pip install -r requirements.txt`
- Trigger parsing: `ai{{ ... }}` (multiline supported, leading indent preserved)
- OpenAI client strips code fences by default.

## Release

GitHub Actions builds a PyInstaller onedir tarball `clipai-linux-x64.tar.gz` from tags `v*` using python-build-standalone (see `.github/workflows/release.yml`).
