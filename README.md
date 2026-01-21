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

### CLI behaviour

The CLI spawns a background worker for prompts by default so the command returns immediately. Use `-w` if you want it to block until the response (handy for debugging). ClipAI does not emit completion notifications—if you want to know whether the response is ready, paste.

## Service

Installer installs a user service:

- Unit: `~/.config/systemd/user/clipai-clipboard-watcher.service`
- Logs: `journalctl --user -u clipai-clipboard-watcher -f`

It runs: `wl-paste --watch ~/.clipai/bin/clipai`

## Usage

### Clipboard trigger (Wayland)
Copy `ai{{ your prompt }}` to the clipboard — the service sees it, sends it to OpenAI, and swaps the clipboard with the response. The first line of the reply is left unindented (even if you copied from a nested block), so you can hit `o` in Vim or paste anywhere without fighting indentation; subsequent lines mirror whatever indent was before `ai{{ ... }}`.

If you copy a JSON object (text that starts with `{` and ends with `}`), ClipAI will automatically replace the clipboard with a pretty-printed version using an indent of 4 spaces. This happens even without an API key or trigger syntax.

### Execute trigger (local shell)
Copy `e{{ <shell command> }}` to execute it with your shell (`bash -lc`).

Rules:
- Full shell semantics (pipes, redirects, subshells, expansions) are supported.
- Hard timeout: 5 seconds. On timeout, the clipboard becomes `clipai: execute timeout (5s)`.
- Stdout is copied to the clipboard. If there is stderr, it is appended under a `--- stderr ---` section. Non-zero exit codes append `exit N`.
 - Working directory is the current process working directory. In the systemd user service this is typically `$HOME` unless configured otherwise. Use `cd` inside the command if you need another path.
 
 Optional CWD overrides:
 - Prefix the body with a first line `cwd: /absolute/or/~/path` to run there.
 - Or start the body with an inline token like `@/absolute/or/~/path` followed by a space, then the command.

Examples:
- `e{{ ls -la }}`
- `e{{ git rev-parse --short HEAD }}`
- `e{{ cd ~/project && rg -n "TODO" | head -50 }}`
 - `e{{ cwd: ~/project\nls -la\n}}`
 - `e{{ @~/project rg -n "TODO" | head -50 }}`

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
- Trigger parsing: generic `<tag>{{ ... }}` including `ai{{ ... }}` and `e{{ ... }}` (multiline supported, leading indent preserved)
- OpenAI client strips code fences by default.

## Release

GitHub Actions builds a PyInstaller onedir tarball `clipai-linux-x64.tar.gz` from tags `v*` using python-build-standalone (see `.github/workflows/release.yml`).
