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
from cst_help_mcp.retrieval import KnowledgeBase
from cst_help_mcp.server import server_instructions

BROKEN = "widgets/broken.htm"
# A topic whose bytes are not valid UTF-8 fails on its own, without stopping the build.
MIXED_RELEASE: dict[str, str | bytes] = {
    "widgets/widget.htm": topic("Widget", "Spin", "Spins the widget."),
    "widgets/gadget.htm": topic("Gadget", "Turn", "Turns the gadget."),
    BROKEN: topic("Broken", "Fail", "Café.").encode("cp1252"),
    "widgets/skin.htm": "<html><body>A WebHelp skin page, not a topic.</body></html>",
    "widgets/spin.gif": b"GIF89a",
}


def _snapshot(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()}


def test_a_server_opened_before_a_rebuild_keeps_answering_from_its_build(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    first = build_collection(config, "cst-2024")
    first_build = tmp_path / "kb" / "builds" / "cst-2024" / first.build_id
    before = _snapshot(first_build)

    with KnowledgeBase.open(tmp_path / "kb") as running:
        write_release(release, {"widgets/widget.htm": topic("Widget", "Spin", "New.")})
        second = build_collection(config, "cst-2024")

        assert second.build_id != first.build_id
        assert [h.description for h in running.lookup("Widget.Spin")] == ["Old."]
        assert _snapshot(first_build) == before
        with KnowledgeBase.open(tmp_path / "kb") as restarted:
            assert [h.description for h in restarted.lookup("Widget.Spin")] == ["New."]


def test_a_rebuild_removes_the_builds_and_assemblies_no_server_holds(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    build_collection(config, "cst-2024")
    with KnowledgeBase.open(tmp_path / "kb"):
        build_collection(config, "cst-2024")
    third = build_collection(config, "cst-2024")

    kb = tmp_path / "kb"
    assert [p.name for p in (kb / "builds" / "cst-2024").iterdir()] == [third.build_id]
    assert len(list((kb / "assemblies").iterdir())) == 1
    assert (kb / "cst-2024" / "vba_3d/widgets/widget.htm.md").is_file()


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
        "missing_assets": None,
        "unsupported": 1,
    }
    assert report["complete"] is False
    [failure] = report["failures"]
    assert failure["source"].endswith(BROKEN)
    assert "utf-8" in failure["error"]
    assert report["unsupported"] == {".gif": 1}


def test_a_failed_document_marks_the_knowledge_base_incomplete_and_the_server_says_so(
    tmp_path: Path,
) -> None:
    release = write_release(tmp_path / "release", MIXED_RELEASE)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    build_collection(config, "cst-2024")

    with KnowledgeBase.open(tmp_path / "kb") as kb:
        assert kb.incomplete == {"cst-2024": 1}
        assert [h.qualified_name for h in kb.lookup("Widget.Spin")] == ["Widget.Spin"]
        instructions = server_instructions(kb)

    assert "incomplete" in instructions
    assert "1 Document of Collection cst-2024 failed to build" in instructions


def test_strict_makes_a_failed_document_fatal_and_keeps_the_previous_build_active(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    first = build_collection(config, "cst-2024")
    write_release(release, MIXED_RELEASE)

    with pytest.raises(BuildError) as error:
        build_collection(config, "cst-2024", strict=True)

    assert BROKEN in str(error.value)
    assert [p.name for p in (tmp_path / "kb" / "builds" / "cst-2024").iterdir()] == [first.build_id]
    with KnowledgeBase.open(tmp_path / "kb") as kb:
        assert kb.incomplete == {}
        assert [h.description for h in kb.lookup("Widget.Spin")] == ["Old."]


def test_the_cli_prints_a_summary_of_the_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    release = write_release(tmp_path / "release", MIXED_RELEASE)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    code = main(["build", "cst-2024", "--config", str(config)])

    out = capsys.readouterr().out
    assert code == 0
    assert "discovered 4, converted 2, skipped 1, failed 1" in out
    assert "unresolved links 0, missing Assets not checked yet, unsupported items 1" in out
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

    with KnowledgeBase.open(tmp_path / "kb") as kb:
        assert [h.signature for h in kb.lookup("Solver")] == ["Solver Object (HF)"]
        assert kb.lookup("Monitor.FrequencyRange") == []


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
    with KnowledgeBase.open(tmp_path / "kb") as kb:
        assert kb.lookup("Widget.Spin")


def test_files_in_the_readable_view_cannot_be_edited_in_place(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", "Old.")})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])
    build_collection(config, "cst-2024")

    with pytest.raises(PermissionError):
        (tmp_path / "kb" / "cst-2024" / "vba_3d/widgets/widget.htm.md").write_text("edited", encoding="utf-8")
    assert main(["validate", "--kb", str(tmp_path / "kb")]) == 0


def test_a_build_in_which_every_document_fails_is_an_error(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {BROKEN: MIXED_RELEASE[BROKEN]})
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    with pytest.raises(BuildError) as error:
        build_collection(config, "cst-2024")

    assert "No Documents could be converted" in str(error.value)
    assert BROKEN in str(error.value)
