"""Build one Collection: read its Sources into Documents, write the Markdown tree and index it."""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

from cst_help_mcp import index
from cst_help_mcp.config import CollectionConfig, SourceConfig, load_config
from cst_help_mcp.errors import BuildError
from cst_help_mcp.locator import locator_for
from cst_help_mcp.model import Document
from cst_help_mcp.render import render_markdown
from cst_help_mcp.robohelp import is_topic, read_vba_topic

# Release-folder projects that the cst-release Source can read so far, by Area.
_CST_RELEASE_AREAS = {"vba-3d": "Online Help/mergedProjects/VBA_3D"}


def build_collection(config_path: Path, collection_name: str) -> list[Document]:
    config = load_config(config_path)
    collection = config.collection(collection_name)
    docs = [doc for source in collection.sources for doc in _read_source(collection, source)]
    _check_locators(docs)
    # Ticket 03 replaces this with immutable Builds and an atomic pointer switch (ADR 0009).
    staging = _write_staging_tree(config.kb_path, collection.name, docs)
    try:
        index.replace_collection(config.kb_path, collection.name, collection.release, docs)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    _swap_in(config.kb_path / collection.name, staging)
    return docs


def _read_source(collection: CollectionConfig, source: SourceConfig) -> Iterator[Document]:
    if not (source.path / "Online Help").is_dir():
        raise BuildError(f"{source.path} is not a CST release folder: it has no 'Online Help' folder")
    found = False
    for area, project in _CST_RELEASE_AREAS.items():
        for file in sorted((source.path / project).rglob("*.htm")):
            rel = file.relative_to(source.path).as_posix()
            if not _selected(rel, source):
                continue
            html = file.read_text(encoding="utf-8")
            if not is_topic(html):
                continue
            found = True
            yield read_vba_topic(
                html,
                source_path=rel,
                locator=locator_for(rel),
                area=area,
                release=collection.release,
            )
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


def _write_staging_tree(kb_path: Path, collection: str, docs: list[Document]) -> Path:
    """Write the Markdown files with their persisted models into a staging folder."""
    kb_path.mkdir(parents=True, exist_ok=True)
    staging = kb_path / f".{collection}.staging-{os.getpid()}"
    shutil.rmtree(staging, ignore_errors=True)
    for doc in docs:
        md = staging / doc.locator
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(render_markdown(doc), encoding="utf-8", newline="\n")
        model = md.with_name(md.name + ".json")
        model.write_text(json.dumps(doc.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    return staging


def _swap_in(target: Path, staging: Path) -> None:
    if target.exists():
        retired = target.with_name(f".{target.name}.retired-{os.getpid()}")
        target.rename(retired)
        shutil.rmtree(retired)
    staging.rename(target)
