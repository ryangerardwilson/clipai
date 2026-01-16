# clipai

Clipboard-triggered OpenAI helper. Copy `ai{{ your prompt }}` and the watcher will replace your clipboard with the model response.

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

## Service

Installer installs a user service:

- Unit: `~/.config/systemd/user/clipai-clipboard-watcher.service`
- Logs: `journalctl --user -u clipai-clipboard-watcher -f`

It runs: `wl-paste --watch ~/.clipai/bin/clipai`

## Development

- Entry: `python main.py` (reads stdin, emits to clipboard)
- Requirements: `pip install -r requirements.txt`
- Trigger parsing: `ai{{ ... }}` (multiline supported)
- OpenAI client strips code fences by default.

## Release

GitHub Actions builds a PyInstaller onedir tarball `clipai-linux-x64.tar.gz` from tags `v*` using python-build-standalone (see `.github/workflows/release.yml`).
