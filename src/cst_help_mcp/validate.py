"""Check a Knowledge Base's integrity: its pointer, the active Builds and their files, and the links
between the files of each readable view."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError

# Link targets as the renderer writes them: Markdown links and images, and HTML attributes in tables.
_MARKDOWN_TARGET = re.compile(r"\]\((?:<([^>]+)>|([^)\s]+))\)")
_HTML_TARGET = re.compile(r'<(?:a\s[^>]*?href|img\s[^>]*?src)="([^"]*)"')
_FENCED = re.compile(r"^(`{3,}).*?^\1\s*$", re.MULTILINE | re.DOTALL)
# Inline code, such as the signature `Left[$](S$, Len)` in api.md, which holds no link.
_CODE_SPAN = re.compile(r"(`+)[^`\n].*?\1")
_SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:", re.IGNORECASE)


@dataclass(frozen=True)
class CollectionStatus:
    name: str
    build: str
    documents: int
    failed: int


@dataclass
class Validation:
    problems: list[str] = field(default_factory=list)
    collections: list[CollectionStatus] = field(default_factory=list)


def validate(kb_path: Path) -> Validation:
    result = Validation()
    try:
        assembly_id = layout.active_assembly(kb_path)
    except KnowledgeBaseError as e:
        result.problems.append(str(e))
        return result
    assembly = layout.assemblies_dir(kb_path) / assembly_id
    if not (assembly / layout.ASSEMBLY_MANIFEST).is_file():
        result.problems.append(f"The active assembly {assembly} is missing")
        return result
    try:
        builds = layout.assembly_builds(assembly)
    except KnowledgeBaseError as e:
        result.problems.append(str(e))
        return result
    for collection, build in builds.items():
        folder = layout.build_dir(kb_path, collection, build)
        if not (folder / layout.BUILD_MANIFEST).is_file():
            result.problems.append(f"Build {build} of Collection {collection} is missing: {folder}")
            continue
        try:
            manifest = layout.BuildManifest.read(folder)
        except KnowledgeBaseError as e:
            result.problems.append(str(e))
            continue
        result.collections.append(
            CollectionStatus(collection, build, len(manifest.documents), manifest.failed)
        )
        view = kb_path / collection
        result.problems.extend(_check_files(kb_path, folder, manifest.files))
        result.problems.extend(_check_view(kb_path, view, folder / layout.TREE, manifest.files))
        result.problems.extend(_check_entry_files(kb_path, view, folder))
        result.problems.extend(_check_links(kb_path, view))
    return result


def _check_files(kb_path: Path, folder: Path, files: dict[str, str]) -> list[str]:
    problems = []
    for rel, digest in files.items():
        path = folder / rel
        if not path.is_file():
            problems.append(f"{_shown(kb_path, path)} is missing")
        elif layout.sha256(path) != digest:
            problems.append(f"{_shown(kb_path, path)} has changed since it was built")
    return problems


def _check_view(kb_path: Path, view: Path, tree: Path, files: dict[str, str]) -> list[str]:
    """The readable view holds the same files as the active Build's tree; run assemble to restore it."""
    prefix = f"{layout.TREE}/"
    problems = []
    for rel in files:
        if not rel.startswith(prefix):
            continue
        path = view / rel.removeprefix(prefix)
        source = tree / rel.removeprefix(prefix)
        if not path.is_file():
            problems.append(f"{_shown(kb_path, path)} is missing; run cst-help assemble to restore it")
        elif source.is_file() and path.stat().st_size != source.stat().st_size:
            problems.append(
                f"{_shown(kb_path, path)} differs from its Build; run cst-help assemble to restore it"
            )
    return problems


def _check_entry_files(kb_path: Path, view: Path, build: Path) -> list[str]:
    """Every navigation tree the Build found has its entry file in the view, and so have its Library
    code and Material Definitions."""
    trees = layout.read_navigation(build)
    names = [name for tree, (name, _) in layout.ENTRY_FILES.items() if tree in trees]
    names += layout.library_entry_files(layout.read_library_lines(build))
    return [
        f"{_shown(kb_path, view / name)} is missing; run cst-help assemble to restore it"
        for name in names
        if not (view / name).is_file()
    ]


def _check_links(kb_path: Path, view: Path) -> list[str]:
    """Every link and image between the view's Markdown files leads to a file of the view.

    Links are Locators, relative to the view's root. Fragments are not checked: the build report
    lists the fragments that match no anchor.
    """
    problems = []
    for page in sorted(view.rglob("*.md")):
        if page.relative_to(view).parts[0] == layout.WORK_DIR:
            continue  # what agents write there is theirs, not the Knowledge Base's
        text = _CODE_SPAN.sub("", _FENCED.sub("", page.read_text(encoding="utf-8")))
        targets = [a or b for a, b in _MARKDOWN_TARGET.findall(text)]
        targets += [html.unescape(t) for t in _HTML_TARGET.findall(text)]
        for target in dict.fromkeys(targets):
            path = target.partition("#")[0]
            if not path or _SCHEME.match(path):
                continue
            if not (view / path).is_file():
                problems.append(f"{_shown(kb_path, page)} links to {path}, which is missing")
    return problems


def _shown(kb_path: Path, path: Path) -> str:
    """A path as it is reported: relative to the Knowledge Base folder."""
    return path.relative_to(kb_path).as_posix()
