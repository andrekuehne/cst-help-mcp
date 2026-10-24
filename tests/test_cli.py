"""The `cst-help` command line: building, looking up and searching, and clear errors."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import pytest
from kb_helpers import BENCHMARK, SOLVER_HF, write_config

from cst_help_mcp.cli import main
from cst_help_mcp.retrieval import KnowledgeBase


def test_lookup_prints_signature_description_and_locator(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["lookup", "Solver.FrequencyRange", "--kb", str(vba_kb)])

    out = capsys.readouterr().out
    assert code == 0
    assert "Solver.FrequencyRange  [vba-3d, 2024]" in out
    assert "FrequencyRange ( double fmin, double fmax )" in out
    assert "Sets the frequency range for the simulation." in out
    assert f"Locator: {SOLVER_HF}#frequencyrange" in out


def test_lookup_of_an_unknown_name_says_not_documented(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["lookup", "Solver.InventedMethod", "--kb", str(vba_kb)])

    assert code == 1
    assert "not documented" in capsys.readouterr().out


def test_search_command_prints_matching_locators(vba_kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["search", "frequency range", "for", "the", "simulation", "--kb", str(vba_kb)])

    assert code == 0
    assert f"{SOLVER_HF}#frequencyrange" in capsys.readouterr().out


def test_search_command_narrows_by_kind(vba_kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    prose = main(["search", "frequency range", "--kind", "prose", "--kb", str(vba_kb)])
    out = capsys.readouterr().out
    code = main(["search", "frequency range", "--kind", "code", "--kb", str(vba_kb)])

    assert (prose, code) == (0, 1)
    assert f"{SOLVER_HF}#frequencyrange  [vba-3d, topic, 2024]" in out


def test_build_from_cli(corpus_2024: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = write_config(
        tmp_path / "cst-help.toml",
        tmp_path / "kb",
        corpus_2024,
        ["Online Help/mergedProjects/VBA_3D/special_vbasolver/*"],
    )

    code = main(["build", "cst-2024", "--config", str(config)])

    assert code == 0
    assert "Built cst-2024" in capsys.readouterr().out
    assert (tmp_path / "kb" / "cst-2024" / SOLVER_HF).is_file()


def test_missing_configuration_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["build", "cst-2024", "--config", str(tmp_path / "nope.toml")])

    assert code == 2
    assert f"Configuration file not found: {tmp_path / 'nope.toml'}" in capsys.readouterr().err


def test_missing_source_folder_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", tmp_path / "no-such-release", [])

    code = main(["build", "cst-2024", "--config", str(config)])

    assert code == 2
    err = capsys.readouterr().err
    assert "Source folder of collection 'cst-2024' does not exist" in err
    assert "no-such-release" in err


def test_folder_that_is_not_a_release_fails_clearly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "not-a-release").mkdir()
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", tmp_path / "not-a-release", [])

    code = main(["build", "cst-2024", "--config", str(config)])

    assert code == 2
    assert "is not a CST release folder" in capsys.readouterr().err


def test_unknown_collection_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "release" / "Online Help").mkdir(parents=True)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", tmp_path / "release", [])

    code = main(["build", "cst-2025", "--config", str(config)])

    assert code == 2
    assert "Unknown collection 'cst-2025'. Configured collections: cst-2024" in capsys.readouterr().err


def test_missing_knowledge_base_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["lookup", "Solver", "--kb", str(tmp_path)])

    assert code == 2
    assert "No Knowledge Base at" in capsys.readouterr().err


def test_instructions_print_the_mcp_entry_and_an_agents_md_section(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["instructions", "--kb", str(vba_kb)])

    out = capsys.readouterr().out
    assert code == 0
    server = _printed_mcp_entry(out)["mcpServers"]["cst-help"]
    assert Path(server["command"]).stem == "cst-help"
    assert server["args"] == ["serve", "--kb", str(vba_kb.resolve())]
    assert "## CST help" in out
    assert "cst_help_lookup" in out
    assert "not documented" in out


def test_instructions_pin_a_chosen_release(vba_kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["instructions", "--kb", str(vba_kb), "--release", "2024"])

    server = _printed_mcp_entry(capsys.readouterr().out)["mcpServers"]["cst-help"]
    assert server["args"][-2:] == ["--release", "2024"]


def _printed_mcp_entry(out: str) -> Any:
    """The JSON object in the printed instructions, which starts at the first brace."""
    entry, _ = json.JSONDecoder().raw_decode(out, out.index("{"))
    return entry


def test_serving_a_release_the_knowledge_base_lacks_fails_clearly(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["serve", "--kb", str(vba_kb), "--release", "2025"])

    assert code == 2
    assert "has no Release '2025'; available: 2024" in capsys.readouterr().err


def test_lookup_in_an_unknown_area_fails_clearly(vba_kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["lookup", "Solver", "--kb", str(vba_kb), "--area", "vba-4d"])

    assert code == 2
    assert "Unknown Area 'vba-4d' in Release 2024; available: vba-3d" in capsys.readouterr().err


def test_browse_prints_the_entries_of_a_table_of_contents_book(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    book = "Automation and Scripting > Visual Basic (VBA) > 3D Simulation VBA > VBA Objects > Solver"

    code = main(["browse", f"{book} > high frequency", "--kb", str(vba_kb)])

    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith(f"Table of contents > {book} > High Frequency, Release 2024: 5 entries")
    assert f"- Solver (HF)  [{SOLVER_HF}]" in out


def test_browse_prints_the_topics_of_a_keyword(vba_kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["browse", "Solver Object", "--tree", "keywords", "--kb", str(vba_kb)])

    assert code == 0
    assert f"- Solver Object  [{SOLVER_HF}]" in capsys.readouterr().out


def test_browsing_an_unknown_entry_fails_clearly(vba_kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["browse", "No Such Book", "--kb", str(vba_kb)])

    assert code == 2
    assert "No entry 'No Such Book' at the top level" in capsys.readouterr().err


def test_benchmark_command_scores_the_benchmark_and_the_derived_sets(
    release_kb: KnowledgeBase, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["benchmark", "--kb", str(release_kb.path), "--questions", str(BENCHMARK), "--derived", "20"]

    code = main(args)

    out = capsys.readouterr().out
    assert code == 0
    assert "## questions" in out and "## short" in out and "## toc" in out
    assert "Skipped, Areas not built: API-04 (vba-schematic)" in out
    assert "Scored by hand, not here: NODOC-01" in out


def test_benchmark_command_takes_weight_overrides_and_searches_a_grid(
    release_kb: KnowledgeBase, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["benchmark", "--kb", str(release_kb.path), "--questions", str(BENCHMARK), "--derived", "0"]

    code = main([*args, "--weight", "title=12", "--fusion", "rank", "--grid", "body=0.5,1"])

    out = capsys.readouterr().out
    assert code == 0
    assert "title 12, headings 3, body 0.5, keywords 0.5, toc_paths 0.25; fusion rank" in out
    assert "best: " in out
    assert main([*args, "--weight", "colour=1"]) == 2
    assert "Unknown weight 'colour'" in capsys.readouterr().err


def test_logged_queries_become_draft_benchmark_entries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "queries.jsonl"
    records = [
        {
            "tool": "cst_help_search",
            "query": "AR filter macro",
            "areas": ["vba-3d"],
            "locators": ["a.md#x", "b.md"],
        },
        {"tool": "cst_help_search", "query": "AR filter macro", "areas": ["vba-3d"], "locators": ["a.md#x"]},
        {
            "tool": "cst_help_lookup",
            "name": "Solver.UseArfilter",
            "area": None,
            "locators": ["c.md#usearfilter"],
        },
        # Already a question of the benchmark.
        {"tool": "cst_help_search", "query": "disable history step", "areas": None, "locators": []},
    ]
    log.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")

    code = main(["benchmark-drafts", str(log), "--questions", str(BENCHMARK)])

    out = capsys.readouterr().out
    drafts = tomllib.loads(out)["questions"]
    assert code == 0
    assert [(d["id"], d["question"], d["areas"]) for d in drafts] == [
        ("LOG-01", "AR filter macro", ["vba-3d"]),
        ("LOG-02", "Solver.UseArfilter", []),
    ]
    assert drafts[1]["api_entries"] == ["Solver.UseArfilter"]
    # Logged queries are held out, and a human gives their expected sources.
    assert {d["half"] for d in drafts} == {"held-out"}
    assert all(d["sources"] == [] for d in drafts)
    assert "# returned: a.md#x, b.md" in out


def test_read_prints_a_sections_markdown_and_its_links(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["read", f"{SOLVER_HF}#solver", "--kb", str(vba_kb)])

    out = capsys.readouterr().out
    assert code == 0
    assert '<a id="solver"></a>\n# Solver Object (HF)\n' in out
    assert (
        "FDSolver Object -> vba_3d/special_vbasolver/special_vbasolver_fdsolver_object.htm.md (resolved)"
        in out
    )


def test_read_prints_the_page_a_cursor_names_and_the_next_cursor(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["read", SOLVER_HF, "--cursor", "2", "--kb", str(vba_kb)])

    out = capsys.readouterr().out
    assert code == 0
    assert "page 2 of " in out
    assert "--cursor 3" in out


def test_reading_an_unknown_locator_fails_clearly(vba_kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["read", "vba_3d/invented.md", "--kb", str(vba_kb)])

    assert code == 2
    assert "No Document 'vba_3d/invented.md' in Release 2024" in capsys.readouterr().err
