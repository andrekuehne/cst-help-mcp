"""Several Collections in one Knowledge Base: Releases side by side, a release-independent folder of
PDFs beside them, and removing a Release (ADR 0005, ADR 0009).

The corpus holds one Release and no folder of PDFs, so synthetic fixtures stand in for both.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from kb_helpers import pdf_collection, release_collection, topic, write_kb_config, write_pdf, write_release

from cst_help_mcp.build import build_collection
from cst_help_mcp.cli import main

ANTENNAS = "Antenna Notes.pdf"
UNVERSIONED = "misc/Meshing Tips.pdf"


def _pdf_folder(folder: Path) -> Path:
    write_pdf(
        folder / ANTENNAS, ["Written for CST Studio Suite 2023", "Patch antennas"], title="Antenna Notes"
    )
    write_pdf(folder / UNVERSIONED, ["Mesh refinement near edges"])
    return folder


def _two_releases_and_pdfs(tmp_path: Path) -> Path:
    """A configuration of Releases 2024 and 2025, each one topic, and a folder of PDFs; all built."""
    collections = [pdf_collection("pdfs", _pdf_folder(tmp_path / "pdfs"))]
    for release in ("2024", "2025"):
        folder = write_release(
            tmp_path / release, {"widgets/widget.htm": topic("Widget", "Spin", f"Spins in {release}.")}
        )
        collections.append(release_collection(f"cst-{release}", release, folder))
    config = write_kb_config(tmp_path / "cst-help.toml", tmp_path / "kb", "".join(collections))
    for name in ("cst-2024", "cst-2025", "pdfs"):
        build_collection(config, name)
    return config


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_a_release_independent_collection_builds_its_pdfs_into_its_own_folder(tmp_path: Path) -> None:
    config = write_kb_config(
        tmp_path / "cst-help.toml", tmp_path / "kb", pdf_collection("pdfs", _pdf_folder(tmp_path / "pdfs"))
    )

    build_collection(config, "pdfs")

    view = tmp_path / "kb" / "pdfs"
    assert (view / ANTENNAS).read_bytes() == (tmp_path / "pdfs" / ANTENNAS).read_bytes()
    companion = _read(view / f"{ANTENNAS}.md")
    assert 'title: "Antenna Notes"' in companion
    assert 'cst_version: "2023"' in companion
    assert "release:" not in companion
    assert "## page-2" in companion
    assert "Patch antennas" in companion
    unversioned = _read(view / f"{UNVERSIONED}.md")
    assert "cst_version:" not in unversioned
    assert "release:" not in unversioned
    index = _read(view / "documents.md")
    assert f"[Antenna Notes](<{ANTENNAS}.md>)" in index
    assert "written for CST 2023" in index
    assert "[Meshing Tips](<misc/Meshing Tips.pdf.md>)" in index
    assert "CST version unknown" in index
    assert not (view / "api.md").exists()


def test_each_release_folder_names_its_release_and_points_at_the_pdfs_beside_it(tmp_path: Path) -> None:
    _two_releases_and_pdfs(tmp_path)

    kb = tmp_path / "kb"
    for release in ("2024", "2025"):
        agents = _read(kb / f"cst-{release}" / "AGENTS.md")
        assert agents.startswith(f"# CST Studio Suite {release} help, as files")
        assert "`../pdfs/`" in agents
        assert "listed in its `documents.md`" in agents
        assert "Spins in" in _read(kb / f"cst-{release}" / "vba_3d/widgets/widget.htm.md")
    pdfs = _read(kb / "pdfs" / "AGENTS.md")
    assert "release-independent" in pdfs
    assert "`documents.md`" in pdfs
    assert "CST Studio Suite 2024 help" not in pdfs
    assert _read(kb / "pdfs" / "CLAUDE.md") == "@AGENTS.md\n"


def test_the_root_agents_md_lists_the_releases_and_tells_a_session_to_stay_in_one(tmp_path: Path) -> None:
    _two_releases_and_pdfs(tmp_path)

    root = _read(tmp_path / "kb" / "AGENTS.md")
    assert "`cst-2024/`: Release 2024" in root
    assert "`cst-2025/`: Release 2025" in root
    assert "stay in one Release" in root
    assert "`pdfs/`" in root
    assert "2 PDFs" in root
    assert _read(tmp_path / "kb" / "CLAUDE.md") == "@AGENTS.md\n"


def test_adding_pdfs_to_the_folder_rebuilds_only_that_collection(tmp_path: Path) -> None:
    config = _two_releases_and_pdfs(tmp_path)
    kb = tmp_path / "kb"
    releases = {name: _builds(kb, name) for name in ("cst-2024", "cst-2025")}
    write_pdf(tmp_path / "pdfs" / "Waveguides.pdf", ["Waveguide ports in CST 2025"])

    build_collection(config, "pdfs")

    assert {name: _builds(kb, name) for name in releases} == releases
    assert "[Waveguides](Waveguides.pdf.md)" in _read(kb / "pdfs" / "documents.md")
    assert "written for CST 2025" in _read(kb / "pdfs" / "documents.md")
    assert "3 PDFs" in _read(kb / "AGENTS.md")


def _builds(kb: Path, collection: str) -> list[str]:
    return sorted(p.name for p in (kb / "builds" / collection).iterdir())


def test_removing_a_release_is_a_command_and_assembly_afterwards_leaves_no_trace_of_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _two_releases_and_pdfs(tmp_path)
    kb = tmp_path / "kb"

    assert main(["remove", "cst-2024", "--kb", str(kb)]) == 0
    assert main(["assemble", "--kb", str(kb)]) == 0

    out = capsys.readouterr().out
    assert "Removed cst-2024" in out
    assert not (kb / "cst-2024").exists()
    assert not (kb / "builds" / "cst-2024").exists()
    assert "cst-2024" not in _read(kb / "AGENTS.md")
    assert "Assembled cst-2024" not in out
    [assembly] = (kb / "assemblies").iterdir()
    assert "cst-2024" not in _read(assembly / "assembly.json")
    assert "Spins in 2025." in _read(kb / "cst-2025" / "vba_3d/widgets/widget.htm.md")
    assert main(["validate", "--kb", str(kb)]) == 0


def test_removing_a_collection_the_knowledge_base_lacks_fails_clearly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _two_releases_and_pdfs(tmp_path)

    assert main(["remove", "cst-2023", "--kb", str(tmp_path / "kb")]) == 2

    assert "has no Collection 'cst-2023'; built: cst-2024, cst-2025, pdfs" in capsys.readouterr().err


def test_the_last_collection_is_not_removed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = write_kb_config(
        tmp_path / "cst-help.toml", tmp_path / "kb", pdf_collection("pdfs", _pdf_folder(tmp_path / "pdfs"))
    )
    build_collection(config, "pdfs")

    assert main(["remove", "pdfs", "--kb", str(tmp_path / "kb")]) == 2

    assert "the only Collection" in capsys.readouterr().err
    assert (tmp_path / "kb" / "pdfs" / ANTENNAS).is_file()


def test_validate_reports_a_missing_documents_md(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = write_kb_config(
        tmp_path / "cst-help.toml", tmp_path / "kb", pdf_collection("pdfs", _pdf_folder(tmp_path / "pdfs"))
    )
    build_collection(config, "pdfs")
    (tmp_path / "kb" / "pdfs" / "documents.md").unlink()

    assert main(["validate", "--kb", str(tmp_path / "kb")]) == 1

    assert "pdfs/documents.md is missing" in capsys.readouterr().out


def test_a_pdf_folder_in_a_release_collection_fails_clearly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    release = write_release(tmp_path / "release", {})
    (tmp_path / "pdfs").mkdir()
    collections = release_collection("cst-2024", "2024", release) + (
        f"\n[[collections.cst-2024.sources]]\ntype = \"pdf-folder\"\npath = '{tmp_path / 'pdfs'}'\n"
    )
    config = write_kb_config(tmp_path / "cst-help.toml", tmp_path / "kb", collections)

    assert main(["build", "cst-2024", "--config", str(config)]) == 2

    assert "makes it release-independent" in capsys.readouterr().err


def test_the_instructions_for_a_project_point_at_the_pdfs_beside_the_release(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _two_releases_and_pdfs(tmp_path)

    assert main(["instructions", "--kb", str(tmp_path / "kb"), "--release", "2024"]) == 0

    out = capsys.readouterr().out
    pdfs = (tmp_path / "kb" / "pdfs").resolve()
    assert f"  {pdfs}\n" in out.partition("Add this section")[0]
    section = out.partition("## CST help\n")[2]
    assert f'claude --add-dir "{pdfs}"' in section
    assert "2 PDFs" in section
    assert "cst-2025" not in out
