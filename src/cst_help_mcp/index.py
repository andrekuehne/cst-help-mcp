"""The Knowledge Base's SQLite index: the exact API Entry table, FTS5 word indexes of Sections and
of Documents, a trigram index of names (ADR 0008) and the navigation trees."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from cst_help_mcp.locator import locator_for
from cst_help_mcp.model import Document, NavNode, NavTree

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
    source_path TEXT NOT NULL,
    section INTEGER  -- the Section that holds the entry's anchor
);
CREATE INDEX IF NOT EXISTS api_entries_qualified ON api_entries (qualified_key);
CREATE INDEX IF NOT EXISTS api_entries_member ON api_entries (member_key);
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY,
    document INTEGER NOT NULL,  -- the rowid of its Document in documents_fts
    collection TEXT NOT NULL,
    release TEXT NOT NULL,
    area TEXT NOT NULL,
    kind TEXT NOT NULL,
    locator TEXT NOT NULL,
    title TEXT NOT NULL,
    heading_path TEXT NOT NULL,
    generated INTEGER NOT NULL,
    heuristic INTEGER NOT NULL
);
-- Every Area a Section is found under: its Document's own, and those of its Aliases.
CREATE TABLE IF NOT EXISTS section_areas (
    section INTEGER NOT NULL,
    area TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS section_areas_area ON section_areas (area, section);
CREATE INDEX IF NOT EXISTS sections_document ON sections (document);
-- The Locator each source path maps to, its Document's own or an Alias's, and the Document's.
CREATE TABLE IF NOT EXISTS document_locators (
    release TEXT NOT NULL,
    locator TEXT NOT NULL,
    document TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS document_locators_locator ON document_locators (locator);
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5 (title, headings, body, tokenize = 'unicode61');
-- What a Document's Sections share, indexed once per Document: BM25 normalises by the length
-- of a row, so a long keyword list in every Section's row would count against each of them.
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5 (keywords, toc_paths, tokenize = 'unicode61');
-- The terms of the word indexes, so search can tell which query words they hold.
CREATE VIRTUAL TABLE IF NOT EXISTS sections_vocab USING fts5vocab (sections_fts, row);
CREATE VIRTUAL TABLE IF NOT EXISTS documents_vocab USING fts5vocab (documents_fts, row);
-- A Section's names (its title, heading path and API signatures), for partial identifiers.
CREATE VIRTUAL TABLE IF NOT EXISTS sections_trigram USING fts5 (names, tokenize = 'trigram');
-- The table of contents and the keyword index, each in its order.
CREATE TABLE IF NOT EXISTS nav_entries (
    id INTEGER PRIMARY KEY,
    collection TEXT NOT NULL,
    release TEXT NOT NULL,
    tree TEXT NOT NULL,
    parent INTEGER,
    name TEXT NOT NULL,
    name_key TEXT NOT NULL,
    locator TEXT,
    children INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS nav_entries_parent ON nav_entries (tree, parent);
"""


@dataclass(frozen=True)
class IndexedBuild:
    collection: str
    release: str
    build: str
    failed: int
    docs: Iterable[Document]
    navigation: dict[NavTree, list[NavNode]]


def name_key(name: str) -> str:
    """A navigation entry's name as browse paths match it: without regard to case and spacing."""
    return " ".join(name.split()).casefold()


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
                for tree, nodes in build.navigation.items():
                    _insert_nav(con, build.collection, build.release, tree, None, nodes)
    finally:
        con.close()


def _insert(con: sqlite3.Connection, collection: str, doc: Document) -> None:
    sections: dict[str, int] = {}  # each anchor's Section
    document = con.execute(
        "INSERT INTO documents_fts (keywords, toc_paths) VALUES (?, ?)",
        ("\n".join(doc.keywords), "\n".join(doc.toc_paths)),
    ).lastrowid
    con.executemany(
        "INSERT INTO document_locators VALUES (?, ?, ?)",
        [(doc.release, locator_for(path), doc.locator) for path in (doc.source_path, *doc.aliases)],
    )
    for section in doc.sections:
        locator = f"{doc.locator}#{section.anchor}" if section.anchor else doc.locator
        headings = " ".join(b.plain_text() for b in section.blocks if b.kind == "heading")
        body = "\n".join(b.plain_text() for b in section.blocks if b.kind != "heading")
        cur = con.execute(
            "INSERT INTO sections"
            " (document, collection, release, area, kind, locator, title, heading_path, generated, heuristic)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                document,
                collection,
                doc.release,
                doc.area,
                doc.kind,
                locator,
                doc.title,
                " > ".join(section.heading_path),
                doc.generated,
                doc.heuristic,
            ),
        )
        section_id = cur.lastrowid
        assert section_id is not None
        sections.update((anchor, section_id) for anchor in section.anchors)
        con.execute(
            "INSERT INTO sections_fts (rowid, title, headings, body) VALUES (?, ?, ?, ?)",
            (section_id, doc.title, headings, body),
        )
        names = [doc.title, *section.heading_path]
        names += [b.plain_text() for b in section.blocks if b.kind == "api_signature"]
        con.execute(
            "INSERT INTO sections_trigram (rowid, names) VALUES (?, ?)", (section_id, "\n".join(names))
        )
        con.executemany(
            "INSERT INTO section_areas VALUES (?, ?)",
            [(section_id, area) for area in (doc.area, *doc.alias_areas)],
        )
    for entry in doc.api_entries:
        con.execute(
            "INSERT INTO api_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                sections.get(entry.anchor),
            ),
        )


def _insert_nav(
    con: sqlite3.Connection,
    collection: str,
    release: str,
    tree: NavTree,
    parent: int | None,
    nodes: list[NavNode],
) -> None:
    for node in nodes:
        cur = con.execute(
            "INSERT INTO nav_entries (collection, release, tree, parent, name, name_key, locator, children)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                collection,
                release,
                tree,
                parent,
                node.name,
                name_key(node.name),
                node.locator,
                len(node.children),
            ),
        )
        _insert_nav(con, collection, release, tree, cur.lastrowid, node.children)
