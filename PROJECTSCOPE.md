# Project Scope

## 1. Project Overview

ClipAI is a **clipboard-triggered + CLI-friendly OpenAI helper** for developers on Wayland.

It watches clipboard text for a trigger (`ai{{ ... }}`), sends the extracted prompt to OpenAI, and replaces the clipboard with the response. It also supports direct CLI prompts that write the response into the clipboard.

ClipAI is intentionally small: it is a “prompt in → clipboard out” tool. It does not aim to be a full AI assistant UI, desktop integration framework, or notification system.

---

## 2. Core Design Principles

- **Clipboard is the interface** – Users confirm completion by pasting.
- **Wayland-first** – Uses `wl-paste --watch` and `wl-copy`.
- **One binary, two modes** – Watcher (stdin trigger) and CLI (direct prompt).
- **Centralized orchestration** – `orchestrator.py` owns top-level logic; `main.py` stays thin.
- **Flat project structure** – Python files live in the repo root.
- **Small, single-purpose modules** – Parsing, config, OpenAI, clipboard I/O stay isolated.
- **Watcher-mode stability** – Never crash-loop; stay quiet on missing config/key.
- **Portability over integrations** – Avoid compositor/session-specific dependencies.

---

## 3. Explicit Non-Goals

- Desktop notifications, toasts, or sounds
- Compositor-specific integration hooks (Hyprland/Sway/GNOME/KDE)
- Progress indicators beyond “paste to check”
- Background job management, queues, or persistence
- GUI/TUI interfaces
- Conversation history, memory, or chat threads
- Plugin systems or scripting frameworks
- Agentic/multi-step AI workflows

If a feature requires knowing the user’s desktop session configuration, it is likely out of scope.

---

## 4. Application Entry & Control Flow

### `main.py`
- Instantiate the orchestrator
- Pass `argv` and `stdin`
- Exit with the orchestrator’s return code

`main.py` must remain thin.

### `orchestrator.py`
- Parse CLI arguments
- Route to CLI vs watcher mode
- Own operational policy (quiet watcher, CLI exit codes, etc.)

---

## 5. Current Mode Semantics

### 5.1 Clipboard watcher mode (stdin-driven)
1. Read stdin text (from `wl-paste --watch`).
2. `trigger_parser.extract_prompt` tries to match `ai{{ ... }}`.
   - No match → exit `0` (no-op).
3. Load config. Missing API key → exit `0` quietly.
4. Call OpenAI (`openai_client.complete_prompt`).
   - Exception → print one stderr line, exit `0`.
   - Empty result → exit `0` (no clipboard write).
5. Apply indentation policy: first line unindented, subsequent lines prefixed with captured indent.
6. Write clipboard via `clipboard_io.write_clipboard`.
   - Failure → print stderr, exit `0`.

Watcher exit code is always `0` to keep systemd services healthy.

### 5.2 CLI direct prompt mode
- Default (`clipai "prompt"`): spawns a hidden `--_worker` process and exits immediately (code `0`). Users paste to check completion.
- `--wait`: run synchronously (no worker) for debugging or scripting.

Worker failure policy:
- Missing API key → stderr + exit `1`.
- OpenAI exception → stderr + exit `1`.
- Empty result → exit `1`.
- Clipboard write failure → stderr + exit `1`.
- Success → clipboard updated, exit `0`.

ClipAI never emits completion notifications; pasting is the confirmation.

---

## 6. Trigger Parsing Rules

- Syntax: `ai{{ ... }}`
- Multiline prompt content supported
- Captured indent is re-applied to all lines except the first

---

## 7. Config & Defaults

- Location: `~/.config/clipai/config.json` (XDG-compliant)
- Missing config is tolerated
- Supported keys:
  - `openai_api_key`
  - `model`
  - `system_instruction`
  - `strip_code_fences`

---

## 8. OpenAI Interaction Model

- Single-shot completion: one prompt → one response
- Output normalized for clipboard use (code fences stripped by default)

---

## 9. Release & Installation Constraints

- Target: Linux x86_64
- Release artifact: PyInstaller onedir tarball
- Installer sets up a user systemd service running `wl-paste --watch ~/.clipai/bin/clipai`

---

## 10. Code Organization Rules

- Flat repo: all `.py` files in root
- `orchestrator.py` owns top-level control flow
- Leaf modules stay narrow:
  - `trigger_parser.py`
  - `config_loader.py` / `config_paths.py`
  - `openai_client.py`
  - `clipboard_io.py`
- Avoid introducing global utility modules or abstraction layers

---

## 11. Target User

- Developers and power users working on Wayland
- Comfortable editing JSON and setting env vars
- Expect to paste to confirm completion

---

## 12. Project Success Criteria

- Clipboard-triggered prompts reliably replace clipboard contents
- CLI prompts update clipboard while returning immediately by default
- Watcher mode remains quiet and stable under systemd
- The codebase stays small, flat, and understandable
- New features do not introduce cross-distro compatibility tax

---

## 13. Roadmap

**Short-term priorities**
- Harden CLI + watcher flows with regression tests for missing config, empty responses, and clipboard write errors.
- Improve error messaging (`stderr`) for common misconfigurations.
- Provide optional `--print` or `--stdout` mode for scripting without clipboard (while keeping clipboard as default).
- Document end-to-end installer/uninstaller workflow.

**Medium-term guardrails**
- Add linting/formatting hooks to keep the flat codebase tidy.
- Explore opt-in request logging (CLI flag) for debugging, scoped per run.
- Evaluate additional prompt triggers (e.g., configurable prefixes) without increasing complexity.

**Explicit non-roadmap (won’t pursue unless scope changes)**
- Desktop notifications or UI indicators
- OS-specific integration layers (portal APIs, DBus messaging, etc.)
- Conversation history or chat threading
- Plugin systems or macro engines
- Non-Wayland backends (X11, macOS, Windows)

These roadmap items must preserve the core principle: ClipAI is a clipboard helper, not an assistant UI.
