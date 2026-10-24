"""The retrieval core: one interface for the MCP tools, the CLI and the tests.

It is opened on a Knowledge Base and one Release, and never mixes Releases (ADR 0005).
"""

from __future__ import annotations

import difflib
import re
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NamedTuple, Self

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.index import name_key, open_read_only
from cst_help_mcp.locator import document_part
from cst_help_mcp.model import CODE_KINDS, SEPARATOR, NavTree

MAX_HITS = 10
_CANDIDATES = 100  # Sections each index contributes before the tiers are merged
_SNIPPET_WORDS = 24
_RRF_K = 60  # the usual constant of reciprocal rank fusion
# VBA code calls the Application object's methods without an object; its help page is "Project Object".
_OBJECT_ALIASES = {"application": "project"}

SearchKind = Literal["prose", "code", "all"]
# How a Section's own score and its Document's are put on one scale before they are added: raw BM25,
# each divided by the best score of its index for the query, or reciprocal rank fusion.
Fusion = Literal["sum", "normalised", "rank"]


@dataclass(frozen=True)
class Ranking:
    """BM25 weights of the word indexes' fields, and how their two scores combine.

    A Section's own fields are title, headings and body; its Document's are author keywords and
    table-of-contents paths. The Document's score counts for every Section and comes from short rows,
    so its weights are much lower for the same pull. They were tuned on the benchmark's solver and
    how-to questions (docs/benchmark.toml); `cst-help benchmark` tries others.
    """

    title: float = 10.0
    headings: float = 3.0
    body: float = 1.0
    keywords: float = 0.5
    toc_paths: float = 0.25
    fusion: Fusion = "sum"

    def scores(self, index: str, weights: tuple[float, ...]) -> str:
        """SQL selecting the rowid and score of each row of a word index that matches the parameter;
        lower is better."""
        score = {
            "sum": "raw",
            "normalised": "-(raw / min(raw) OVER ())",
            "rank": f"-1.0 / ({_RRF_K} + rank() OVER (ORDER BY raw))",
        }[self.fusion]
        bm25 = f"bm25({index}, {', '.join(str(float(w)) for w in weights)})"
        # bm25() can't be used in a window function, so it is computed first.
        return (
            f"SELECT id, {score} AS score"
            f" FROM (SELECT rowid AS id, {bm25} AS raw FROM {index} WHERE {index} MATCH ?)"
        )


DEFAULT_RANKING = Ranking()

NAV_TREES: dict[NavTree, str] = {"toc": "table of contents", "keywords": "keyword index"}


class _NavRow(NamedTuple):
    """A navigation entry as browse reads it."""

    id: int
    key: str
    name: str
    locator: str | None
    children: int


class _ApiSection(NamedTuple):
    """A Section that search answers with an API Entry: the entry's Locator and snippet."""

    locator: str
    snippet: str


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
    generated: bool  # written in an agent session, such as a Guide
    heuristic: bool  # found by the build's heuristics, such as a Usage

    @property
    def labels(self) -> list[str]:
        """The hit's Area, kind and flags, as the CLI and the MCP server show them."""
        flags = [name for name, on in (("generated", self.generated), ("heuristic", self.heuristic)) if on]
        return [self.area, self.kind, *flags]


@dataclass(frozen=True)
class BrowseEntry:
    name: str
    locator: str | None  # None for a book or keyword that is no Document of its own
    children: int  # the entries below it

    def __str__(self) -> str:
        below = f" ({self.children} entries below)" if self.children else ""
        return f"{self.name}{below}"


