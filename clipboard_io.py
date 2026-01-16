#!/usr/bin/env python3
"""Clipboard helpers using wl-clipboard."""
from __future__ import annotations

import subprocess


def write_clipboard(text: str) -> None:
    # Requires wl-copy to be installed
    subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)


__all__ = ["write_clipboard"]
