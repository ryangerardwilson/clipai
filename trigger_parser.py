#!/usr/bin/env python3
"""Parsing the trigger syntax from clipboard text.

Default trigger: ai{{ <prompt> }}
Supports multiline content between the delimiters.
Note: While a generic trigger parser exists internally, only `ai{{ ... }}` is
handled by the application logic.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

TRIGGER_PATTERN = re.compile(
    r"^(?P<indent>[ \t]*)[^\n]*?(?P<tag>[A-Za-z][\w:!-]*)\{\{(?P<body>.*)\}\}\s*$",
    re.DOTALL,
)


def extract_trigger(text: str) -> Optional[Tuple[str, str, str]]:
    """Extract a generic trigger of the form:
    <indent>...<tag>{{<body>}}

    Returns (indent, tag, body) if present, else None.
    """
    if not text:
        return None
    candidate = text.rstrip()
    match = TRIGGER_PATTERN.match(candidate)
    if not match:
        return None
    tag = match.group("tag")
    body = (match.group("body") or "").strip()
    if not body:
        return None
    indent = match.group("indent") or ""
    return indent, tag, body


def extract_prompt(text: str) -> Optional[Tuple[str, str]]:
    """Backward-compatible extractor for ai{{ ... }} prompts.
    Returns (indent, prompt) only when tag == 'ai'.
    """
    parsed = extract_trigger(text)
    if not parsed:
        return None
    indent, tag, body = parsed
    if tag != "ai":
        return None
    return indent, body


__all__ = ["extract_prompt", "extract_trigger"]
