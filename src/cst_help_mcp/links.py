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


def resolve_links(docs: list[Document], release_folders: Iterable[Path]) -> LinkReport:
    """Set every link's status and target, and report them.

    A link is resolved when it leads to a Document or Alias, external when it is a URL,
    outside when its file exists but is no Document of this Build (a project not read or
    filtered out, a PDF, an image), and unresolved when its file exists nowhere in the
    release folder.
    """
    by_path = {path.lower(): doc for doc in docs for path in (doc.source_path, *doc.aliases)}
    anchors = {
        doc.locator: {a.lower(): a for section in doc.sections for a in section.anchors} for doc in docs
    }
    on_disk = _Files(release_folders)
    report = LinkReport()
    for doc in docs:
        for link in doc.links:
            if _URL.match(link.href):
                link.status = "external"
            else:
                _resolve(doc, link, by_path, anchors, on_disk, report)
            report.statuses[link.status] += 1
    return report


def _resolve(
    doc: Document,
    link: Link,
    by_path: dict[str, Document],
    anchors: dict[str, dict[str, str]],
    on_disk: _Files,
    report: LinkReport,
) -> None:
    path, _, fragment = link.href.partition("#")
    target = by_path.get(path.lower())
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
    known = anchors[target.locator]
    # Anchors generated from a source id that is no valid fragment still match it.
    anchor = known.get(fragment.lower()) or known.get(anchor_for(fragment))
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


class _Files:
    """The lowercase relative paths of the files in the release folders, read per top-level folder on first use."""

    def __init__(self, release_folders: Iterable[Path]) -> None:
        self._folders = list(release_folders)
        self._paths: set[str] = set()
        self._walked: set[str] = set()

    def exists(self, path: str) -> bool:
        if path.startswith("../"):
            return False  # above the release folder
        top = path.split("/", 1)[0].lower()
        if top not in self._walked:
            self._walked.add(top)
            for folder in self._folders:
                for entry in folder.iterdir() if folder.is_dir() else ():
                    if entry.name.lower() == top:
                        self._add(folder, entry)
        return path.lower() in self._paths

    def _add(self, folder: Path, entry: Path) -> None:
        if entry.is_file():
            self._paths.add(entry.name.lower())
            return
        for dirpath, _, filenames in os.walk(entry):
            rel = Path(dirpath).relative_to(folder).as_posix()
            self._paths.update(f"{rel}/{name}".lower() for name in filenames)
