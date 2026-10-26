"""Build one Collection: read its Sources into Documents and write them as a new, immutable Build."""

from __future__ import annotations

import fnmatch
import hashlib
import shutil
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, get_args

from cst_help_mcp import layout
from cst_help_mcp.assembly import assemble
from cst_help_mcp.assets import write_assets
from cst_help_mcp.config import CollectionConfig, SourceConfig, load_config
from cst_help_mcp.errors import BuildError
from cst_help_mcp.library import Library, read_library, write_library
from cst_help_mcp.links import Inventory, LinkReport, ReleaseFiles, SourceLink, resolve_links
from cst_help_mcp.locator import locator_for
from cst_help_mcp.model import Document, LinkStatus
from cst_help_mcp.navigation import (
    Navigation,
    NavigationReport,
    apply_navigation,
    read_navigation,
    resolve_navigation,
)
from cst_help_mcp.pdf import read_manual
from cst_help_mcp.render import render_markdown
from cst_help_mcp.robohelp import PROSE, VBA, is_topic, read_topic
from cst_help_mcp.sphinx import read_inventory, read_sphinx_page
from cst_help_mcp.winwrap import read_winwrap_topic

# Reads one topic's HTML into a Document: html, then source_path, locator, area and release by keyword.
_Reader = Callable[..., Document]
_READ_PROSE: _Reader = partial(read_topic, profile=PROSE)
_READ_VBA: _Reader = partial(read_topic, profile=VBA)


@dataclass(frozen=True)
class _Project:
    area: str
    folder: str  # relative to the release folder
    read: _Reader
    # When set, only these files directly in the folder are read, all as topics: they are
    # topics that don't load whtopic.js, among WebHelp's shell pages.
    topics: tuple[str, ...] = ()
    # A Sphinx project: its inventory lists its pages, all topics, and its reader reads them with it.
    sphinx: bool = False
    # A folder of the tree where its Documents are also written, when their Locators lie outside
    # their Area's folder.
    copy_to: str = ""

    def files(self, release: Path) -> list[Path]:
        folder = release / self.folder
        if self.sphinx:
            return [release / page for page in read_inventory(release, self.folder).pages]
        if self.topics:
            return [folder / name for name in self.topics if (folder / name).is_file()]
        return sorted(p for p in folder.rglob("*") if p.is_file())

    def reader(self, release: Path) -> _Reader:
        if self.sphinx:
            return partial(self.read, inventory=read_inventory(release, self.folder))
        return self.read

    @property
    def all_topics(self) -> bool:
        """Whether every file it lists is a topic, whatever it loads."""
        return self.sphinx or bool(self.topics)


# The help projects that the cst-release Source reads. The root project's own
# subtrees make up the General Area, except its VBA overview, which macro questions need in
# VBA 3D, and its Python menu topics, which belong with the Python reference. A topic published
# identically in several projects becomes a Document of the first one listed here, so the ribbon
# topics belong to General.
_CST_RELEASE_PROJECTS = (
    *(
        _Project("general", f"Online Help/{folder}", _READ_PROSE)
        for folder in (
            "general",
            "userinterface",
            "ribbons",
            "advanced",
            "license",
            "simulation_acceleration",
        )
    ),
    _Project("3d", "Online Help/mergedProjects/3D", _READ_PROSE),
    _Project("vba-3d", "Online Help/vba", _READ_PROSE),
    _Project("vba-3d", "Online Help/mergedProjects/VBA_3D", _READ_VBA),
    _Project("winwrap-basic", "Online Help/sax_basic", read_winwrap_topic),
    _Project("python", "Online Help/Python", read_sphinx_page, sphinx=True),
    _Project("python", "Online Help/mergedProjects/Python", _READ_PROSE),
    # The Python menu topics (CST Apps and user scripts) at the root of the help.
    _Project("python", "Online Help", _READ_PROSE, topics=("menu.htm", "user_scipts.htm"), copy_to="python"),
    _Project("circuits", "Online Help/mergedProjects/DES", _READ_PROSE),
    _Project("pcb", "Online Help/mergedProjects/PCB", _READ_PROSE),
    _Project("filter-designer", "Online Help/mergedProjects/Filter_Designer_3D", _READ_PROSE),
    _Project("chip-interface", "Online Help/mergedProjects/CHI", _READ_PROSE),
    _Project("vba-schematic", "Online Help/mergedProjects/VBA_DES", _READ_VBA),
    # The Example Projects are published beside the others, but no table of contents splices them in.
    *(
        _Project("example-projects", f"Online Help/mergedProjects/EXP_{name}", _READ_PROSE)
        for name in ("CBL", "DES", "HF", "LF", "MP", "PCB", "PD")
    ),
)


