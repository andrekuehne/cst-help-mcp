"""The retrieval core: one interface for the MCP tools, the CLI and the tests.

It is opened on a Knowledge Base and one Release, and never mixes Releases (ADR 0005).
"""

from __future__ import annotations

import difflib
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Self

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.index import name_key, open_read_only
from cst_help_mcp.model import SEPARATOR, NavTree

MAX_HITS = 10
# VBA code calls the Application object's methods without an object; its help page is "Project Object".
_OBJECT_ALIASES = {"application": "project"}

NAV_TREES: dict[NavTree, str] = {"toc": "table of contents", "keywords": "keyword index"}


class _NavRow(NamedTuple):
    """A navigation entry as browse reads it."""

    id: int
    key: str
    name: str
    locator: str | None
    children: int


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


@dataclass(frozen=True)
class BrowseEntry:
    name: str
    locator: str | None  # None for a book or keyword that is no Document of its own
    children: int  # the entries below it

    def __str__(self) -> str:
        below = f" ({self.children} entries below)" if self.children else ""
        return f"{self.name}{below}"


@dataclass(frozen=True)
class BrowseResult:
    tree: NavTree
    release: str
    path: list[str]  # the names of the entry browsed, as the help writes them; empty for the top level
    entries: list[BrowseEntry]

    @property
    def title(self) -> str:
        """The tree and the path browsed, such as "Table of contents > 3D Simulation"."""
        return SEPARATOR.join([NAV_TREES[self.tree].capitalize(), *self.path])


class KnowledgeBase:
    def __init__(self, con: sqlite3.Connection, path: Path, release: str) -> None:
        self._con = con
        self.path = path
        self.release = release
        # Collections of this Release whose active Build lost Documents, with how many it lost.
        self.incomplete: dict[str, int] = dict(
            con.execute(
                "SELECT name, failed FROM collections WHERE release = ? AND failed > 0 ORDER BY name",
                (release,),
            ).fetchall()
        )
        self.areas = [
            r[0]
            for r in con.execute(
                "SELECT DISTINCT a.area FROM section_areas a JOIN sections s ON s.id = a.section"
                " WHERE s.release = ? ORDER BY a.area",
                (release,),
            )
        ]

    @classmethod
    def open(cls, path: Path, release: str | None = None) -> KnowledgeBase:
        con = _connect_active(path)
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
            sql += f" AND s.id IN (SELECT section FROM section_areas WHERE area IN ({', '.join('?' * len(areas))}))"
            params.extend(areas)
        sql += " ORDER BY bm25(sections_fts, 10.0, 5.0, 1.0) LIMIT ?"
        params.append(max(1, min(limit, MAX_HITS)))
        return [
            SearchHit(locator, release, area, kind, title, heading_path, " ".join(snippet.split()))
            for locator, release, area, kind, title, heading_path, snippet in self._con.execute(sql, params)
        ]

    def browse(self, path: str = "", tree: NavTree = "toc") -> BrowseResult:
        """The entries below a table-of-contents book or a keyword, given as names joined by ">".

        Names are matched without regard to case and spacing; an empty path gives the top level.
        """
        if tree not in NAV_TREES:
            raise KnowledgeBaseError(f"Unknown tree '{tree}'; available: {', '.join(NAV_TREES)}")
        names = [n for n in (" ".join(part.split()) for part in path.split(">")) if n]
        parents: list[int] | None = None
        found: list[str] = []
        for name in names:
            rows = self._nav_children(tree, parents)
            # Same-named books, such as one per Collection, are browsed together.
            matches = [r for r in rows if r.key == name_key(name) and r.children]
            if not matches:
                raise KnowledgeBaseError(self._not_found(tree, name, found, rows))
            found.append(matches[0].name)
            parents = [r.id for r in matches]
        entries = [BrowseEntry(r.name, r.locator, r.children) for r in self._nav_children(tree, parents)]
        return BrowseResult(tree, self.release, found, entries)

    def _nav_children(self, tree: NavTree, parents: list[int] | None) -> list[_NavRow]:
        sql = "SELECT id, name_key, name, locator, children FROM nav_entries WHERE release = ? AND tree = ?"
        params: list[str | int] = [self.release, tree]
        if parents is None:
            sql += " AND parent IS NULL"
        else:
            sql += f" AND parent IN ({', '.join('?' * len(parents))})"
            params.extend(parents)
        return [_NavRow(*row) for row in self._con.execute(sql + " ORDER BY id", params)]

    def _not_found(self, tree: NavTree, name: str, found: list[str], rows: list[_NavRow]) -> str:
        where = f"under '{SEPARATOR.join(found)}'" if found else "at the top level"
        leaf = next((r for r in rows if r.key == name_key(name)), None)
        if leaf is not None:
            return (
                f"'{leaf.name}' {where} of the {NAV_TREES[tree]} has no entries below it; read {leaf.locator}"
            )
        message = f"No entry '{name}' {where} of the {NAV_TREES[tree]} of Release {self.release}"
        by_key = {r.key: r.name for r in rows if r.children}
        nearest = difflib.get_close_matches(name_key(name), list(by_key), n=3)
        if nearest:
            message += f"; nearest: {', '.join(by_key[k] for k in nearest)}"
        return message

    def _check_areas(self, areas: list[str]) -> None:
        for area in areas:
            if area not in self.areas:
                raise KnowledgeBaseError(
                    f"Unknown Area '{area}' in Release {self.release}; available: {', '.join(self.areas)}"
                )


def _connect_active(path: Path) -> sqlite3.Connection:
    """Open the active assembly's database, read-only, and keep it for the life of the connection."""
    for _ in range(3):
        db = layout.assemblies_dir(path) / layout.active_assembly(path) / layout.INDEX_FILE
        try:
            return open_read_only(db)
        except sqlite3.OperationalError:
            # An assembly may have switched the pointer and pruned this database in the meantime.
            if db.is_file():
                raise
    raise KnowledgeBaseError(f"The Knowledge Base at {path} points at a missing database: {db}")
