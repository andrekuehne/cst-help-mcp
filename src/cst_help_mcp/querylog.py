"""The opt-in query log: each search and lookup an agent sends, with the Locators it got back.

It is written only to a file the server is given, never by default and never to stdout, which
carries the MCP protocol. The benchmark runner turns logged queries into draft benchmark entries.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cst_help_mcp.errors import BenchmarkError


class QueryLog:
    """Appends one JSON line per tool call."""

    def __init__(self, path: Path, release: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.release = release

    def record(self, tool: str, arguments: dict[str, Any], locators: Sequence[str]) -> None:
        line = {
            "time": datetime.now(UTC).isoformat(timespec="seconds"),
            "release": self.release,
            "tool": tool,
            **arguments,
            "locators": list(locators),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


def read_query_log(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        raise BenchmarkError(f"Query log not found: {path}") from None
    try:
        return [json.loads(line) for line in lines if line.strip()]
    except json.JSONDecodeError as e:
        raise BenchmarkError(f"{path} is not a query log: {e}") from None