# The PDFs in the release folder that the cst-release Source reads into Area manuals, with text
# companions: the Word manuals and the release notes. The FEST3D, SPARK3D and IdEM PDFs are left
# out with their online help.
_MANUALS_FOLDER = "Documentation"
_LEFT_OUT_MANUALS = ("*FEST3D*", "*SPARK3D*", "*IdEM*")

_IMAGE_SUFFIXES = frozenset((".png", ".gif", ".jpg", ".jpeg", ".bmp", ".svg", ".ico"))


@dataclass(frozen=True)
class Failure:
    source: str  # the Document's source path
    error: str


@dataclass(frozen=True)
class SourceUnpairedMath:
    """A math delimiter without its partner, as the report lists it: the Document's source path,
    the delimiter and the text around it."""

    source: str
    delimiter: str
    context: str


@dataclass
class BuildReport:
    """What a Build found and what it could not convert. Written as report.json in every Build."""

    discovered: int = 0
    converted: int = 0
    skipped: int = 0
    aliases: int = 0  # converted topics that became Aliases of another Document
    assets: int = 0
    # Images whose file is missing from the release folder, or can't be read as an image.
    missing_assets: list[SourceLink] = field(default_factory=list)
    failures: list[Failure] = field(default_factory=list)
    # Math delimiters without a partner, in topics that load MathJax, so they stay text.
    unpaired_math: list[SourceUnpairedMath] = field(default_factory=list)
    links: LinkReport = field(default_factory=LinkReport)
    navigation: NavigationReport = field(default_factory=NavigationReport)
    unsupported: Counter[str] = field(default_factory=Counter)  # files no reader handles, by extension
    # The Library's Python modules that are not copied: neither an app's entry module nor driving CST.
    library_left_out: list[str] = field(default_factory=list)
    api_entries: int = 0

    @property
    def failed(self) -> int:
        return len(self.failures)

    @property
    def documents(self) -> int:
        return self.converted - self.aliases

    @property
    def unresolved_links(self) -> int:
        return len(self.links.unresolved)

    @property
    def missing_anchors(self) -> int:
        return len(self.links.missing_anchors)

    @property
    def complete(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "counts": {
                "discovered": self.discovered,
                "converted": self.converted,
                "skipped": self.skipped,
                "aliases": self.aliases,
                "failed": self.failed,
                "unresolved_links": self.unresolved_links,
                "missing_anchors": self.missing_anchors,
                "assets": self.assets,
                "missing_assets": len(self.missing_assets),
                "unsupported": sum(self.unsupported.values()),
                "library_left_out": len(self.library_left_out),
                "unpaired_math": len(self.unpaired_math),
            },
            "api_entries": self.api_entries,
            "links": {status: self.links.statuses[status] for status in get_args(LinkStatus)},
            "outside_links": dict(self.links.outside.most_common()),
            "unresolved_links": [asdict(u) for u in self.links.unresolved],
            "missing_anchors": [asdict(u) for u in self.links.missing_anchors],
            "missing_assets": [asdict(m) for m in self.missing_assets],
            "navigation": asdict(self.navigation),
            "unpaired_math": [asdict(u) for u in self.unpaired_math],
            "failures": [asdict(f) for f in self.failures],
            "unsupported": dict(sorted(self.unsupported.items())),
            "library_left_out": self.library_left_out,
        }


@dataclass(frozen=True)
class BuildResult:
    collection: str
    build_id: str
    report: BuildReport
    report_path: Path