@dataclass(frozen=True)
class NavEntry:
    path: list[str]  # the names from the top level down to the entry
    locator: str | None
    children: int


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
        key = _api_key(name)
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

    def search(
        self,
        query: str,
        areas: list[str] | None = None,
        kind: SearchKind = "all",
        limit: int = MAX_HITS,
        ranking: Ranking = DEFAULT_RANKING,
    ) -> list[SearchHit]:
        """Ranked Sections for plain words and partial identifiers. Raw query text never reaches FTS5.

        API Entries named in the query come first, as lookup orders them. Words the word indexes hold
        are ranked by BM25. Other words of three or more characters, such as ``MeshProp``, are
        matched inside Section names by the trigram index; Sections that match them come next.
        """
        if areas:
            self._check_areas(areas)
        scope, params = self._scope(areas, kind)
        api = self._api_sections(query, scope, params)
        words = re.findall(r"\w+", query)
        indexed = {w for w in words if self._in_word_index(w)}
        known = _match([w for w in words if w in indexed])
        partial = _match([w for w in words if w not in indexed and len(w) >= 3])
        # A Section's score adds its own fields' and its Document's; BM25 scores are negative.
        section_scores = ranking.scores("sections_fts", (ranking.title, ranking.headings, ranking.body))
        document_scores = ranking.scores("documents_fts", (ranking.keywords, ranking.toc_paths))
        by_words = self._ranked(
            f"WITH w AS ({section_scores}), d AS ({document_scores}),"
            " scores AS (SELECT id, score FROM w UNION ALL SELECT s.id, d.score FROM d JOIN sections s ON s.document = d.id)"
            f" SELECT s.id FROM scores JOIN sections s ON s.id = scores.id WHERE {scope}"
            " GROUP BY s.id ORDER BY sum(scores.score)",
            [known, known, *params] if known else None,
        )
        by_names = self._ranked(
            "SELECT s.id FROM sections_trigram t JOIN sections s ON s.id = t.rowid"
            f" WHERE sections_trigram MATCH ? AND {scope} ORDER BY bm25(sections_trigram)",
            [partial, *params] if partial else None,
        )
        names = set(by_names)
        ranked = dict.fromkeys([*api, *(i for i in by_words if i in names), *by_names, *by_words])
        return self._hits(list(ranked)[: max(1, min(limit, MAX_HITS))], api, known)

    def _api_sections(self, query: str, scope: str, params: list[str]) -> dict[int, _ApiSection]:
        """The Sections of the API Entries named by identifiers in the query, as lookup orders them.

        Each comes with the entry's own Locator and a snippet of its signature and description.
        """
        found: dict[int, _ApiSection] = {}
        for name in filter(_is_identifier, re.findall(r"\w+(?:\.\w+)*", query)):
            key = _api_key(name)
            rows = self._con.execute(
                "SELECT s.id, a.locator, a.signature, a.description FROM api_entries a"
                f" JOIN sections s ON s.id = a.section WHERE (a.qualified_key = ? OR a.member_key = ?) AND {scope}"
                " ORDER BY a.qualified_key = ? DESC, a.area, a.qualified_name, a.locator",
                [key, key, *params, key],
            )
            for section, locator, signature, description in rows:
                found.setdefault(section, _ApiSection(locator, _leading_words(f"{signature}: {description}")))
        return found

    def _in_word_index(self, word: str) -> bool:
        sql = "SELECT 1 FROM sections_vocab WHERE term = ? UNION ALL SELECT 1 FROM documents_vocab WHERE term = ?"
        return self._con.execute(sql, (word.lower(), word.lower())).fetchone() is not None

    def _scope(self, areas: list[str] | None, kind: SearchKind) -> tuple[str, list[str]]:
        """The SQL condition on Sections ``s`` that keeps a search within its Release, Areas and kind."""
        sql = "s.release = ?"
        params = [self.release]
        if areas:
            sql += f" AND s.id IN (SELECT section FROM section_areas WHERE area IN ({_placeholders(areas)}))"
            params.extend(areas)
        if kind != "all":
            code_kinds = sorted(CODE_KINDS)
            negation = "" if kind == "code" else "NOT "
            sql += f" AND s.kind {negation}IN ({_placeholders(code_kinds)})"
            params.extend(code_kinds)
        return sql, params

    def _ranked(self, sql: str, params: list[str] | None) -> list[int]:
        """Section ids, best first; none when there is nothing to match."""
        if params is None:
            return []
        return [row[0] for row in self._con.execute(f"{sql} LIMIT ?", [*params, _CANDIDATES])]

    def _hits(self, sections: list[int], api: dict[int, _ApiSection], words: str | None) -> list[SearchHit]:
        """The hits for Section ids, in their order.

        A hit for an API Entry has the entry's Locator and snippet; others have a snippet of where the
        words match in the body, or else the body's first words.
        """
        marks = _placeholders(sections)
        snippets = {section: hit.snippet for section, hit in api.items()}
        if words:
            snippets |= {
                section: " ".join(snippet.split())
                for section, snippet in self._con.execute(
                    f"SELECT rowid, snippet(sections_fts, 2, '', '', ' ... ', {_SNIPPET_WORDS}) FROM sections_fts"
                    f" WHERE sections_fts MATCH ? AND rowid IN ({marks})",
                    [words, *sections],
                )
                if section not in snippets
            }
        rest = [section for section in sections if section not in snippets]
        snippets |= {
            section: _leading_words(body)
            for section, body in self._con.execute(
                f"SELECT rowid, body FROM sections_fts WHERE rowid IN ({_placeholders(rest)})", rest
            )
        }
        rows = self._con.execute(
            "SELECT id, locator, release, area, kind, title, heading_path, generated, heuristic FROM sections"
            f" WHERE id IN ({marks})",
            sections,
        )
        hits = {
            section: SearchHit(
                api[section].locator if section in api else locator,
                release,
                area,
                kind,
                title,
                heading_path,
                snippets[section],
                bool(generated),
                bool(heuristic),
            )
            for section, locator, release, area, kind, title, heading_path, generated, heuristic in rows
        }
        return [hits[section] for section in sections]

    def document_of(self, locator: str) -> str | None:
        """The Locator of the Document a source path's Locator is served as: its own, or that of the
        Document it is an Alias of; None when the Knowledge Base doesn't hold it."""
        try:
            row = self._con.execute(
                "SELECT document FROM document_locators WHERE release = ? AND locator = ?",
                (self.release, document_part(locator)),
            ).fetchone()
        except sqlite3.OperationalError:
            raise KnowledgeBaseError(
                f"The Knowledge Base at {self.path} was assembled before it recorded source Locators; rebuild it"
            ) from None
        return str(row[0]) if row else None

    def api_entries(self) -> list[ApiEntryHit]:
        """Every API Entry of the Release, by qualified name."""
        rows = self._con.execute(
            "SELECT qualified_name, area, release, signature, description, locator, title, source_path"
            " FROM api_entries WHERE release = ? ORDER BY qualified_key, area, locator",
            (self.release,),
        )
        return [ApiEntryHit(*row) for row in rows]

    def nav_entries(self, tree: NavTree) -> list[NavEntry]:
        """Every entry of the table of contents or the keyword index, each with the names leading to it."""
        rows = self._con.execute(
            "SELECT id, parent, name, locator, children FROM nav_entries WHERE release = ? AND tree = ?"
            " ORDER BY id",
            (self.release, tree),
        )
        entries: dict[int, NavEntry] = {}
        for id_, parent, name, locator, children in rows:
            path = [*(entries[parent].path if parent in entries else []), name]
            entries[id_] = NavEntry(path, locator, children)
        return list(entries.values())

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
            sql += f" AND parent IN ({_placeholders(parents)})"
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


def _api_key(name: str) -> str:
    """A name as the API Entry table matches it: lower case, with object aliases resolved."""
    key = name.strip().lower()
    obj, dot, member = key.partition(".")
    if dot and obj in _OBJECT_ALIASES:
        key = f"{_OBJECT_ALIASES[obj]}.{member}"
    return key


def _is_identifier(word: str) -> bool:
    """Whether a query word is written like an API name: dotted, with an underscore, or camelCase."""
    return "." in word or "_" in word or re.search(r"[a-z][A-Z]", word) is not None


def _match(terms: list[str]) -> str | None:
    """An FTS5 expression matching any of the terms, each quoted so FTS5 reads it as a string."""
    return " OR ".join(f'"{t}"' for t in terms) or None


def _placeholders(values: Sequence[object]) -> str:
    """SQL parameter markers for the values of an ``IN (...)`` list."""
    return ", ".join("?" * len(values))


def _leading_words(text: str) -> str:
    """The text's first words, as the snippet of a Section the words do not match in its body."""
    words = text.split()
    return " ".join(words[:_SNIPPET_WORDS]) + (" ..." if len(words) > _SNIPPET_WORDS else "")


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
