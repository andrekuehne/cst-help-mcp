"""The retrieval core: one interface for the MCP tools, the CLI and the tests.

It is opened on a Knowledge Base and one Release, and never mixes Releases (ADR 0005).
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.index import INDEX_FILE

MAX_HITS = 10
# VBA code calls the Application object's methods without an object; its help page is "Project Object".
_OBJECT_ALIASES = {"application": "project"}


@dataclass(frozen=True)
class ApiEntryHit:
    qualified_name: str
    area: str
    release: str
    signature: str
    description: str
    locator: str
    title: str
    source_path: str


@dataclass(frozen=True)
class SearchHit:
    locator: str
    release: str
    area: str
    kind: str
    title: str
    heading_path: str
    snippet: str


class KnowledgeBase:
    def __init__(self, con: sqlite3.Connection, path: Path, release: str) -> None:
        self._con = con
        self.path = path
        self.release = release
        self.areas = [
            r[0]
            for r in con.execute(
                "SELECT DISTINCT area FROM sections WHERE release = ? ORDER BY area", (release,)
            )
        ]

    @classmethod
    def open(cls, path: Path, release: str | None = None) -> KnowledgeBase:
        db = path / INDEX_FILE
        if not db.is_file():
            raise KnowledgeBaseError(f"No Knowledge Base at {path}: {INDEX_FILE} is missing")
        con = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
        releases = sorted(
            (r[0] for r in con.execute("SELECT DISTINCT release FROM collections")),
            key=lambda r: (len(r), r),
        )
        if not releases:
            raise KnowledgeBaseError(f"The Knowledge Base at {path} holds no Collections")
        if release is None:
            release = releases[-1]
        elif release not in releases:
            raise KnowledgeBaseError(
                f"The Knowledge Base at {path} has no Release '{release}'; available: {', '.join(releases)}"
            )
        return cls(con, path, release)

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def lookup(self, name: str, area: str | None = None) -> list[ApiEntryHit]:
        """Exact API Entries for ``Object.Member``, a bare member or object name; case is ignored."""
        if area:
            self._check_areas([area])
        key = name.strip().lower()
        obj, dot, member = key.partition(".")
        if dot and obj in _OBJECT_ALIASES:
            key = f"{_OBJECT_ALIASES[obj]}.{member}"
        sql = (
            "SELECT qualified_name, area, release, signature, description, locator, title, source_path"
            " FROM api_entries WHERE release = ? AND (qualified_key = ? OR member_key = ?)"
        )
        params: list[str] = [self.release, key, key]
        if area:
            sql += " AND area = ?"
            params.append(area)
        sql += " ORDER BY qualified_key = ? DESC, area, qualified_name, locator"
        params.append(key)
        return [ApiEntryHit(*row) for row in self._con.execute(sql, params)]

    def search(self, query: str, areas: list[str] | None = None, limit: int = MAX_HITS) -> list[SearchHit]:
        """Ranked Sections for plain words. Raw query text never reaches FTS5."""
        if areas:
            self._check_areas(areas)
        words = re.findall(r"\w+", query)
        if not words:
            return []
        # Any word may match; BM25 ranks Sections that match more of them higher.
        match = " OR ".join(f'"{w}"' for w in words)
        sql = (
            "SELECT s.locator, s.release, s.area, s.kind, s.title, s.heading_path,"
            " snippet(sections_fts, 2, '', '', ' ... ', 24)"
            " FROM sections_fts JOIN sections s ON s.id = sections_fts.rowid"
            " WHERE sections_fts MATCH ? AND s.release = ?"
        )
        params: list[str | int] = [match, self.release]
        if areas:
            sql += f" AND s.area IN ({', '.join('?' * len(areas))})"
            params.extend(areas)
        sql += " ORDER BY bm25(sections_fts, 10.0, 5.0, 1.0) LIMIT ?"
        params.append(max(1, min(limit, MAX_HITS)))
        return [
            SearchHit(locator, release, area, kind, title, heading_path, " ".join(snippet.split()))
            for locator, release, area, kind, title, heading_path, snippet in self._con.execute(sql, params)
        ]

    def _check_areas(self, areas: list[str]) -> None:
        for area in areas:
            if area not in self.areas:
                raise KnowledgeBaseError(
                    f"Unknown Area '{area}' in Release {self.release}; available: {', '.join(self.areas)}"
                )
