"""Helpers for writing test configurations."""

from __future__ import annotations

from pathlib import Path

SOLVER_HF = "vba_3d/special_vbasolver/special_vbasolver_solver_object.htm.md"


def write_config(path: Path, kb: Path, release_folder: Path, include: list[str]) -> Path:
    """Write a minimal configuration with one `cst-2024` Collection."""
    includes = ", ".join(f'"{p}"' for p in include)
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
""",
        encoding="utf-8",
    )
    return path
