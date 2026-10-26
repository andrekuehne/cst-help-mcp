"""Assembly: make the newest Build of every Collection the readable view, then switch the pointer.

Each Collection's view is its Build's tree, linked file by file, with the entry files rendered
from the Build's navigation data and API Entries. Nothing but files for reading goes into a view
(ADR 0014), and the workspace around them: AGENTS.md, CLAUDE.md, and the folders that agents
write into, carried over from the previous view (ADR 0013).
"""

from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.instructions import ReleaseFolder, agents_md, independent_agents_md, root_agents_md
from cst_help_mcp.render import (
    render_api,
    render_documents,
    render_library,
    render_materials,
    render_navigation,
)


@dataclass(frozen=True)
class Assembly:
    id: str
    builds: dict[str, str]  # Collection name to Build id


def assemble(kb_path: Path) -> Assembly:
    """Assemble the newest finished Build of every Collection and make it active."""
    with layout.assembly_lock(kb_path):
        builds = _newest_builds(kb_path)
        if not builds:
            raise KnowledgeBaseError(f"Nothing to assemble: the Knowledge Base at {kb_path} holds no Builds")
        return _assemble(kb_path, builds)


def remove(kb_path: Path, collection: str) -> Assembly:
    """Remove a Collection, such as an old Release: assemble the others without it, then delete its
    view, with what agents wrote into it, and its Builds, so that no later assembly brings it back."""
    layout.active_assembly(kb_path)  # fails clearly where there is no Knowledge Base
    with layout.assembly_lock(kb_path):
        builds = _newest_builds(kb_path)
        if collection not in builds:
            raise KnowledgeBaseError(
                f"The Knowledge Base at {kb_path} has no Collection '{collection}'; "
                f"built: {', '.join(builds) or 'none'}"
            )
        del builds[collection]
        if not builds:
            raise KnowledgeBaseError(
                f"{collection} is the only Collection of the Knowledge Base at {kb_path}; "
                "delete the Knowledge Base folder to remove it all"
            )
        assembly = _assemble(kb_path, builds)
        folder = layout.builds_dir(kb_path, collection)
        for build in folder.iterdir():
            _unlink_manifest(build)
        leftovers = [folder, kb_path / collection, *kb_path.glob(f".{collection}.view-*")]
        for path in leftovers:
            if path.exists():
                layout.remove_tree(path)
        if left := [p for p in leftovers if p.exists()]:
            raise KnowledgeBaseError(
                f"{collection} is no longer assembled, but {', '.join(map(str, left))} could not be "
                "deleted, perhaps because a file in it is open. Close it and delete the folder."
            )
    return assembly


def _newest_builds(kb_path: Path) -> dict[str, str]:
    """The newest finished Build of every Collection."""
    return {c: layout.finished_builds(kb_path, c)[-1] for c in layout.built_collections(kb_path)}


def _assemble(kb_path: Path, builds: dict[str, str]) -> Assembly:
    """Assemble the given Builds and make them active; the caller holds the lock."""
    assembly = Assembly(layout.new_id(), builds)
    with layout.staged(layout.assemblies_dir(kb_path) / assembly.id) as staging:
        layout.write_json(staging / layout.ASSEMBLY_MANIFEST, {"builds": builds})
    folders = [
        ReleaseFolder.of(layout.BuildManifest.read(layout.build_dir(kb_path, c, b)), kb_path / c)
        for c, b in builds.items()
    ]
    beside = [f for f in folders if f.release_independent]
    # The views switch just before the pointer: a view that cannot switch leaves the old one active.
    for collection, build in builds.items():
        _update_view(kb_path, collection, layout.build_dir(kb_path, collection, build), beside)
    # The root AGENTS.md lists the Releases and the release-independent Collections beside them.
    _write(kb_path / layout.AGENTS_FILE, root_agents_md(folders))
    _write(kb_path / layout.CLAUDE_FILE, f"@{layout.AGENTS_FILE}\n")
    layout.write_pointer(kb_path, assembly.id)
    _prune(kb_path, assembly)
    return assembly


