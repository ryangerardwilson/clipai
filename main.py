#!/usr/bin/env python3
"""Entry point for ClipAI.

Reads clipboard content from stdin (as provided by `wl-paste --watch`),
parses trigger text, calls OpenAI, and writes the response back to the clipboard.

This file is intended to be the PyInstaller entrypoint (`--name clipai`).
"""
import argparse
import subprocess
import sys

from clipboard_io import write_clipboard
from clipboard_watcher import run
from config_loader import load_config
from openai_client import complete_prompt

INSTALL_CMD = "curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/clipai/main/install.sh | bash"


def get_version() -> str:
    try:
        from _version import __version__  # type: ignore

        return __version__
    except Exception:  # noqa: BLE001
        return "dev"


def upgrade() -> int:
    return subprocess.call(["bash", "-c", INSTALL_CMD])


def run_direct_prompt(prompt: str) -> int:
    prompt = prompt.strip()
    if not prompt:
        return 0

    cfg = load_config()
    key = cfg.get("openai_api_key")
    if not key:
        sys.stderr.write("clipai: missing openai_api_key in ~/.config/clipai/config.json\n")
        return 1

    try:
        result = complete_prompt(prompt, cfg)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"clipai: error calling OpenAI: {exc}\n")
        return 1

    if result:
        try:
            write_clipboard(result)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="clipai")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade clipai via installer")
    parser.add_argument("prompt", nargs="*", help="Prompt to run directly")
    args = parser.parse_args()

    if args.version:
        print(get_version())
        return 0

    if args.upgrade:
        return upgrade()

    if args.prompt:
        prompt = " ".join(args.prompt)
        return run_direct_prompt(prompt)

    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
