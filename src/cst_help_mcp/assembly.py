"""Assembly: combine the active Build of every Collection into a new database, then switch the pointer.

A running server keeps the database it opened. On Windows that file stays locked, so the
assembly and the Builds it references survive pruning until the server restarts. (Elsewhere
the open database survives, but its Builds' files may be pruned.)
"""

from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.index import IndexedBuild, write_index
from cst_help_mcp.model import Asset, Document, NavNode, NavTree


@dataclass(frozen=True)
class Assembly:
    id: str
    builds: dict[str, str]  # Collection name to Build id


def assemble(kb_path: Path) -> Assembly:
    """Assemble the newest finished Build of every Collection and make it active."""
    with layout.assembly_lock(kb_path):
        builds = {c: layout.finished_builds(kb_path, c)[-1] for c in layout.built_collections(kb_path)}
        if not builds:
            raise KnowledgeBaseError(f"Nothing to assemble: the Knowledge Base at {kb_path} holds no Builds")
        assembly = Assembly(layout.new_id(), builds)
        with layout.staged(layout.assemblies_dir(kb_path) / assembly.id) as staging:
            write_index(
                staging / layout.INDEX_FILE,
                (_indexed(layout.build_dir(kb_path, c, b)) for c, b in builds.items()),
            )
            layout.write_json(staging / layout.ASSEMBLY_MANIFEST, {"builds": builds})
        # The views switch just before the pointer: a view that cannot switch leaves the old one active.
        for collection, build in builds.items():
            _update_view(kb_path, collection, layout.build_dir(kb_path, collection, build) / layout.TREE)
        layout.write_pointer(kb_path, assembly.id)
        _prune(kb_path, assembly)
    return assembly


def _indexed(build: Path) -> IndexedBuild:
    manifest = layout.BuildManifest.read(build)
    tree = build / layout.TREE
    docs = (Document.from_dict(layout.read_json(tree / f"{locator}.json")) for locator in manifest.documents)
    nav_file = build / layout.NAVIGATION_FILE
    trees: dict[NavTree, list[Any]] = layout.read_json(nav_file) if nav_file.is_file() else {}
    navigation = {tree: [NavNode.from_dict(n) for n in nodes] for tree, nodes in trees.items()}
    assets_file = tree / layout.ASSETS_INDEX
    assets = [Asset(**a) for a in layout.read_json(assets_file)] if assets_file.is_file() else []
    return IndexedBuild(
        manifest.collection, manifest.release, build.name, manifest.failed, docs, navigation, assets
    )


def _update_view(kb_path: Path, collection: str, tree: Path) -> None:
    """Replace the readable view with hard links into the active Build, or copies where links fail."""
    for leftover in kb_path.glob(f".{collection}.view-*"):
        layout.remove_tree(leftover)
    staging = kb_path / f".{collection}.view-{os.getpid()}"
    shutil.copytree(tree, staging, copy_function=_link_or_copy)
    target = kb_path / collection
    if target.exists():
        retired = target.with_name(f".{target.name}.view-retired-{os.getpid()}")
        try:
            target.rename(retired)
        except OSError as e:
            layout.remove_tree(staging)
            raise KnowledgeBaseError(
                f"Cannot replace {target}, perhaps because a file in it is open: {e}. "
                "Close it and run cst-help assemble."
            ) from None
        layout.remove_tree(retired)
    staging.rename(target)


def _link_or_copy(src: str, dst: str) -> None:
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _prune(kb_path: Path, active: Assembly) -> None:
    """Remove older assemblies no server holds open, then the older Builds no remaining assembly uses."""
    in_use = set(active.builds.items())
    for folder in layout.assemblies_dir(kb_path).iterdir():
        if folder.name.startswith(".") or folder.name >= active.id:
            continue
        try:
            (folder / layout.INDEX_FILE).unlink(missing_ok=True)
        except OSError:
            # A running server still holds this database open, and with it its Builds.
            try:
                in_use.update(layout.assembly_builds(folder).items())
            except KnowledgeBaseError:
                pass
            continue
        layout.remove_tree(folder)
    for collection, build in active.builds.items():
        for folder in layout.builds_dir(kb_path, collection).iterdir():
            # A newer Build may be one that is finishing right now.
            if folder.name.startswith(".") or folder.name >= build or (collection, folder.name) in in_use:
                continue
            # Without its manifest a Build no longer counts as finished, even if a file stays locked.
            manifest = folder / layout.BUILD_MANIFEST
            try:
                manifest.chmod(stat.S_IWRITE)
                manifest.unlink()
            except OSError:
                pass
            layout.remove_tree(folder)
        # Unlinking a read-only view file clears the flag that its Build's file shares.
        for build_id in layout.finished_builds(kb_path, collection):
            layout.make_read_only(layout.build_dir(kb_path, collection, build_id))
