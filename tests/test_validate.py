"""`cst-help validate` finds a missing or inconsistent Build, database or file; `assemble` repairs the view."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest
from kb_helpers import SOLVER_HF, write_config

from cst_help_mcp.build import build_collection
from cst_help_mcp.cli import main

SOLVERS = "Online Help/mergedProjects/VBA_3D/special_vbasolver/*"
EMS_SOLVER = "vba_3d/special_vbasolver/special_vba_ems_solver_object.htm.md"


@pytest.fixture
def kb(corpus_2024: Path, tmp_path: Path) -> Path:
    build_collection(
        write_config(tmp_path / "cst-help.toml", tmp_path / "kb", corpus_2024, [SOLVERS]), "cst-2024"
    )
    return tmp_path / "kb"


def _validate(kb: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(["validate", "--kb", str(kb)])
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def _only(folder: Path) -> Path:
    [child] = [p for p in folder.iterdir() if not p.name.startswith(".")]
    return child


def _writable(path: Path) -> Path:
    """Clear the read-only flag a Build's files carry, as someone tampering with them would."""
    path.chmod(stat.S_IWRITE | stat.S_IREAD)
    return path


def test_a_fresh_knowledge_base_is_valid(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _validate(kb, capsys)

    assert code == 0
    assert "is valid" in out
    assert "cst-2024: Build " in out
    assert "Documents, complete" in out


def test_a_missing_pointer_is_reported(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (kb / "active.json").unlink()

    code, out = _validate(kb, capsys)

    assert code == 1
    assert "active.json is missing" in out


def test_a_missing_database_is_reported(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (_only(kb / "assemblies") / "index.sqlite").unlink()

    code, out = _validate(kb, capsys)

    assert code == 1
    assert "database" in out
    assert "is missing" in out


def test_a_damaged_database_is_reported(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (_only(kb / "assemblies") / "index.sqlite").write_bytes(b"not a database" * 100)

    code, out = _validate(kb, capsys)

    assert code == 1
    assert "damaged" in out


def test_a_missing_build_is_reported(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build = _only(kb / "builds" / "cst-2024")
    build.rename(build.with_name("elsewhere"))

    code, out = _validate(kb, capsys)

    assert code == 1
    assert f"Build {build.name} of Collection cst-2024 is missing" in out


def test_a_damaged_build_manifest_is_reported(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _writable(_only(kb / "builds" / "cst-2024") / "build.json").write_text("{", encoding="utf-8")

    code, out = _validate(kb, capsys)

    assert code == 1
    assert "build.json is damaged" in out


def test_a_changed_or_missing_file_in_a_build_is_reported(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _only(kb / "builds" / "cst-2024") / "tree"
    _writable(tree / SOLVER_HF).unlink()
    _writable(tree / EMS_SOLVER).write_text("edited", encoding="utf-8")

    code, out = _validate(kb, capsys)

    assert code == 1
    assert f"tree/{SOLVER_HF} is missing" in out
    assert f"tree/{EMS_SOLVER} has changed" in out


def test_a_database_that_disagrees_with_its_builds_is_reported(
    kb: Path, capsys: pytest.CaptureFixture[str], corpus_2024: Path, tmp_path: Path
) -> None:
    solver_only = "Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm"
    config = write_config(tmp_path / "other.toml", tmp_path / "other-kb", corpus_2024, [solver_only])
    build_collection(config, "cst-2024")
    # The database of a Knowledge Base built from a narrower part of the Source.
    (_only(kb / "assemblies") / "index.sqlite").write_bytes(
        (_only(tmp_path / "other-kb" / "assemblies") / "index.sqlite").read_bytes()
    )

    code, out = _validate(kb, capsys)

    assert code == 1
    assert "inconsistent" in out


def test_assemble_restores_a_damaged_view(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _writable(kb / "cst-2024" / SOLVER_HF).unlink()
    code, out = _validate(kb, capsys)
    assert code == 1
    assert f"cst-2024/{SOLVER_HF} is missing" in out

    assert main(["assemble", "--kb", str(kb)]) == 0
    assert "Assembled cst-2024" in capsys.readouterr().out

    code, out = _validate(kb, capsys)
    assert code == 0, out
