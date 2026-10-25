"""Where a Knowledge Base keeps its Builds, assemblies and the active pointer (ADR 0009).

    <kb>/builds/<collection>/<build id>/   one immutable Build: build.json, report.json, navigation.json,
                                           assets.json, tree/
    <kb>/assemblies/<assembly id>/         one assembly: assembly.json, naming the Build of each Collection
    <kb>/active.json                       the pointer to the active assembly, replaced atomically
    <kb>/<collection>/                     the readable view: the active Build's tree and the entry files

Builds and assemblies are written under a dot-prefixed name and renamed into place once
finished, so a folder under its final name is always whole. A Build's files are then made
read-only, and the readable view links to them, so nothing edits a Build in place. Only what
agents read goes into the tree; the manifest, report and navigation data stay beside it.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import stat
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any

from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.model import NavNode, NavTree

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

POINTER_FILE = "active.json"
LOCK_FILE = ".lock"
BUILD_MANIFEST = "build.json"
REPORT_FILE = "report.json"
NAVIGATION_FILE = "navigation.json"
# Entry files that assembly writes at the root of a readable view, listing its navigation trees.
ENTRY_FILES: dict[NavTree, tuple[str, str]] = {
    "toc": ("toc.md", "Table of contents"),
    "keywords": ("keywords.md", "Keywords"),
}
# The folder of a Build's tree that holds its Assets, and the list of them beside the tree.
ASSETS_DIR = "assets"
ASSETS_FILE = "assets.json"
ASSEMBLY_MANIFEST = "assembly.json"
TREE = "tree"


@dataclass(frozen=True)
class BuildManifest:
    """What a finished Build holds. Written last, so a Build without one is not finished."""

    collection: str
    release: str
    failed: int  # Documents that failed to build, leaving the Knowledge Base incomplete
    documents: list[str]  # Locators
    files: dict[str, str]  # SHA-256 of every other file in the Build, by path relative to it

    def write(self, build: Path) -> None:
        write_json(build / BUILD_MANIFEST, asdict(self))

    @classmethod
    def read(cls, build: Path) -> BuildManifest:
        try:
            return cls(**read_json(build / BUILD_MANIFEST))
        except (ValueError, TypeError) as e:
            raise KnowledgeBaseError(f"{build / BUILD_MANIFEST} is damaged: {e}") from None


def new_id() -> str:
    """A fresh id that sorts by creation time."""
    return f"{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}-{secrets.token_hex(2)}"


def builds_dir(kb_path: Path, collection: str) -> Path:
    return kb_path / "builds" / collection


def build_dir(kb_path: Path, collection: str, build_id: str) -> Path:
    return builds_dir(kb_path, collection) / build_id


def assemblies_dir(kb_path: Path) -> Path:
    return kb_path / "assemblies"


def finished_builds(kb_path: Path, collection: str) -> list[str]:
    """Ids of the collection's finished Builds, oldest first."""
    folder = builds_dir(kb_path, collection)
    if not folder.is_dir():
        return []
    return sorted(
        p.name for p in folder.iterdir() if not p.name.startswith(".") and (p / BUILD_MANIFEST).is_file()
    )


def built_collections(kb_path: Path) -> list[str]:
    folder = kb_path / "builds"
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.is_dir() and finished_builds(kb_path, p.name))


@contextmanager
def staged(final: Path) -> Iterator[Path]:
    """Yield a staging folder that becomes ``final`` once the block finishes, or is removed if it fails."""
    staging = final.with_name(f".{final.name}.partial")
    staging.mkdir(parents=True)
    try:
        yield staging
        staging.rename(final)
    except BaseException:
        remove_tree(staging)
        raise


def make_read_only(folder: Path) -> None:
    for path in folder.rglob("*"):
        if path.is_file():
            path.chmod(stat.S_IREAD)


def remove_tree(path: Path) -> None:
    """Remove a folder as far as possible, read-only files included; files held open stay behind."""

    def retry_writable(func: Callable[..., Any], name: str, _: BaseException) -> None:
        try:
            os.chmod(name, stat.S_IWRITE)
            func(name)
        except OSError:
            pass

    shutil.rmtree(path, onexc=retry_writable)


@contextmanager
def assembly_lock(kb_path: Path) -> Iterator[None]:
    """Hold the Knowledge Base's lock, so only one process assembles or prunes at a time."""
    kb_path.mkdir(parents=True, exist_ok=True)
    with (kb_path / LOCK_FILE).open("a+b") as f:
        try:
            _lock(f)
        except OSError:
            raise KnowledgeBaseError(
                f"Another build or assembly is running on {kb_path}; try again once it has finished"
            ) from None
        try:
            yield
        finally:
            _unlock(f)


def _lock(f: IO[bytes]) -> None:
    if sys.platform == "win32":
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(f: IO[bytes]) -> None:
    if sys.platform == "win32":
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(f, fcntl.LOCK_UN)


def file_hashes(folder: Path) -> dict[str, str]:
    """The SHA-256 of every file below a folder, by path relative to it."""
    return {p.relative_to(folder).as_posix(): sha256(p) for p in sorted(folder.rglob("*")) if p.is_file()}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_pointer(kb_path: Path, assembly: str) -> None:
    """Switch the active assembly atomically."""
    temp = kb_path / f".{POINTER_FILE}.{os.getpid()}"
    write_json(temp, {"assembly": assembly})
    os.replace(temp, kb_path / POINTER_FILE)


def active_assembly(kb_path: Path) -> str:
    pointer = kb_path / POINTER_FILE
    if not pointer.is_file():
        raise KnowledgeBaseError(f"No Knowledge Base at {kb_path}: {POINTER_FILE} is missing")
    try:
        assembly = read_json(pointer)["assembly"]
    except (ValueError, KeyError, TypeError):
        raise KnowledgeBaseError(f"The Knowledge Base at {kb_path} has a damaged {POINTER_FILE}") from None
    if not isinstance(assembly, str):
        raise KnowledgeBaseError(f"The Knowledge Base at {kb_path} has a damaged {POINTER_FILE}")
    return assembly


def read_navigation(build: Path) -> dict[NavTree, list[NavNode]]:
    """The navigation trees a Build found; none for a Build without navigation data."""
    nav_file = build / NAVIGATION_FILE
    trees: dict[NavTree, list[Any]] = read_json(nav_file) if nav_file.is_file() else {}
    return {tree: [NavNode.from_dict(n) for n in nodes] for tree, nodes in trees.items()}


def assembly_builds(assembly: Path) -> dict[str, str]:
    """The Build id of each Collection that an assembly holds."""
    try:
        builds = read_json(assembly / ASSEMBLY_MANIFEST)["builds"]
    except (ValueError, KeyError, TypeError) as e:
        raise KnowledgeBaseError(f"{assembly / ASSEMBLY_MANIFEST} is damaged: {e}") from None
    if not isinstance(builds, dict):
        raise KnowledgeBaseError(f"{assembly / ASSEMBLY_MANIFEST} is damaged")
    return builds
