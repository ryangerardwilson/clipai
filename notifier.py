#!/usr/bin/env python3
"""Notification helper for ClipAI."""
from __future__ import annotations

import os
import subprocess
from typing import Any, List, Optional, Sequence


def _is_command_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and all(isinstance(item, str) for item in value)


class Notifier:
    """Runs user-configured commands to indicate success/failure."""

    def __init__(self, config: dict[str, Any]) -> None:
        notifications = config.get("notifications") or {}
        if not isinstance(notifications, dict):
            notifications = {}

        self.success_command: Optional[List[str]] = self._sanitize_command(
            notifications.get("success_notification_command")
        )
        self.failure_command: Optional[List[str]] = self._sanitize_command(
            notifications.get("failure_notification_command")
        )
        self.hide_command: Optional[List[str]] = self._sanitize_command(
            notifications.get("hide_notification_command")
        )
        self.hide_delay = self._coerce_delay(notifications.get("duration_in_seconds"))

    def notify_success(self) -> None:
        self._run_command(self.success_command)

    def notify_failure(self) -> None:
        self._run_command(self.failure_command)

    @staticmethod
    def _sanitize_command(value: Any) -> Optional[List[str]]:
        if _is_command_sequence(value):
            return list(value)
        return None

    @staticmethod
    def _coerce_delay(value: Any) -> float:
        if isinstance(value, (int, float)) and value > 0:
            return min(float(value), 60.0)
        return 0.0

    def _run_command(self, command: Optional[Sequence[str]]) -> None:
        if not command:
            return
        try:
            _run_detached(command)
        except Exception:
            pass


def _run_detached(command: Sequence[str]) -> None:
    subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy(),
        close_fds=True,
    )


__all__ = ["Notifier"]
