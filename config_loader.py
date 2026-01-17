#!/usr/bin/env python3
"""Config loader for clipai.

Loads JSON config from XDG path, applies defaults, and tolerates missing files.
Returns a dict; missing API key is allowed (callers decide how to handle it).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from config_paths import get_config_path

DEFAULTS = {
    "openai_api_key": "",
    "model": "gpt-5.2",
    "system_instruction": "Your role is to simply return a concise code snippet",
    "strip_code_fences": True,
    "notifications": {},
}


def load_config() -> Dict[str, Any]:
    path = get_config_path()
    data: Dict[str, Any] = {}

    if path.is_file():
        try:
            data = json.loads(path.read_text())
        except Exception:  # noqa: BLE001
            data = {}

    # Apply defaults where missing
    cfg = {**DEFAULTS, **data}

    # Allow env override for key (optional, helpful for CI)
    import os

    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        cfg["openai_api_key"] = env_key

    return cfg


__all__ = ["load_config", "DEFAULTS"]
