#!/usr/bin/env python3
"""PyInstaller entrypoint for ClipAI."""
from __future__ import annotations

import sys

from orchestrator import Orchestrator


def main() -> int:
    orchestrator = Orchestrator()
    return orchestrator.run(argv=sys.argv[1:], stdin=sys.stdin)


if __name__ == "__main__":
    sys.exit(main())
