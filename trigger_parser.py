#!/usr/bin/env python3
"""Parsing the trigger syntax from clipboard text.

Default trigger: ai{{ <prompt> }}
Supports multiline content between the delimiters.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

TRIGGER_PATTERN = re.compile(
    r"^(?P<indent>[ \t]*)[^\n]*?ai\{\{(?P<prompt>.*)\}\}\s*$",
    re.DOTALL,
)


def extract_prompt(text: str) -> Optional[Tuple[str, str]]:
    if not text:
        return None

    candidate = text.rstrip()
    match = TRIGGER_PATTERN.match(candidate)
    if not match:
        return None

    prompt = match.group("prompt").strip()
    if not prompt:
        return None

    indent = match.group("indent") or ""
    return indent, prompt


__all__ = ["extract_prompt"]
