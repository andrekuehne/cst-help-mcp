"""The Knowledge Base's SQLite index: the exact API Entry table and an FTS5 word index (ADR 0008)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from cst_help_mcp.model import Document

_SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    name TEXT PRIMARY KEY,
    release TEXT NOT NULL,
    build TEXT NOT NULL,
    failed INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS api_entries (
    collection TEXT NOT NULL,
    release TEXT NOT NULL,
    area TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    qualified_key TEXT NOT NULL,
    member_key TEXT,
    signature TEXT NOT NULL,
    description TEXT NOT NULL,
    locator TEXT NOT NULL,
    title TEXT NOT NULL,
    source_path TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS api_entries_qualified ON api_entries (qualified_key);
CREATE INDEX IF NOT EXISTS api_entries_member ON api_entries (member_key);
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY,
    collection TEXT NOT NULL,
    release TEXT NOT NULL,
    area TEXT NOT NULL,
    kind TEXT NOT NULL,
    locator TEXT NOT NULL,
    title TEXT NOT NULL,
    heading_path TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5 (
    title, headings, body, tokenize = 'unicode61'
);
"""


@dataclass(frozen=True)
class IndexedBuild:
    collection: str
    release: str
    build: str
    failed: int
    docs: Iterable[Document]


def open_read_only(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)


def write_index(db_path: Path, builds: Iterable[IndexedBuild]) -> None:
    """Write a new database holding the given Builds. Assembly never changes an existing one."""
    con = sqlite3.connect(db_path)
    try:
        with con:
            con.executescript(_SCHEMA)
            for build in builds:
                con.execute(
                    "INSERT INTO collections VALUES (?, ?, ?, ?)",
                    (build.collection, build.release, build.build, build.failed),
                )
                for doc in build.docs:
                    _insert(con, build.collection, doc)
    finally:
        con.close()


def _insert(con: sqlite3.Connection, collection: str, doc: Document) -> None:
    for entry in doc.api_entries:
        con.execute(
            "INSERT INTO api_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                collection,
                doc.release,
                doc.area,
                entry.qualified_name,
                entry.qualified_name.lower(),
                entry.member_name.lower() if entry.member_name else None,
                entry.signature,
                entry.description,
                f"{doc.locator}#{entry.anchor}",
                doc.title,
                doc.source_path,
            ),
        )
    for section in doc.sections:
        locator = f"{doc.locator}#{section.anchor}" if section.anchor else doc.locator
        headings = " ".join(b.text for b in section.blocks if b.kind == "heading")
        body = "\n".join(b.plain_text() for b in section.blocks if b.kind != "heading")
        cur = con.execute(
            "INSERT INTO sections (collection, release, area, kind, locator, title, heading_path)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                collection,
                doc.release,
                doc.area,
                doc.kind,
                locator,
                doc.title,
                " > ".join(section.heading_path),
            ),
        )
        con.execute(
            "INSERT INTO sections_fts (rowid, title, headings, body) VALUES (?, ?, ?, ?)",
            (cur.lastrowid, doc.title, headings, body),
        )
