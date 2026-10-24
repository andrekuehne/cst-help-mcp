"""Helpers for writing test configurations."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

SOLVER_HF = "vba_3d/special_vbasolver/special_vbasolver_solver_object.htm.md"
VBA_3D = "Online Help/mergedProjects/VBA_3D"


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
    """A synthetic release folder holding the given files, by path relative to the VBA 3D project."""
    (folder / VBA_3D).mkdir(parents=True, exist_ok=True)
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
