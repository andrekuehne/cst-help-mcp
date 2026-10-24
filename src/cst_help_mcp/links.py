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
from dataclasses import dataclass
from pathlib import Path

from cst_help_mcp.locator import anchor_for
from cst_help_mcp.model import Document, Link, LinkStatus

_URL = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
# Only links into the help can be broken; links to other parts of a release, such as
# Documentation/ or Licenses/, lead outside the corpus.
_CORPUS = "online help/"


@dataclass(frozen=True)
class UnresolvedLink:
    source: str  # the linking Document's source path
    href: str


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


def resolve_links(docs: list[Document], release_folders: Iterable[Path]) -> Counter[LinkStatus]:
    """Set every link's status and target. Returns the number of links by status."""
    by_path = {path.lower(): doc for doc in docs for path in (doc.source_path, *doc.aliases)}
    anchors = {
        doc.locator: {a.lower(): a for section in doc.sections for a in section.anchors} for doc in docs
    }
    on_disk = _Files(release_folders)
    counts: Counter[LinkStatus] = Counter()
    for doc in docs:
        for link in doc.links:
            _resolve(link, by_path, anchors, on_disk)
            counts[link.status] += 1
    return counts


def unresolved_links(docs: Iterable[Document]) -> list[UnresolvedLink]:
    return [
        UnresolvedLink(doc.source_path, link.href)
        for doc in docs
        for link in doc.links
        if link.status == "unresolved"
    ]


def _resolve(
    link: Link, by_path: dict[str, Document], anchors: dict[str, dict[str, str]], on_disk: _Files
) -> None:
    if _URL.match(link.href):
        link.status = "external"
        return
    path, _, fragment = link.href.partition("#")
    target = by_path.get(path.lower())
    if target is None:
        # A file that exists but is no Document of this Build, such as a PDF or a project left
        # out by the filters, is outside the corpus; a missing file in the help is a broken link.
        missing = path.lower().startswith(_CORPUS) and not on_disk.exists(path)
        link.status = "unresolved" if missing else "outside"
        return
    link.status = "resolved"
    link.target = target.locator
    known = anchors[target.locator]
    # Anchors generated from a source id that is no valid fragment still match it.
    anchor = (known.get(fragment.lower()) or known.get(anchor_for(fragment))) if fragment else None
    if anchor:
        link.target += f"#{anchor}"


class _Files:
    """The lowercase relative paths of every file under the release folders' help, read on first use."""

    def __init__(self, release_folders: Iterable[Path]) -> None:
        self._folders = list(release_folders)
        self._paths: set[str] | None = None

    def exists(self, path: str) -> bool:
        if self._paths is None:
            self._paths = set()
            for folder in self._folders:
                for dirpath, _, filenames in os.walk(folder / "Online Help"):
                    rel = Path(dirpath).relative_to(folder).as_posix()
                    self._paths.update(f"{rel}/{name}".lower() for name in filenames)
        return path.lower() in self._paths
