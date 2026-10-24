"""The `cst-help` command line: building, looking up and searching, and clear errors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from kb_helpers import SOLVER_HF, write_config

from cst_help_mcp.cli import main


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
