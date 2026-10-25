"""Immutable Builds, assembly and the pointer switch, the build report and failures (ADR 0009).

Synthetic release folders stand in for the corpus, which has no failures to provoke.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from kb_helpers import topic, write_config, write_release

from cst_help_mcp.build import build_collection
from cst_help_mcp.cli import main
from cst_help_mcp.errors import BuildError

BROKEN = "widgets/broken.htm"
# A topic whose bytes are not valid UTF-8 fails on its own, without stopping the build.
MIXED_RELEASE: dict[str, str | bytes] = {
    "widgets/widget.htm": topic("Widget", "Spin", "Spins the widget."),
    "widgets/gadget.htm": topic("Gadget", "Turn", "Turns the gadget."),
    BROKEN: topic("Broken", "Fail", "Café.").encode("cp1252"),
    "widgets/skin.htm": "<html><body>A WebHelp skin page, not a topic.</body></html>",
    "widgets/spin.avi": b"RIFF",
}


WIDGET = "vba_3d/widgets/widget.htm.md"


def _view(kb: Path, locator: str = WIDGET) -> str:
    return (kb / "cst-2024" / locator).read_text(encoding="utf-8")


def _files(folder: Path) -> list[str]:
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


def test_a_rebuild_switches_the_view_and_removes_the_older_build_and_assembly(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    first = build_collection(config, "cst-2024")
    assert "Old." in _view(tmp_path / "kb")
    write_release(release, {"widgets/widget.htm": topic("Widget", "Spin", "New.")})

    second = build_collection(config, "cst-2024")

    kb = tmp_path / "kb"
    assert second.build_id != first.build_id
    assert "New." in _view(kb)
    assert [p.name for p in (kb / "builds" / "cst-2024").iterdir()] == [second.build_id]
    assert len(list((kb / "assemblies").iterdir())) == 1


def test_the_tree_holds_only_what_agents_read_and_the_build_data_stays_beside_it(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", MIXED_RELEASE)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    result = build_collection(config, "cst-2024")

    build = tmp_path / "kb" / "builds" / "cst-2024" / result.build_id
    assert sorted(p.name for p in build.iterdir()) == [
        "api.json",
        "assets.json",
        "build.json",
        "navigation.json",
        "report.json",
        "tree",
    ]
    pages = ["vba_3d/widgets/gadget.htm.md", WIDGET]
    assert _files(build / "tree") == pages
    # Assembly adds the entry and workspace files to the view.
    view = tmp_path / "kb" / "cst-2024"
    assert _files(view) == ["AGENTS.md", "CLAUDE.md", "api.md", "keywords.md", "toc.md", *pages]
    assert not (tmp_path / "kb" / "index.sqlite").exists()
    assert [p.name for p in (tmp_path / "kb" / "assemblies").rglob("*") if p.is_file()] == ["assembly.json"]


def test_the_build_report_counts_documents_and_lists_failures(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", MIXED_RELEASE)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    result = build_collection(config, "cst-2024")

    report = json.loads(
        (tmp_path / "kb" / "builds" / "cst-2024" / result.build_id / "report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["counts"] == {
        "discovered": 4,
        "converted": 2,
        "skipped": 1,
        "aliases": 0,
        "failed": 1,
        "unresolved_links": 0,
        "missing_anchors": 0,
        "assets": 0,
        "missing_assets": 0,
        "unsupported": 1,
        "library_left_out": 0,
        "unpaired_math": 0,
    }
    assert report["complete"] is False
    [failure] = report["failures"]
    assert failure["source"].endswith(BROKEN)
    assert "utf-8" in failure["error"]
    assert report["unsupported"] == {".avi": 1}


def test_a_failed_document_marks_the_knowledge_base_incomplete_and_the_instructions_say_so(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    release = write_release(tmp_path / "release", MIXED_RELEASE)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    build_collection(config, "cst-2024")

    assert main(["instructions", "--kb", str(tmp_path / "kb")]) == 0

    out = capsys.readouterr().out
    assert "This Knowledge Base is incomplete: 1 Document of Collection cst-2024 failed to build" in out
    assert "Spins the widget." in _view(tmp_path / "kb")


def test_strict_makes_a_failed_document_fatal_and_keeps_the_previous_build_active(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    first = build_collection(config, "cst-2024")
    write_release(release, MIXED_RELEASE)

    with pytest.raises(BuildError) as error:
        build_collection(config, "cst-2024", strict=True)

    assert BROKEN in str(error.value)
    assert [p.name for p in (tmp_path / "kb" / "builds" / "cst-2024").iterdir()] == [first.build_id]
    assert "Old." in _view(tmp_path / "kb")
    assert not (tmp_path / "kb" / "cst-2024" / "vba_3d/widgets/gadget.htm.md").exists()


def test_the_cli_prints_a_summary_of_the_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    release = write_release(tmp_path / "release", MIXED_RELEASE)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    code = main(["build", "cst-2024", "--config", str(config)])

    out = capsys.readouterr().out
    assert code == 0
    assert "discovered 4, converted 2, skipped 1, failed 1" in out
    assert "unresolved links 0, missing anchors 0, missing Assets 0, unsupported items 1" in out
    assert f"failed: {BROKEN}" in out.replace("Online Help/mergedProjects/VBA_3D/", "")
    assert "incomplete" in out


def test_strict_from_the_cli_fails_the_build(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    release = write_release(tmp_path / "release", MIXED_RELEASE)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    code = main(["build", "cst-2024", "--config", str(config), "--strict"])

    assert code == 2
    assert BROKEN in capsys.readouterr().err
    assert not (tmp_path / "kb" / "cst-2024").exists()


def test_include_and_exclude_filters_build_part_of_a_release(corpus_2024: Path, tmp_path: Path) -> None:
    config = write_config(
        tmp_path / "cst-help.toml",
        tmp_path / "kb",
        corpus_2024,
        ["Online Help/mergedProjects/VBA_3D/special_vbasolver/*"],
        exclude=["*/SPECIAL_VBA_EMS_SOLVER_OBJECT.htm"],
    )

    build_collection(config, "cst-2024")

    solvers = tmp_path / "kb" / "cst-2024" / "vba_3d" / "special_vbasolver"
    assert (solvers / "special_vbasolver_solver_object.htm.md").is_file()
    assert not (solvers / "special_vba_ems_solver_object.htm.md").exists()
    assert not (tmp_path / "kb" / "cst-2024" / "vba_3d" / "special_vbamonitors").exists()


def test_a_release_folder_without_the_expected_projects_fails_and_keeps_the_previous_build(
    tmp_path: Path,
) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    first = build_collection(config, "cst-2024")
    (release / "Online Help" / "mergedProjects" / "VBA_3D").rename(release / "Online Help" / "elsewhere")

    with pytest.raises(BuildError) as error:
        build_collection(config, "cst-2024")

    assert "not recognised" in str(error.value)
    assert "Online Help/mergedProjects/VBA_3D" in str(error.value)
    assert [p.name for p in (tmp_path / "kb" / "builds" / "cst-2024").iterdir()] == [first.build_id]
    assert "Old." in _view(tmp_path / "kb")


def test_files_in_the_readable_view_cannot_be_edited_in_place(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    build_collection(config, "cst-2024")

    with pytest.raises(PermissionError):
        (tmp_path / "kb" / "cst-2024" / WIDGET).write_text("edited", encoding="utf-8")
    assert main(["validate", "--kb", str(tmp_path / "kb")]) == 0


def test_a_build_in_which_every_document_fails_is_an_error(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {BROKEN: MIXED_RELEASE[BROKEN]})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    with pytest.raises(BuildError) as error:
        build_collection(config, "cst-2024")

    assert "No Documents could be converted" in str(error.value)
    assert BROKEN in str(error.value)
