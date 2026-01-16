#!/usr/bin/env python3
"""Entry point for ClipAI.

Reads clipboard content from stdin (as provided by `wl-paste --watch`),
parses trigger text, calls OpenAI, and writes the response back to the clipboard.

This file is intended to be the PyInstaller entrypoint (`--name clipai`).
"""
import argparse
import subprocess
import sys

from clipboard_watcher import run


INSTALL_CMD = "curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/clipai/main/install.sh | bash"


def get_version() -> str:
    try:
        from _version import __version__  # type: ignore

        return __version__
    except Exception:  # noqa: BLE001
        return "dev"


def upgrade() -> int:
    return subprocess.call(["bash", "-c", INSTALL_CMD])


def main() -> int:
    parser = argparse.ArgumentParser(prog="clipai")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade clipai via installer")
    args = parser.parse_args()

    if args.version:
        print(get_version())
        return 0

    if args.upgrade:
        return upgrade()

    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
