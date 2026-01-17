#!/usr/bin/env python3
"""Central orchestration for ClipAI CLI and clipboard watcher flows."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import List, Sequence, TextIO

from clipboard_io import write_clipboard
from config_loader import load_config
from config_paths import get_config_path
from notifier import Notifier
from openai_client import complete_prompt
from trigger_parser import extract_prompt

DEFAULT_INSTALL_CMD = "curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/clipai/main/install.sh | bash"
ENV_HIDE_COMMAND = "CLIPAI_HIDE_COMMAND"
ENV_HIDE_DELAY = "CLIPAI_HIDE_DELAY"


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

        if args.background_hide:
            return self._handle_hide_notification()

        if args.prompt:
            prompt = " ".join(args.prompt).strip()
            return self._handle_direct_prompt(prompt, worker=args.worker, wait=args.wait)

        return self._handle_watcher(stdin)

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="clipai")
        parser.add_argument("--version", action="store_true", help="Show version and exit")
        parser.add_argument("--upgrade", action="store_true", help="Upgrade clipai via installer")
        parser.add_argument("--wait", action="store_true", help="Run prompt synchronously")
        parser.add_argument(
            "--_worker",
            dest="worker",
            action="store_true",
            default=False,
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            "--_notify-hide",
            dest="background_hide",
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

    def _handle_direct_prompt(self, prompt: str, worker: bool = False, wait: bool = False) -> int:
        if not prompt:
            return 0

        cfg = load_config()
        notifier = Notifier(cfg)

        if not cfg.get("openai_api_key"):
            config_path = get_config_path()
            sys.stderr.write(f"clipai: missing openai_api_key in {config_path}\n")
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
            self._notify(notifier, success=False)
            return 1

        if not result:
            self._notify(notifier, success=False)
            return 1

        try:
            write_clipboard(result)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
            sys.stderr.flush()
            self._notify(notifier, success=False)
            return 1

        self._notify(notifier, success=True)
        return 0

    def _handle_watcher(self, stdin: TextIO) -> int:
        text = stdin.read()
        parsed = extract_prompt(text)
        if parsed is None:
            return 0

        indent, prompt = parsed

        cfg = load_config()
        notifier = Notifier(cfg)

        if not cfg.get("openai_api_key"):
            # Missing key: stay quiet so systemd service can run even before config exists
            return 0

        try:
            result = complete_prompt(prompt, cfg)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error calling OpenAI: {exc}\n")
            sys.stderr.flush()
            self._notify(notifier, success=False)
            return 0

        if not result:
            self._notify(notifier, success=False)
            return 0

        result = self._apply_indent(result, indent)
        try:
            write_clipboard(result)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"clipai: error writing clipboard: {exc}\n")
            sys.stderr.flush()
            self._notify(notifier, success=False)
            return 0

        self._notify(notifier, success=True)
        return 0

    def _handle_hide_notification(self) -> int:
        command_json = os.environ.get(ENV_HIDE_COMMAND)
        if not command_json:
            return 0

        try:
            command = json.loads(command_json)
        except json.JSONDecodeError:
            return 0

        if not self._is_command_sequence(command):
            return 0

        delay_raw = os.environ.get(ENV_HIDE_DELAY, "0")
        try:
            delay = float(delay_raw)
        except (TypeError, ValueError):
            delay = 0.0

        delay = max(0.0, min(delay, 60.0))
        if delay > 0:
            time.sleep(delay)

        try:
            subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
        except Exception:
            pass
        return 0

    def _notify(self, notifier: Notifier, *, success: bool) -> None:
        if success:
            notifier.notify_success()
        else:
            notifier.notify_failure()
        self._schedule_hide(notifier)

    def _schedule_hide(self, notifier: Notifier) -> None:
        command = notifier.hide_command
        if not command:
            return

        env = os.environ.copy()
        env[ENV_HIDE_COMMAND] = json.dumps(command)
        env[ENV_HIDE_DELAY] = str(max(0.0, notifier.hide_delay))

        cmd = self._self_command(["--_notify-hide"])
        try:
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                env=env,
            )
        except Exception:
            pass

    def _spawn_prompt_worker(self, prompt: str) -> None:
        cmd = self._self_command(["--_worker", prompt])
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

    @staticmethod
    def _is_command_sequence(value: object) -> bool:
        return isinstance(value, list) and all(isinstance(item, str) for item in value)

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