def _update_view(kb_path: Path, collection: str, build: Path, beside: list[ReleaseFolder]) -> None:
    """Replace the readable view with hard links into the Build's tree, or copies where links fail,
    and the entry files. What agents wrote into the workspace folders moves over to the new view."""
    target = kb_path / collection
    for leftover in kb_path.glob(f".{collection}.view-*"):
        # An assembly that stopped between its renames left the workspace folders here.
        _move_workspace(leftover, target)
        if any((leftover / name).exists() for name in layout.WORKSPACE_DIRS):
            continue  # the view has its own; keep these rather than lose what agents wrote
        layout.remove_tree(leftover)
    staging = kb_path / f".{collection}.view-{os.getpid()}"
    shutil.copytree(build / layout.TREE, staging, copy_function=_link_or_copy)
    _write_entry_files(staging, build)
    retired = None
    if target.exists():
        retired = target.with_name(f".{target.name}.view-retired-{os.getpid()}")
        try:
            target.rename(retired)
            _move_workspace(retired, staging)
        except OSError as e:
            if retired.exists():
                _move_workspace(staging, retired)
                retired.rename(target)
            layout.remove_tree(staging)
            raise KnowledgeBaseError(
                f"Cannot replace {target}, perhaps because a file in it is open: {e}. "
                "Close it and run cst-help assemble."
            ) from None
    _write_workspace_files(staging, build, beside)
    staging.rename(target)
    if retired is not None:
        layout.remove_tree(retired)


def _move_workspace(old: Path, new: Path) -> None:
    """Move the workspace folders from an old view to a new one that lacks them."""
    for name in layout.WORKSPACE_DIRS:
        if (old / name).is_dir() and not (new / name).exists():
            new.mkdir(exist_ok=True)
            (old / name).rename(new / name)


def _write_entry_files(view: Path, build: Path) -> None:
    """Write ``toc.md`` and ``keywords.md`` from the navigation trees the Build found, ``api.md``
    from its API Entries, ``library.md`` from its Library code and ``materials.md`` from its
    Material Definitions, if it has any. A release-independent Build has only ``documents.md``."""
    manifest = layout.BuildManifest.read(build)
    documents = layout.read_document_lines(build)
    if documents is not None:
        _write(view / layout.DOCUMENTS_ENTRY_FILE, render_documents(f"{manifest.collection} PDFs", documents))
        return
    release = manifest.release
    for tree, nodes in layout.read_navigation(build).items():
        name, title = layout.ENTRY_FILES[tree]
        _write(view / name, render_navigation(release, title, nodes))
    _write(view / layout.API_ENTRY_FILE, render_api(release, layout.read_api_entries(build)))
    library = layout.read_library_lines(build)
    render = {layout.LIBRARY_ENTRY_FILE: render_library, layout.MATERIALS_ENTRY_FILE: render_materials}
    for name in layout.library_entry_files(library):
        _write(view / name, render[name](release, library))


def _write_workspace_files(view: Path, build: Path, beside: list[ReleaseFolder]) -> None:
    """Write ``AGENTS.md``, which lists the view's entry files and Guides, and ``CLAUDE.md``, which
    imports it; and, in a Release's view, the folders agents write into. A session works in a
    Release, so a release-independent view has no workspace folders."""
    folder = ReleaseFolder.of(layout.BuildManifest.read(build), view)
    if folder.release_independent:
        _write(view / layout.AGENTS_FILE, independent_agents_md(folder))
    else:
        for name in layout.WORKSPACE_DIRS:
            (view / name).mkdir(exist_ok=True)
        _write(view / layout.AGENTS_FILE, agents_md(folder, beside))
    _write(view / layout.CLAUDE_FILE, f"@{layout.AGENTS_FILE}\n")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


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
            _unlink_manifest(folder)
            layout.remove_tree(folder)
        # Unlinking a read-only view file clears the flag that its Build's file shares.
        for build_id in layout.finished_builds(kb_path, collection):
            layout.make_read_only(layout.build_dir(kb_path, collection, build_id))


def _unlink_manifest(build: Path) -> None:
    """Without its manifest a Build no longer counts as finished, even if a file stays locked."""
    manifest = build / layout.BUILD_MANIFEST
    try:
        manifest.chmod(stat.S_IWRITE)
        manifest.unlink()
    except OSError:
        pass
