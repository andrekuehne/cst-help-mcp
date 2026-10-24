"""Build one Collection: read its Sources into Documents and write them as a new, immutable Build."""

from __future__ import annotations

import fnmatch
import json
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cst_help_mcp import layout
from cst_help_mcp.assembly import assemble
from cst_help_mcp.config import CollectionConfig, SourceConfig, load_config
from cst_help_mcp.errors import BuildError
from cst_help_mcp.locator import locator_for
from cst_help_mcp.model import Document
from cst_help_mcp.render import render_markdown
from cst_help_mcp.robohelp import is_topic, read_vba_topic

# Release-folder projects that the cst-release Source can read so far, by Area.
_CST_RELEASE_AREAS = {"vba-3d": "Online Help/mergedProjects/VBA_3D"}


@dataclass(frozen=True)
class Failure:
    source: str  # the Document's source path
    error: str


@dataclass
class BuildReport:
    """What a Build found and what it could not convert. Written as report.json in every Build."""

    discovered: int = 0
    converted: int = 0
    skipped: int = 0
    # None until a later ticket checks them: links (ticket 04) and Assets (ticket 09).
    unresolved_links: int | None = None
    missing_assets: int | None = None
    failures: list[Failure] = field(default_factory=list)
    unsupported: Counter[str] = field(default_factory=Counter)  # files no reader handles, by extension
    api_entries: int = 0

    @property
    def failed(self) -> int:
        return len(self.failures)

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
                "failed": self.failed,
                "unresolved_links": self.unresolved_links,
                "missing_assets": self.missing_assets,
                "unsupported": sum(self.unsupported.values()),
            },
            "api_entries": self.api_entries,
            "failures": [asdict(f) for f in self.failures],
            "unsupported": dict(sorted(self.unsupported.items())),
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
    docs = [doc for source in collection.sources for doc in _read_source(collection, source, report)]
    _check_locators(docs)
    if not docs:
        raise BuildError(
            f"No Documents could be converted for collection '{collection.name}': {_listed(report)}"
        )
    if strict and report.failures:
        raise BuildError(f"{report.failed} Documents failed to build, and --strict is set: {_listed(report)}")
    report.api_entries = sum(len(d.api_entries) for d in docs)
    build_id = layout.new_id()
    final = layout.build_dir(config.kb_path, collection.name, build_id)
    with layout.staged(final) as staging:
        _write_tree(staging / layout.TREE, docs)
        layout.write_json(staging / layout.REPORT_FILE, report.to_dict())
        manifest = layout.BuildManifest(
            collection=collection.name,
            release=collection.release,
            failed=report.failed,
            documents=[doc.locator for doc in docs],
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


def _read_source(
    collection: CollectionConfig, source: SourceConfig, report: BuildReport
) -> Iterator[Document]:
    if not (source.path / "Online Help").is_dir():
        raise BuildError(f"{source.path} is not a CST release folder: it has no 'Online Help' folder")
    found = False
    for area, project in _CST_RELEASE_AREAS.items():
        if not (source.path / project).is_dir():
            raise BuildError(
                f"The structure of {source.path} is not recognised as a CST release folder: "
                f"it has no '{project}' project"
            )
        for file in sorted(p for p in (source.path / project).rglob("*") if p.is_file()):
            rel = file.relative_to(source.path).as_posix()
            if not _selected(rel, source):
                continue
            if file.suffix.lower() != ".htm":
                report.unsupported[file.suffix.lower()] += 1
                continue
            report.discovered += 1
            try:
                html = file.read_text(encoding="utf-8")
                if not is_topic(html):
                    report.skipped += 1
                    continue
                found = True
                doc = read_vba_topic(
                    html,
                    source_path=rel,
                    locator=locator_for(rel),
                    area=area,
                    release=collection.release,
                )
            except Exception as e:  # noqa: BLE001
                # One unreadable Document must not cost the whole Collection; the report lists it.
                found = True
                report.failures.append(Failure(rel, f"{type(e).__name__}: {e}"))
                continue
            report.converted += 1
            yield doc
    if not found:
        raise BuildError(
            f"No topics found for collection '{collection.name}' in {source.path} "
            "with the configured include and exclude filters"
        )


def _selected(rel: str, source: SourceConfig) -> bool:
    path = rel.lower()
    included = not source.include or any(fnmatch.fnmatchcase(path, p.lower()) for p in source.include)
    excluded = any(fnmatch.fnmatchcase(path, p.lower()) for p in source.exclude)
    return included and not excluded


def _check_locators(docs: list[Document]) -> None:
    seen: dict[str, str] = {}
    for doc in docs:
        other = seen.setdefault(doc.locator, doc.source_path)
        if other != doc.source_path:
            raise BuildError(
                f"Locator collision: '{other}' and '{doc.source_path}' both map to '{doc.locator}'"
            )


def _write_tree(tree: Path, docs: list[Document]) -> None:
    """Write each Document's Markdown with its persisted model next to it."""
    tree.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        md = tree / doc.locator
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(render_markdown(doc), encoding="utf-8", newline="\n")
        model = md.with_name(md.name + ".json")
        model.write_text(json.dumps(doc.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
