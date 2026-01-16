#!/usr/bin/env python3
"""Clipboard watcher invoked by wl-paste --watch.

Reads stdin (clipboard contents), checks for trigger, calls OpenAI, writes result to clipboard.
Gracefully no-ops if config or key is missing.
"""
from __future__ import annotations

import sys
from typing import Optional

from config_loader import load_config
from trigger_parser import extract_prompt
from openai_client import complete_prompt
from clipboard_io import write_clipboard


def _apply_indent(text: str, indent: str) -> str:
    if not indent:
        return text
    lines = text.splitlines(True)  # Keep line endings
    return "".join((indent + line) if line.endswith("\n") else (indent + line) for line in lines)


def run() -> None:
    text = sys.stdin.read()
    parsed = extract_prompt(text)
    if parsed is None:
        return  # Not for us

    indent, prompt = parsed

    cfg = load_config()
    if not cfg.get("openai_api_key"):
        # Missing key: stay quiet so systemd service can run even before config exists
        return

    try:
        result = complete_prompt(prompt, cfg)
    except Exception as exc:  # noqa: BLE001
        # Fail quietly to avoid crash-loop; you can add logging later if desired
        sys.stderr.write(f"clipai: error calling OpenAI: {exc}\n")
        sys.stderr.flush()
        return

    if result:
        result = _apply_indent(result, indent)
        try:
            write_clipboard(result)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
            sys.stderr.flush()


__all__ = ["run"]
