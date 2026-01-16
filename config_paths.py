#!/usr/bin/env python3
"""XDG-aware config paths for clipai."""
from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "clipai"
CONFIG_BASENAME = "config.json"


def get_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / APP_NAME / CONFIG_BASENAME


__all__ = ["get_config_path"]
