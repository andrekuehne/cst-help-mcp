"""The TOML configuration: a Knowledge Base path, its Collections and their Sources."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cst_help_mcp.errors import ConfigError

# The Source type that reads a CST release folder, such as an installation.
CST_RELEASE = "cst-release"
# The Source type that makes a Collection release-independent.
PDF_FOLDER = "pdf-folder"
SOURCE_TYPES = (CST_RELEASE, PDF_FOLDER)


@dataclass(frozen=True)
class SourceConfig:
    type: str
    path: Path
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CollectionConfig:
    name: str
    release: str  # "" for a release-independent Collection
    sources: list[SourceConfig]

    @property
    def release_independent(self) -> bool:
        return not self.release


@dataclass(frozen=True)
class Config:
    kb_path: Path
    collections: dict[str, CollectionConfig]

    def collection(self, name: str) -> CollectionConfig:
        try:
            return self.collections[name]
        except KeyError:
            known = ", ".join(sorted(self.collections)) or "none"
            raise ConfigError(f"Unknown collection '{name}'. Configured collections: {known}") from None


def load_config(path: Path) -> Config:
    """Read and check a configuration file. Relative paths resolve against its folder."""
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path} is not valid TOML: {e}") from None
    base = path.resolve().parent

    kb = data.get("knowledge_base", {}).get("path")
    if not isinstance(kb, str) or not kb:
        raise ConfigError(f"{path}: [knowledge_base] needs a 'path'")

    collections_data = data.get("collections", {})
    if not isinstance(collections_data, dict) or not collections_data:
        raise ConfigError(f"{path}: no [collections.<name>] are configured")
    collections = {name: _collection(path, base, name, c) for name, c in collections_data.items()}
    return Config(kb_path=base / kb, collections=collections)


def _collection(path: Path, base: Path, name: str, data: dict[str, Any]) -> CollectionConfig:
    sources_data = data.get("sources", [])
    if not sources_data:
        raise ConfigError(f"{path}: collection '{name}' has no [[collections.{name}.sources]]")
    sources = [_source(path, base, name, s) for s in sources_data]
    release = data.get("release")
    pdf_folders = sum(source.type == PDF_FOLDER for source in sources)
    if pdf_folders:
        # A folder of PDFs is gathered apart from any Release, and sits beside every Release.
        if pdf_folders < len(sources) or release is not None:
            raise ConfigError(
                f"{path}: collection '{name}' has a '{PDF_FOLDER}' Source, which makes it "
                f"release-independent: it takes no 'release' and only '{PDF_FOLDER}' Sources"
            )
        return CollectionConfig(name=name, release="", sources=sources)
    if release is None:
        release = _release_named(name)
        if release is None:
            raise ConfigError(f"{path}: collection '{name}' needs a 'release'")
    return CollectionConfig(name=name, release=str(release), sources=sources)


def command_line_config(kb_path: Path, name: str, source: Path, release: str | None = None) -> Config:
    """The configuration `build --source --kb` describes: one Collection read from one CST release
    folder, such as an installation. Its Release comes from a name like cst-2024 unless given."""
    if release is None:
        release = _release_named(name)
        if release is None:
            raise ConfigError(f"Collection '{name}' needs --release: its name is not cst-<release>")
    if not source.is_dir():
        raise ConfigError(f"Source folder of collection '{name}' does not exist: {source}")
    sources = [SourceConfig(type=CST_RELEASE, path=source)]
    return Config(
        kb_path=kb_path, collections={name: CollectionConfig(name=name, release=release, sources=sources)}
    )


def _release_named(name: str) -> str | None:
    """The Release a Collection's name gives, as cst-2024 gives 2024."""
    match = re.fullmatch(r"cst-(\d+)", name)
    return match.group(1) if match else None


def _source(path: Path, base: Path, collection: str, data: dict[str, Any]) -> SourceConfig:
    kind = data.get("type")
    if kind not in SOURCE_TYPES:
        raise ConfigError(
            f"{path}: collection '{collection}' has a Source of unknown type {kind!r}; "
            f"supported: {', '.join(SOURCE_TYPES)}"
        )
    raw = data.get("path")
    if not isinstance(raw, str) or not raw:
        raise ConfigError(f"{path}: a '{kind}' Source of collection '{collection}' needs a 'path'")
    folder = base / raw
    if not folder.is_dir():
        raise ConfigError(f"Source folder of collection '{collection}' does not exist: {folder}")
    return SourceConfig(
        type=kind,
        path=folder,
        include=list(data.get("include", [])),
        exclude=list(data.get("exclude", [])),
    )
