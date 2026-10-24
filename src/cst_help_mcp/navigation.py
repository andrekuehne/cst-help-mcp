"""RoboHelp navigation data: the table of contents, the author keyword index and the context-help maps.

Each lives in a ``*_xml.js`` file holding one JS string assignment, ``gXMLBuffer = "<?xml ...>";``.
It is read by decoding the string's escapes, never by running JS. Child projects' tables of
contents are spliced into the root one where it names them (``<project ref>``). Their paths
are project-relative, use backslashes and mixed case, so they are matched without regard to case.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from cst_help_mcp.errors import BuildError
from cst_help_mcp.links import Inventory, normalise_href
from cst_help_mcp.model import SEPARATOR, Document, NavNode, NavTree

ROOT_PROJECT = "Online Help"

_BUFFER = re.compile(r'gXMLBuffer\s*=\s*"((?:\\.|[^"\\])*)"', re.DOTALL)
_ESCAPE = re.compile(r"\\(u[0-9A-Fa-f]{4}|x[0-9A-Fa-f]{2}|\r\n|.)", re.DOTALL)
_BREADCRUMB_MARKER = re.compile(r"bc-\d+$")
_SIMPLE_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}


def decode_js_string(body: str) -> str:
    """The value of a JS string literal's body: ``\\"``, ``\\\\``, ``\\n``, ``\\uXXXX`` and the rest."""

    def unescape(m: re.Match[str]) -> str:
        seq = m[1]
        if seq[0] in "ux" and len(seq) > 1:
            return chr(int(seq[1:], 16))
        if seq in ("\n", "\r", "\r\n"):
            return ""  # a line continuation
        return _SIMPLE_ESCAPES.get(seq, seq)

    return _ESCAPE.sub(unescape, body)


@dataclass
class Navigation:
    toc: list[NavNode] = field(default_factory=list)
    keywords: list[NavNode] = field(default_factory=list)
    # Context-help map ids by the lowercase source path of their topic.
    context_ids: dict[str, list[str]] = field(default_factory=dict)
    # Where each project's table of contents is spliced in, by lowercase project folder; the
    # breadcrumbs embedded in its topics start below it.
    prefixes: dict[str, list[str]] = field(default_factory=dict)

    def prefix(self, source: str) -> list[str]:
        """Where the project holding a source path (lowercase) is spliced in; the top level if nowhere."""
        folders = [f for f in self.prefixes if source.startswith(f"{f}/")]
        return self.prefixes[max(folders, key=len)] if folders else []

    def trees(self) -> dict[NavTree, list[NavNode]]:
        """The trees a Build keeps; the context-help ids and prefixes only serve the build."""
        return {"toc": self.toc, "keywords": self.keywords}


@dataclass
class NavigationReport:
    toc_entries: int = 0
    # Entries that lead to no Document of the Build: other projects, other files, external pages.
    toc_entries_dropped: int = 0
    keywords: int = 0
    keyword_topics_dropped: int = 0
    context_ids: int = 0  # context-help map ids of Documents of the Build


def read_navigation(release_folders: Iterable[Path]) -> Navigation:
    """The navigation data of every project the root table of contents splices in."""
    navigation = Navigation()
    for release in release_folders:
        _Reader(release, navigation).read()
    navigation.keywords = _merged(navigation.keywords)
    return navigation


class _Reader:
    def __init__(self, release: Path, navigation: Navigation) -> None:
        self.release = release
        self.navigation = navigation

    def read(self) -> None:
        self.navigation.toc.extend(self._project(ROOT_PROJECT, []))

    def _project(self, folder: str, prefix: list[str]) -> list[NavNode]:
        """A project's table of contents with its child projects spliced in; reads its index and maps too."""
        key = folder.lower()
        if key in self.navigation.prefixes:
            return []  # spliced in already
        self.navigation.prefixes[key] = prefix
        self._index(folder)
        self._context_map(folder)
        wiring = self._xml(f"{folder}/whxdata/whtoc_xml.js")
        if wiring is None:
            return []
        root = self._xml(f"{folder}/whxdata/{_js_name(wiring.get('root', 'whtdata0.xml'))}")
        return [] if root is None else self._toc_children(root, folder, prefix)

    def _toc_children(self, element: ET.Element, folder: str, path: list[str]) -> list[NavNode]:
        nodes: list[NavNode] = []
        for child in element:
            if child.tag == "project":
                ref = normalise_href(child.get("ref", ""), f"{folder}/whtdata0.xml")
                if ref:
                    nodes.extend(self._project(ref, path))
            elif child.tag in ("book", "item"):
                node = NavNode(_name(child), href=_href(child.get("url"), folder))
                node.children = self._toc_children(child, folder, [*path, node.name])
                nodes.append(node)
        return nodes

    def _index(self, folder: str) -> None:
        chunks = self._xml(f"{folder}/whxdata/whidx_xml.js")
        for chunk in chunks.iter("chunkinfo") if chunks is not None else ():
            data = self._xml(f"{folder}/whxdata/{_js_name(chunk.get('url', ''))}")
            if data is not None:
                self.navigation.keywords.extend(self._keys(data, folder))

    def _keys(self, element: ET.Element, folder: str) -> list[NavNode]:
        keys = []
        for key in element.findall("key"):
            topics = [NavNode(_name(t), href=_href(t.get("url"), folder)) for t in key.findall("topic")]
            keys.append(NavNode(_name(key), children=[*topics, *self._keys(key, folder)]))
        return keys

    def _context_map(self, folder: str) -> None:
        data = self._xml(f"{folder}/whcsh_xml.js")
        for item in data.iter("item") if data is not None else ():
            path = _href(item.get("topicurl"), folder)
            if path and item.get("mapid"):
                self.navigation.context_ids.setdefault(path.lower(), []).append(str(item.get("mapid")))

    def _xml(self, rel: str) -> ET.Element | None:
        """The XML document a data file holds, or None if the project has no such file."""
        file = self.release / rel
        if not file.is_file():
            return None
        match = _BUFFER.search(file.read_text(encoding="utf-8"))
        if match is None:
            raise BuildError(f"{rel} holds no gXMLBuffer string")
        try:
            return ET.fromstring(decode_js_string(match[1]).encode("utf-8"))
        except ET.ParseError as e:
            raise BuildError(f"{rel} holds no valid XML: {e}") from None


