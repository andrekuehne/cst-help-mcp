"""Assembly: make the newest Build of every Collection the readable view, then switch the pointer.

Each Collection's view is its Build's tree, linked file by file, with the entry files rendered
from the Build's navigation data. Nothing but files for reading goes into a view (ADR 0014).
"""

from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.render import render_navigation


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
            layout.write_json(staging / layout.ASSEMBLY_MANIFEST, {"builds": builds})
        # The views switch just before the pointer: a view that cannot switch leaves the old one active.
        for collection, build in builds.items():
            _update_view(kb_path, collection, layout.build_dir(kb_path, collection, build))
        layout.write_pointer(kb_path, assembly.id)
        _prune(kb_path, assembly)
    return assembly


def _update_view(kb_path: Path, collection: str, build: Path) -> None:
    """Replace the readable view with hard links into the Build's tree, or copies where links fail,
    and the entry files."""
    for leftover in kb_path.glob(f".{collection}.view-*"):
        layout.remove_tree(leftover)
    staging = kb_path / f".{collection}.view-{os.getpid()}"
    shutil.copytree(build / layout.TREE, staging, copy_function=_link_or_copy)
    _write_entry_files(staging, build)
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


def _write_entry_files(view: Path, build: Path) -> None:
    """Write ``toc.md`` and ``keywords.md`` from the navigation trees the Build found."""
    release = layout.BuildManifest.read(build).release
    for tree, nodes in layout.read_navigation(build).items():
        name, title = layout.ENTRY_FILES[tree]
        text = render_navigation(release, title, nodes)
        (view / name).write_text(text, encoding="utf-8", newline="\n")


def _link_or_copy(src: str, dst: str) -> None:
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _prune(kb_path: Path, active: Assembly) -> None:
    """Remove older assemblies, then the older Builds the active assembly does not use."""
    for folder in layout.assemblies_dir(kb_path).iterdir():
        if not folder.name.startswith(".") and folder.name < active.id:
            layout.remove_tree(folder)
    for collection, build in active.builds.items():
        for folder in layout.builds_dir(kb_path, collection).iterdir():
            # A newer Build may be one that is finishing right now.
            if folder.name.startswith(".") or folder.name >= build:
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
