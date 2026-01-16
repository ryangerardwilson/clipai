#!/usr/bin/env python3
"""Entry point for ClipAI.

Reads clipboard content from stdin (as provided by `wl-paste --watch`),
parses trigger text, calls OpenAI, and writes the response back to the clipboard.

This file is intended to be the PyInstaller entrypoint (`--name clipai`).
"""
from clipboard_watcher import run


if __name__ == "__main__":
    run()
