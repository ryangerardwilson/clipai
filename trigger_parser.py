#!/usr/bin/env python3
"""Parsing the trigger syntax from clipboard text.

Default trigger: ai{{ <prompt> }}
Supports multiline content between the delimiters.
"""
from __future__ import annotations

import re
from typing import Optional

TRIGGER_PREFIX = "ai{{"
TRIGGER_SUFFIX = "}}"

# Multiline, greedy until last }}
TRIGGER_PATTERN = re.compile(r"^ai\{\{(.*)\}\}$", re.DOTALL)


def extract_prompt(text: str) -> Optional[str]:
    if not text:
        return None
    match = TRIGGER_PATTERN.match(text.strip())
    if not match:
        return None
    prompt = match.group(1).strip()
    return prompt or None


__all__ = ["extract_prompt"]
