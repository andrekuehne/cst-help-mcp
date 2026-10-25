"""Link resolution, the build's second pass.

Readers record each link's href relative to the release folder. Once every Document is
read, an inventory of their source paths, Aliases and anchors resolves the links, without
regard to case, to Locators.
"""

from __future__ import annotations

import os
import posixpath
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from cst_help_mcp.locator import anchor_for
from cst_help_mcp.model import Document, Link, LinkStatus

_URL = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
_TOPIC_SUFFIXES = (".htm", ".html")


@dataclass(frozen=True)
class SourceLink:
    """A link as the report lists it: the linking Document's source path and the link's href."""

    source: str
    href: str


@dataclass
class LinkReport:
    statuses: Counter[LinkStatus] = field(default_factory=Counter)
    # Outside links by where they lead: a topic's help project, or another file's type.
    outside: Counter[str] = field(default_factory=Counter)
    unresolved: list[SourceLink] = field(default_factory=list)
    # Resolved links whose fragment names nothing in the target Document's source.
    missing_anchors: list[SourceLink] = field(default_factory=list)


def is_url(href: str) -> bool:
    return _URL.match(href) is not None


def normalise_href(href: str, source_path: str) -> str | None:
    """A URL as written, or a path relative to the release folder with its fragment.

    Relative paths resolve against ``source_path``. Script links (``javascript:``) and
    empty hrefs give None.
    """
    href = href.strip()
    if not href:
        return None
    if _URL.match(href):
        return None if href.lower().startswith("javascript:") else href
    path, _, fragment = href.replace("\\", "/").partition("#")
    resolved = (
        posixpath.normpath(posixpath.join(posixpath.dirname(source_path), path)) if path else source_path
    )
    return f"{resolved}#{fragment}" if fragment else resolved


class Inventory:
    """Every Document by its source path and its Aliases' paths, and their anchors, matched without regard to case."""

    def __init__(self, docs: Iterable[Document]) -> None:
        docs = list(docs)
        self._by_path = {path.lower(): doc for doc in docs for path in (doc.source_path, *doc.aliases)}
        self._anchors = {
            doc.locator: {a.lower(): a for section in doc.sections for a in section.anchors} for doc in docs
        }

    def document(self, path: str) -> Document | None:
        return self._by_path.get(path.lower())

    def anchor(self, doc: Document, fragment: str) -> str | None:
        """The Section anchor a fragment names; anchors generated from a source id that is no valid fragment match it too."""
        known = self._anchors[doc.locator]
        return known.get(fragment.lower()) or known.get(anchor_for(fragment))

    def locate(self, href: str) -> str | None:
        """The Locator a path leads to, with the anchor its fragment names, if it matches one."""
        path, _, fragment = href.partition("#")
        doc = self.document(path)
        if doc is None:
            return None
        anchor = self.anchor(doc, fragment) if fragment else None
        return f"{doc.locator}#{anchor}" if anchor else doc.locator


def resolve_links(docs: list[Document], inventory: Inventory, on_disk: ReleaseFiles) -> LinkReport:
    """Set every link's status and target, and report them.

    A link is resolved when it leads to a Document or Alias, external when it is a URL,
    outside when its file exists but is no Document of this Build (a project not read or
    filtered out, a PDF, an image), and unresolved when its file exists nowhere in the
    release folder.
    """
    report = LinkReport()
    for doc in docs:
        for link in doc.links:
            if _URL.match(link.href):
                link.status = "external"
            else:
                _resolve(doc, link, inventory, on_disk, report)
            report.statuses[link.status] += 1
    return report


def _resolve(
    doc: Document, link: Link, inventory: Inventory, on_disk: ReleaseFiles, report: LinkReport
) -> None:
    path, _, fragment = link.href.partition("#")
    target = inventory.document(path)
    if target is None:
        if on_disk.exists(path):
            link.status = "outside"
            report.outside[_where(path)] += 1
        else:
            link.status = "unresolved"
            report.unresolved.append(SourceLink(doc.source_path, link.href))
        return
    link.status = "resolved"
    link.target = target.locator
    if not fragment:
        return
    anchor = inventory.anchor(target, fragment)
    if anchor:
        link.target += f"#{anchor}"
    elif fragment.lower() not in {a.lower() for a in target.source_anchors}:
        # The source names this fragment nowhere; an id inside a paragraph is merely not a Section.
        report.missing_anchors.append(SourceLink(doc.source_path, link.href))


def _where(path: str) -> str:
    """``Online Help/mergedProjects/DES`` for a topic in that project; ``.pdf`` for a PDF."""
    parts = PurePosixPath(path)
    if parts.suffix.lower() not in _TOPIC_SUFFIXES:
        return parts.suffix.lower() or "(no extension)"
    depth = 3 if parts.parts[1:2] == ("mergedProjects",) else 2
    return "/".join(parts.parts[: min(depth, len(parts.parts) - 1)]) or "(release folder)"


class ReleaseFiles:
    """The files in the release folders, found by relative path without regard to case.

    Each top-level folder is read on first use.
    """

    def __init__(self, release_folders: Iterable[Path]) -> None:
        self._folders = list(release_folders)
        self._paths: dict[str, Path] = {}
        self._walked: set[str] = set()

    def exists(self, path: str) -> bool:
        return self.find(path) is not None

    def find(self, path: str) -> Path | None:
        """The file a path relative to the release folder names, or None."""
        if path.startswith("../"):
            return None  # above the release folder
        top = path.split("/", 1)[0].lower()
        if top not in self._walked:
            self._walked.add(top)
            for folder in self._folders:
                for entry in folder.iterdir() if folder.is_dir() else ():
                    if entry.name.lower() == top:
                        self._add(folder, entry)
        return self._paths.get(path.lower())

    def _add(self, folder: Path, entry: Path) -> None:
        if entry.is_file():
            self._paths.setdefault(entry.name.lower(), entry)
            return
        for dirpath, _, filenames in os.walk(entry):
            rel = Path(dirpath).relative_to(folder).as_posix()
            for name in filenames:
                self._paths.setdefault(f"{rel}/{name}".lower(), Path(dirpath) / name)
