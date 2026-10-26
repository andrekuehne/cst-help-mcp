"""`cst-help validate` finds a missing or changed Build, file or link target; `assemble` repairs the view."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest
from kb_helpers import SOLVER_HF, write_config

from cst_help_mcp.build import build_collection
from cst_help_mcp.cli import main

SOLVERS = "Online Help/mergedProjects/VBA_3D/special_vbasolver/*"
EMS_SOLVER = "vba_3d/special_vbasolver/special_vba_ems_solver_object.htm.md"
FD_SOLVER = "vba_3d/special_vbasolver/special_vbasolver_fdsolver_object.htm.md"


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


def test_assemble_restores_a_damaged_view(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _writable(kb / "cst-2024" / SOLVER_HF).unlink()
    code, out = _validate(kb, capsys)
    assert code == 1
    assert f"cst-2024/{SOLVER_HF} is missing" in out

    assert main(["assemble", "--kb", str(kb)]) == 0
    assert "Assembled cst-2024" in capsys.readouterr().out

    code, out = _validate(kb, capsys)
    assert code == 0, out


def test_a_link_to_a_missing_page_is_reported(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    toc = kb / "cst-2024" / "toc.md"
    toc.write_text(
        toc.read_text(encoding="utf-8") + "- [Gone](vba_3d/gone.htm.md#somewhere)", encoding="utf-8"
    )

    code, out = _validate(kb, capsys)

    assert code == 1
    assert "cst-2024/toc.md links to vba_3d/gone.htm.md, which is missing" in out


def test_a_missing_entry_file_is_reported(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (kb / "cst-2024" / "keywords.md").unlink()

    code, out = _validate(kb, capsys)

    assert code == 1
    assert "cst-2024/keywords.md is missing; run cst-help assemble to restore it" in out


def test_a_missing_library_md_is_reported(
    corpus_2024: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", corpus_2024, ["Library/Includes/*"])
    build_collection(config, "cst-2024")
    assert _validate(tmp_path / "kb", capsys)[0] == 0
    (tmp_path / "kb" / "cst-2024" / "library.md").unlink()

    code, out = _validate(tmp_path / "kb", capsys)

    assert code == 1
    assert "cst-2024/library.md is missing; run cst-help assemble to restore it" in out


def test_a_page_whose_link_target_is_gone_is_reported_through_the_link_too(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The Solver page links to the FDSolver page.
    _writable(kb / "cst-2024" / FD_SOLVER).unlink()

    code, out = _validate(kb, capsys)

    assert code == 1
    assert f"cst-2024/{SOLVER_HF} links to {FD_SOLVER}, which is missing" in out


def test_materials_md_links_resolve_and_a_missing_materials_md_is_reported(
    corpus_2024: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    include = ["Library/Materials/Rogers RO3003*", "Library/Materials/Taconic NF-30*"]
    build_collection(
        write_config(tmp_path / "cst-help.toml", tmp_path / "kb", corpus_2024, include), "cst-2024"
    )
    view = tmp_path / "kb" / "cst-2024"
    assert "](<library/Materials/Taconic NF-30 (loss free).mtd>)" in (view / "materials.md").read_text(
        "utf-8"
    )
    assert not (view / "library.md").exists()  # no Library code in this build
    assert _validate(tmp_path / "kb", capsys)[0] == 0
    (view / "materials.md").unlink()

    code, out = _validate(tmp_path / "kb", capsys)

    assert code == 1
    assert "cst-2024/materials.md is missing; run cst-help assemble to restore it" in out
