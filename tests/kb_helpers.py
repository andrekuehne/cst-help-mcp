"""Helpers for writing test configurations."""

from __future__ import annotations

import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BENCHMARK = Path(__file__).resolve().parent.parent / "docs" / "benchmark.toml"
SOLVER_HF = "vba_3d/special_vbasolver/special_vbasolver_solver_object.htm.md"
VBA_3D = "Online Help/mergedProjects/VBA_3D"
VBA_OVERVIEW = "Online Help/vba"
WINWRAP = "Online Help/sax_basic"
SPHINX = "Online Help/Python"
PYTHON_OVERVIEW = "Online Help/mergedProjects/Python"
# The Library folders a cst-release Source expects in a release folder.
LIBRARY_FOLDERS = ("Library/Macros", "Library/Result Templates", "Library/Includes")
# The help projects a cst-release Source expects in a release folder.
PROJECTS = (
    VBA_3D,
    "Online Help/mergedProjects/3D",
    "Online Help/general",
    "Online Help/userinterface",
    "Online Help/ribbons",
    "Online Help/advanced",
    "Online Help/license",
    "Online Help/simulation_acceleration",
    VBA_OVERVIEW,
    WINWRAP,
    SPHINX,
    PYTHON_OVERVIEW,
)


@dataclass(frozen=True)
class ProseBuild:
    """A Knowledge Base built from some Areas of the corpus, with its build report."""

    kb: Path
    tree: Path  # the Collection's readable view
    report: dict[str, Any]


def topic(obj: str, member: str, description: str) -> str:
    """A minimal synthetic VBA topic: one object with one documented member."""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html><head><title>{obj} Object</title>
<script type="text/javascript" src="../whtopic.js"></script></head>
<body>
<p class="VBA-Heading-Object">{obj} Object</p>
<p class="VBA-Heading-Method">{member} ( int turns )</p>
<p class="VBA-Text-Indent">{description}</p>
</body></html>
"""


def write_release(folder: Path, files: dict[str, str | bytes]) -> Path:
    """A synthetic release folder holding the given files, by path relative to the VBA 3D project.

    The other projects and Library folders the cst-release Source expects are created empty; the
    Python reference with an inventory that lists no pages.
    """
    for expected in (*PROJECTS, *LIBRARY_FOLDERS):
        (folder / expected).mkdir(parents=True, exist_ok=True)
    header = b"# Sphinx inventory version 2\n# Project: P\n# Version: 1\n# zlib\n"
    (folder / SPHINX / "objects.inv").write_bytes(header + zlib.compress(b""))
    for rel, content in files.items():
        file = folder / VBA_3D / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            file.write_bytes(content)
        else:
            file.write_text(content, encoding="utf-8")
    return folder


def write_config(
    path: Path, kb: Path, release_folder: Path, include: list[str], exclude: Sequence[str] = ()
) -> Path:
    """Write a minimal configuration with one `cst-2024` Collection."""
    includes = ", ".join(f'"{p}"' for p in include)
    excludes = ", ".join(f'"{p}"' for p in exclude)
    path.write_text(
        f"""
[knowledge_base]
path = '{kb}'

[collections.cst-2024]
release = "2024"

[[collections.cst-2024.sources]]
type = "cst-release"
path = '{release_folder}'
include = [{includes}]
exclude = [{excludes}]
""",
        encoding="utf-8",
    )
    return path