def build_collection(config_path: Path, collection_name: str, *, strict: bool = False) -> BuildResult:
    """Build a Collection into a new Build, then assemble it into the Knowledge Base.

    A failed Document leaves the Build incomplete, or with ``strict`` fails the whole build.
    """
    config = load_config(config_path)
    collection = config.collection(collection_name)
    report = BuildReport()
    docs: list[Document] = []
    library = Library()
    for source in collection.sources:
        found = _read_library(source, library, report)
        docs.extend(_read_source(collection, source, report, library_found=found))
    _check_locators(docs)
    release_folders = [source.path for source in collection.sources]
    navigation = read_navigation(release_folders)
    apply_navigation(docs, navigation)
    unmerged = len(docs)
    docs = _merge_aliases(docs)
    report.aliases = unmerged - len(docs)
    report.unpaired_math = [
        SourceUnpairedMath(doc.source_path, u.delimiter, u.context) for doc in docs for u in doc.unpaired_math
    ]
    if not docs and not library.copied:
        raise BuildError(
            f"No Documents could be converted for collection '{collection.name}': {_listed(report)}"
        )
    if strict and report.failures:
        raise BuildError(f"{report.failed} Documents failed to build, and --strict is set: {_listed(report)}")
    report.api_entries = sum(len(d.api_entries) for d in docs)
    inventory = Inventory(docs)
    files = ReleaseFiles(release_folders)
    report.links = resolve_links(docs, inventory, files)
    report.navigation = resolve_navigation(navigation, inventory)
    build_id = layout.new_id()
    final = layout.build_dir(config.kb_path, collection.name, build_id)
    with layout.staged(final) as staging:
        assets, report.missing_assets = write_assets(staging / layout.TREE, docs, files)
        report.assets = len(assets)
        layout.write_json(staging / layout.ASSETS_FILE, [asdict(asset) for asset in assets])
        _write_tree(staging / layout.TREE, docs, files)
        report.failures.extend(Failure(*f) for f in write_library(staging / layout.TREE, library))
        if library.files:
            layout.write_library_lines(staging, [file.line for file in library.files])
        _write_navigation(staging, navigation)
        layout.write_api_entries(
            staging,
            [
                layout.ApiLine(e.qualified_name, doc.area, e.signature, doc.locator, e.anchor)
                for doc in docs
                for e in doc.api_entries
            ],
        )
        layout.write_json(staging / layout.REPORT_FILE, report.to_dict())
        manifest = layout.BuildManifest(
            collection=collection.name,
            release=collection.release,
            failed=report.failed,
            documents=[doc.locator for doc in docs] + [file.line.locator for file in library.copied],
            files=layout.file_hashes(staging),
        )
        manifest.write(staging)
        layout.make_read_only(staging)
    assemble(config.kb_path)
    return BuildResult(collection.name, build_id, report, final / layout.REPORT_FILE)


def _listed(report: BuildReport, limit: int = 5) -> str:
    listed = "; ".join(f"{f.source} ({f.error})" for f in report.failures[:limit])
    more = f" and {report.failed - limit} more" if report.failed > limit else ""
    return listed + more


def _read_library(source: SourceConfig, library: Library, report: BuildReport) -> bool:
    """Add the Source's Library files to ``library``; whether the filters take any."""
    _check_release(source)
    found = read_library(source.path, partial(_selected, source=source))
    report.discovered += len(found.files) + len(found.failures)
    report.converted += len(found.copied)
    report.skipped += len(found.files) - len(found.copied)  # scrambled Macros, listed but not copied
    report.failures.extend(Failure(*f) for f in found.failures)
    report.unsupported.update(found.unsupported)
    report.library_left_out.extend(found.python_left_out)
    library.extend(found)
    return bool(found.files or found.failures)


def _check_release(source: SourceConfig) -> None:
    if not (source.path / "Online Help").is_dir():
        raise BuildError(f"{source.path} is not a CST release folder: it has no 'Online Help' folder")


def _read_source(
    collection: CollectionConfig, source: SourceConfig, report: BuildReport, *, library_found: bool
) -> Iterator[Document]:
    """The Source's help topics and manuals as Documents; ``library_found`` says whether its
    Library already gave the filters something, so that finding no topic is not an error."""
    _check_release(source)
    found = library_found
    for project in _CST_RELEASE_PROJECTS:
        folder = source.path / project.folder
        if not folder.is_dir():
            raise BuildError(
                f"The structure of {source.path} is not recognised as a CST release folder: "
                f"it has no '{project.folder}' project"
            )
        read = project.reader(source.path)
        for file in project.files(source.path):
            rel = file.relative_to(source.path).as_posix()
            if not _selected(rel, source):
                continue
            if not project.sphinx and file.suffix.lower() != ".htm":
                # Images become Assets when a Document shows them.
                if file.suffix.lower() not in _IMAGE_SUFFIXES:
                    report.unsupported[file.suffix.lower()] += 1
                continue
            report.discovered += 1
            try:
                html = file.read_text(encoding="utf-8")
                if not (project.all_topics or is_topic(html)):
                    report.skipped += 1
                    continue
                found = True
                doc = read(
                    html,
                    source_path=rel,
                    locator=locator_for(rel),
                    area=project.area,
                    release=collection.release,
                )
            except Exception as e:  # noqa: BLE001
                # One unreadable Document must not cost the whole Collection; the report lists it.
                found = True
                report.failures.append(Failure(rel, f"{type(e).__name__}: {e}"))
                continue
            report.converted += 1
            if project.copy_to:
                doc.copied_to.append(project.copy_to)
            yield doc
    for name in _manuals(source.path):
        rel = f"{_MANUALS_FOLDER}/{name}"
        if not _selected(rel, source):
            continue
        report.discovered += 1
        found = True
        try:
            doc = read_manual(
                source.path / rel,
                source_path=rel,
                locator=f"manuals/{name}.md",
                area="manuals",
                release=collection.release,
            )
        except Exception as e:  # noqa: BLE001
            # A manual that can't be read, such as one without a text layer, is a reported failure.
            report.failures.append(Failure(rel, f"{type(e).__name__}: {e}"))
            continue
        report.converted += 1
        yield doc
    if not found:
        raise BuildError(
            f"No topics found for collection '{collection.name}' in {source.path} "
            "with the configured include and exclude filters"
        )


