#!/usr/bin/env python3
"""Central orchestration for ClipAI CLI and clipboard watcher flows."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import List, Sequence, TextIO

from clipboard_io import write_clipboard
from config_loader import load_config
from config_paths import get_config_path
from openai_client import complete_prompt
from trigger_parser import extract_trigger

DEFAULT_INSTALL_CMD = "curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/clipai/main/install.sh | bash"


class Orchestrator:
    """Application orchestrator for ClipAI."""

    def __init__(self, install_cmd: str = DEFAULT_INSTALL_CMD) -> None:
        self.install_cmd = install_cmd

    def run(self, *, argv: Sequence[str], stdin: TextIO) -> int:
        parser = self._build_parser()
        args = parser.parse_args(list(argv))

        if args.version:
            return self._handle_version()

        if args.upgrade:
            return self._handle_upgrade()

        if args.prompt:
            prompt = " ".join(args.prompt).strip()
            return self._handle_direct_prompt(prompt, worker=args.worker, wait=args.wait)

        return self._handle_watcher(stdin)

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="clipai")
        parser.add_argument("-v", dest="version", action="store_true", help="Show version and exit")
        parser.add_argument("-u", dest="upgrade", action="store_true", help="Upgrade clipai via installer")
        parser.add_argument("-w", dest="wait", action="store_true", help="Run prompt synchronously")
        parser.add_argument(
            "-W",
            dest="worker",
            action="store_true",
            default=False,
            help=argparse.SUPPRESS,
        )
        parser.add_argument("prompt", nargs="*", help="Prompt to run directly")
        return parser

    def _handle_version(self) -> int:
        print(self._get_version())
        return 0

    def _handle_upgrade(self) -> int:
        return subprocess.call(["bash", "-c", self.install_cmd])

    def _handle_direct_prompt(self, prompt: str, worker: bool, wait: bool) -> int:
        if not prompt:
            return 0

        cfg = load_config()
        if not cfg.get("openai_api_key"):
            sys.stderr.write(f"clipai: missing openai_api_key in {get_config_path()}\n")
            sys.stderr.flush()
            return 1

        if not worker and not wait:
            self._spawn_prompt_worker(prompt)
            return 0

        try:
            result = complete_prompt(prompt, cfg)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error calling OpenAI: {exc}\n")
            sys.stderr.flush()
            return 1

        if not result:
            return 1

        try:
            write_clipboard(result)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
            sys.stderr.flush()
            return 1

        return 0

    def _handle_watcher(self, stdin: TextIO) -> int:
        text = stdin.read()
        if self._maybe_pretty_json(text):
            return 0
        trig = extract_trigger(text)
        if trig is None:
            return 0

        indent, tag, body = trig

        if tag == "e":
            return self._handle_execute(indent, body)
        if tag == "ai":
            cfg = load_config()
            if not cfg.get("openai_api_key"):
                return 0
            try:
                result = complete_prompt(body, cfg)
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write(f"clipai: error calling OpenAI: {exc}\n")
                sys.stderr.flush()
                return 0
            if not result:
                return 0
            result = self._apply_indent(result, indent)
            try:
                write_clipboard(result)
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
                sys.stderr.flush()
            return 0

        # Unknown tag: ignore
        return 0

    def _spawn_prompt_worker(self, prompt: str) -> None:
        cmd = self._self_command(["-W", prompt])
        try:
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                env=os.environ.copy(),
            )
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: failed to spawn worker: {exc}\n")
            sys.stderr.flush()

    def _self_command(self, extra_args: Sequence[str]) -> List[str]:
        executable = sys.argv[0] if sys.argv else "clipai"
        if executable.endswith((".py", ".pyc")):
            python = sys.executable or "python3"
            return [python, executable, *extra_args]
        return [executable, *extra_args]

    @staticmethod
    def _apply_indent(text: str, indent: str) -> str:
        if not indent:
            return text
        lines = text.splitlines(True)
        if not lines:
            return text
        first = lines[0]
        rest = lines[1:]
        rest_indented = [(indent + line) if line.endswith("\n") else (indent + line) for line in rest]
        return first + "".join(rest_indented)

    def _maybe_pretty_json(self, text: str) -> bool:
        if not text:
            return False

        stripped = text.strip()
        if not stripped or not stripped.startswith("{") or not stripped.endswith("}"):
            return False

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return False

        pretty = json.dumps(parsed, indent=4, ensure_ascii=False)
        newline_suffix = ""
        if text.endswith("\n"):
            newline_count = len(text) - len(text.rstrip("\n"))
            newline_suffix = "\n" * newline_count

        final_text = pretty + newline_suffix

        if final_text == text:
            return False

        try:
            write_clipboard(final_text)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
            sys.stderr.flush()
            return False

        return True

    def _handle_execute(self, indent: str, command: str) -> int:
        # Execute using the user's shell semantics via bash -lc
        env = os.environ.copy()
        try:
            proc = subprocess.run(
                ["bash", "-lc", command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired:
            try:
                write_clipboard("clipai: execute timeout (5s)\n")
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
                sys.stderr.flush()
            return 0
        except Exception as exc:  # noqa: BLE001
            try:
                write_clipboard(f"clipai: execute error: {exc}\n")
            except Exception as exc2:  # noqa: BLE001
                sys.stderr.write(f"clipai: error writing clipboard: {exc2}\n")
                sys.stderr.flush()
            return 0

        out = (proc.stdout or b"").decode("utf-8", errors="replace")
        err = (proc.stderr or b"").decode("utf-8", errors="replace")

        result = out
        if err:
            if result and not result.endswith("\n"):
                result += "\n"
            result += "--- stderr ---\n" + err
        if proc.returncode != 0:
            if result and not result.endswith("\n"):
                result += "\n"
            result += f"exit {proc.returncode}\n"

        result = self._apply_indent(result, indent)
        try:
            write_clipboard(result)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
            sys.stderr.flush()
        return 0

    @staticmethod
    def _get_version() -> str:
        try:
            from _version import __version__  # type: ignore

            return __version__
        except Exception:  # noqa: BLE001
            return "dev"


__all__ = ["Orchestrator"]
