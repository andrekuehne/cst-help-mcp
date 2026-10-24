"""Check a Knowledge Base's integrity: its pointer, the active database, its Builds and their files."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.index import open_read_only


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
    manifests: dict[str, layout.BuildManifest] = {}
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
        manifests[collection] = manifest
        result.collections.append(
            CollectionStatus(collection, build, len(manifest.documents), manifest.failed)
        )
        result.problems.extend(_check_files(kb_path, folder, manifest.files))
        result.problems.extend(
            _check_view(kb_path, kb_path / collection, folder / layout.TREE, manifest.files)
        )
    result.problems.extend(_check_database(assembly / layout.INDEX_FILE, builds, manifests))
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


def _shown(kb_path: Path, path: Path) -> str:
    """A path as it is reported: relative to the Knowledge Base folder."""
    return path.relative_to(kb_path).as_posix()


def _check_database(
    db: Path, builds: dict[str, str], manifests: dict[str, layout.BuildManifest]
) -> list[str]:
    if not db.is_file():
        return [f"The active database {db} is missing"]
    try:
        con = open_read_only(db)
        try:
            [(integrity,)] = con.execute("PRAGMA integrity_check").fetchall()
            if integrity != "ok":
                return [f"The active database {db} is damaged: {integrity}"]
            held = dict(con.execute("SELECT name, build FROM collections").fetchall())
            documents = {
                c: {
                    locator.partition("#")[0]
                    for (locator,) in con.execute("SELECT locator FROM sections WHERE collection = ?", (c,))
                }
                for c in builds
            }
        finally:
            con.close()
    except sqlite3.DatabaseError as e:
        return [f"The active database {db} is damaged: {e}"]
    problems = []
    if held != builds:
        problems.append(f"The active database {db} is inconsistent: it holds Builds {held}, not {builds}")
    for collection, manifest in manifests.items():
        if documents[collection] != set(manifest.documents):
            problems.append(
                f"The active database {db} is inconsistent with Build {builds[collection]} of "
                f"Collection {collection}: {len(documents[collection])} Documents indexed, "
                f"{len(manifest.documents)} built"
            )
    return problems