def _js_name(xml_name: str) -> str:
    """``whtdata0.xml`` is published as ``whtdata0_xml.js``."""
    return re.sub(r"\.xml$", "_xml.js", xml_name, flags=re.IGNORECASE)


def _name(element: ET.Element) -> str:
    return " ".join(element.get("name", "").split())


def _href(url: str | None, folder: str) -> str | None:
    """An entry's path relative to the release folder, without the breadcrumb marker on its fragment.

    ``page.htm#bc-1`` (or ``#Anchorbc-1``) opens the page with its second breadcrumb.
    """
    href = normalise_href(url, f"{folder}/whtdata0.xml") if url else None
    if not href:
        return None
    path, _, fragment = href.partition("#")
    fragment = _BREADCRUMB_MARKER.sub("", fragment)
    return f"{path}#{fragment}" if fragment else path


def _merged(keys: list[NavNode]) -> list[NavNode]:
    """Keywords of several projects merged by name, without regard to case, and sorted."""
    by_name: dict[str, NavNode] = {}
    for key in keys:
        kept = by_name.setdefault(key.name.casefold(), NavNode(key.name))
        kept.children.extend(key.children)
    for key in by_name.values():
        topics = [c for c in key.children if c.href is not None or c.locator is not None]
        subkeys = [c for c in key.children if c.href is None and c.locator is None]
        key.children = [*topics, *_merged(subkeys)]
    return sorted(by_name.values(), key=lambda k: k.name.casefold())


def _walk(nodes: list[NavNode], path: list[str]) -> Iterator[tuple[list[str], NavNode]]:
    """Every node with the names of its ancestors."""
    for node in nodes:
        yield path, node
        yield from _walk(node.children, [*path, node.name])


def apply_navigation(docs: list[Document], navigation: Navigation) -> None:
    """Give each Document its table-of-contents paths, keywords and context-help ids, by its source path.

    A Document in no table of contents takes the breadcrumbs embedded in it, below the place
    where its project is spliced in. Runs before Aliases merge, so each Alias brings its own.
    """
    toc_paths: dict[str, list[str]] = {}
    for path, node in _walk(navigation.toc, []):
        if node.href:
            _add(toc_paths, node.href, SEPARATOR.join([*path, node.name]))
    keywords: dict[str, list[str]] = {}
    for path, node in _walk(navigation.keywords, []):
        if node.href:
            _add(keywords, node.href, SEPARATOR.join(path))
    for doc in docs:
        source = doc.source_path.lower()
        doc.toc_paths = toc_paths.get(source) or [
            SEPARATOR.join([*navigation.prefix(source), crumb]) for crumb in doc.breadcrumbs
        ]
        doc.keywords = keywords.get(source, [])
        doc.context_ids = navigation.context_ids.get(source, [])


def _add(paths: dict[str, list[str]], href: str, path: str) -> None:
    found = paths.setdefault(href.partition("#")[0].lower(), [])
    if path not in found:
        found.append(path)


def resolve_navigation(navigation: Navigation, inventory: Inventory) -> NavigationReport:
    """Resolve every entry to a Locator, and drop those that lead to no Document of the Build."""
    report = NavigationReport()
    navigation.toc = _resolved(navigation.toc, inventory, report, keywords=False)
    navigation.keywords = _resolved(navigation.keywords, inventory, report, keywords=True)
    report.context_ids = sum(
        len(ids) for path, ids in navigation.context_ids.items() if inventory.document(path) is not None
    )
    return report


def _resolved(
    nodes: list[NavNode], inventory: Inventory, report: NavigationReport, *, keywords: bool
) -> list[NavNode]:
    kept = []
    for node in nodes:
        node.locator = inventory.locate(node.href) if node.href else None
        node.children = _resolved(node.children, inventory, report, keywords=keywords)
        if keywords:
            node.children = _without_copies(node.children)
        if node.locator is None and not node.children:
            if node.href is not None:
                if keywords:
                    report.keyword_topics_dropped += 1
                else:
                    report.toc_entries_dropped += 1
            continue
        if keywords:
            report.keywords += node.href is None
        else:
            report.toc_entries += 1
        kept.append(node)
    return kept


def _without_copies(children: list[NavNode]) -> list[NavNode]:
    """A keyword's topics without repeats: two of them may be Aliases of one Document."""
    seen: set[str] = set()
    kept = []
    for child in children:
        if child.locator is not None:
            if child.locator in seen:
                continue
            seen.add(child.locator)
        kept.append(child)
    return kept
