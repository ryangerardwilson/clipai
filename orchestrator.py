#!/usr/bin/env python3
"""Central orchestration for ClipAI CLI and clipboard watcher flows."""
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Sequence, TextIO

from clipboard_io import write_clipboard
from config_loader import load_config
from config_paths import get_config_path
from openai_client import complete_prompt
from trigger_parser import extract_prompt

DEFAULT_INSTALL_CMD = "curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/clipai/main/install.sh | bash"


class Orchestrator:
    """Application orchestrator for ClipAI."""

    def __init__(self, install_cmd: str = DEFAULT_INSTALL_CMD) -> None:
        self.install_cmd = install_cmd

    def run(self, *, argv: Sequence[str], stdin: TextIO) -> int:
        """Parse CLI arguments and dispatch to the appropriate execution mode."""
        parser = self._build_parser()
        args = parser.parse_args(list(argv))

        if args.version:
            return self._handle_version()

        if args.upgrade:
            return self._handle_upgrade()

        if args.prompt:
            prompt = " ".join(args.prompt).strip()
            return self._handle_direct_prompt(prompt)

        return self._handle_watcher(stdin)

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="clipai")
        parser.add_argument("--version", action="store_true", help="Show version and exit")
        parser.add_argument("--upgrade", action="store_true", help="Upgrade clipai via installer")
        parser.add_argument("prompt", nargs="*", help="Prompt to run directly")
        return parser

    def _handle_version(self) -> int:
        print(self._get_version())
        return 0

    def _handle_upgrade(self) -> int:
        return subprocess.call(["bash", "-c", self.install_cmd])

    def _handle_direct_prompt(self, prompt: str) -> int:
        if not prompt:
            return 0

        cfg = load_config()
        if not cfg.get("openai_api_key"):
            config_path = get_config_path()
            sys.stderr.write(f"clipai: missing openai_api_key in {config_path}\n")
            sys.stderr.flush()
            return 1

        try:
            result = complete_prompt(prompt, cfg)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error calling OpenAI: {exc}\n")
            sys.stderr.flush()
            return 1

        if result:
            try:
                write_clipboard(result)
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
                sys.stderr.flush()
                return 1

        return 0

    def _handle_watcher(self, stdin: TextIO) -> int:
        text = stdin.read()
        parsed = extract_prompt(text)
        if parsed is None:
            return 0

        indent, prompt = parsed

        cfg = load_config()
        if not cfg.get("openai_api_key"):
            # Missing key: stay quiet so systemd service can run even before config exists
            return 0

        try:
            result = complete_prompt(prompt, cfg)
        except Exception as exc:  # noqa: BLE001
            # Fail quietly to avoid crash-loop; you can add logging later if desired
            sys.stderr.write(f"clipai: error calling OpenAI: {exc}\n")
            sys.stderr.flush()
            return 0

        if result:
            result = self._apply_indent(result, indent)
            try:
                write_clipboard(result)
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
                sys.stderr.flush()

        return 0

    @staticmethod
    def _apply_indent(text: str, indent: str) -> str:
        if not indent:
            return text
        lines = text.splitlines(True)  # Keep line endings
        if not lines:
            return text
        first = lines[0]
        rest = lines[1:]
        rest_indented = [(indent + line) if line.endswith("\n") else (indent + line) for line in rest]
        return first + "".join(rest_indented)

    @staticmethod
    def _get_version() -> str:
        try:
            from _version import __version__  # type: ignore

            return __version__
        except Exception:  # noqa: BLE001
            return "dev"


__all__ = ["Orchestrator"]