def _manuals(release: Path) -> list[str]:
    """The file names of the release folder's PDFs that Area manuals holds."""
    folder = release / _MANUALS_FOLDER
    pdfs = sorted(p.name for p in folder.glob("*.pdf")) if folder.is_dir() else []
    return [name for name in pdfs if not any(fnmatch.fnmatch(name, p) for p in _LEFT_OUT_MANUALS)]


def _selected(rel: str, source: SourceConfig) -> bool:
    path = rel.lower()
    included = not source.include or any(fnmatch.fnmatchcase(path, p.lower()) for p in source.include)
    excluded = any(fnmatch.fnmatchcase(path, p.lower()) for p in source.exclude)
    return included and not excluded


def _check_locators(docs: list[Document]) -> None:
    """No two Documents share a path in the tree, as a Locator or as a copy's path."""
    seen: dict[str, str] = {}
    for doc in docs:
        for path in (doc.locator, *_copies(doc)):
            other = seen.setdefault(path, doc.source_path)
            if other != doc.source_path:
                raise BuildError(f"Locator collision: '{other}' and '{doc.source_path}' both map to '{path}'")


def _merge_aliases(docs: list[Document]) -> list[Document]:
    """Keep one Document per identical title and text; the others' source paths become its Aliases.

    Text, not structure, is compared, because projects with different Profiles parse the same
    page differently. The first Document read wins, so the project order decides which is kept.
    """
    kept: dict[str, Document] = {}
    for doc in docs:
        text = " ".join(b.plain_text() for s in doc.sections for b in s.blocks)
        content = f"{doc.title}\n{' '.join(text.split())}"
        first = kept.setdefault(hashlib.sha256(content.encode()).hexdigest(), doc)
        if first is not doc:
            first.aliases.append(doc.source_path)
            if doc.area != first.area and doc.area not in first.alias_areas:
                first.alias_areas.append(doc.area)
            for kept_values, values in (
                (first.toc_paths, doc.toc_paths),
                (first.keywords, doc.keywords),
                (first.context_ids, doc.context_ids),
            ):
                kept_values.extend(v for v in values if v not in kept_values)
    return list(kept.values())


def _write_tree(tree: Path, docs: list[Document], files: ReleaseFiles) -> None:
    """Write each Document's Markdown, and its source file where that is copied as it is; the model
    itself is not kept (ADR 0014)."""
    tree.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        md = tree / doc.locator
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(render_markdown(doc), encoding="utf-8", newline="\n")
        if doc.original and (original := files.find(doc.source_path)):
            shutil.copyfile(original, tree / doc.original)
        for path in _copies(doc):
            (tree / path).parent.mkdir(parents=True, exist_ok=True)
            (tree / path).write_text(render_markdown(doc, copy=True), encoding="utf-8", newline="\n")


def _copies(doc: Document) -> list[str]:
    """The paths in the tree where a Document's Markdown is copied."""
    return [f"{folder}/{doc.locator}" for folder in doc.copied_to]


def _write_navigation(build: Path, navigation: Navigation) -> None:
    """Write the navigation trees beside the tree, for assembly to render as entry files."""
    layout.write_json(
        build / layout.NAVIGATION_FILE,
        {tree: [node.to_dict() for node in nodes] for tree, nodes in navigation.trees().items()},
    )
