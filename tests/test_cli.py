"""The `cst-help` command line: building, the instructions for a project, and clear errors."""

from __future__ import annotations

from pathlib import Path

import pytest
from kb_helpers import SOLVER_HF, topic, write_config, write_release

from cst_help_mcp.cli import main


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


def test_build_from_a_release_folder_without_a_configuration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    release = write_release(tmp_path / "install", {"widgets/widget.htm": topic("Widget", "Spin", "Spins.")})
    kb = tmp_path / "elsewhere" / "kb"

    code = main(["build", "cst-2024", "--source", str(release), "--kb", str(kb)])

    assert code == 0
    assert "Built cst-2024" in capsys.readouterr().out
    page = (kb / "cst-2024" / "vba_3d" / "widgets" / "widget.htm.md").read_text(encoding="utf-8")
    assert page.startswith('---\nrelease: "2024"\n')
    assert "Spins." in page


def test_build_from_a_release_folder_takes_the_release_for_any_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    release = write_release(tmp_path / "install", {"widgets/widget.htm": topic("Widget", "Spin", "Spins.")})
    kb = tmp_path / "kb"

    code = main(["build", "latest", "--source", str(release), "--kb", str(kb), "--release", "2025"])

    assert code == 0
    page = (kb / "latest" / "vba_3d" / "widgets" / "widget.htm.md").read_text(encoding="utf-8")
    assert page.startswith('---\nrelease: "2025"\n')


def test_build_from_a_release_folder_needs_a_release_its_name_lacks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    release = write_release(tmp_path / "install", {})

    code = main(["build", "latest", "--source", str(release), "--kb", str(tmp_path / "kb")])

    assert code == 2
    assert "Collection 'latest' needs --release" in capsys.readouterr().err


def test_build_from_a_missing_release_folder_fails_clearly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["build", "cst-2024", "--source", str(tmp_path / "nope"), "--kb", str(tmp_path / "kb")])

    assert code == 2
    assert "Source folder of collection 'cst-2024' does not exist" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("flags", "message"),
    [
        (["--source", "x"], "--source and --kb go together"),
        (["--kb", "x"], "--source and --kb go together"),
        (["--source", "x", "--kb", "y", "--config", "z.toml"], "in place of --config"),
        (["--release", "2024"], "--release goes with --source"),
    ],
)
def test_build_flags_that_do_not_go_together_fail_clearly(
    flags: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        main(["build", "cst-2024", *flags])

    assert message in capsys.readouterr().err


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
    code = main(["instructions", "--kb", str(tmp_path)])

    assert code == 2
    assert "No Knowledge Base at" in capsys.readouterr().err


def test_instructions_print_the_release_folder_and_an_agents_md_section(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["instructions", "--kb", str(vba_kb)])

    out = capsys.readouterr().out
    folder = (vba_kb / "cst-2024").resolve()
    assert code == 0
    assert out.startswith(f"The Knowledge Base of Release 2024:\n  {folder}\n")
    section = out.partition("## CST help\n")[2]
    assert f'claude --add-dir "{folder}"' in section
    assert f'codex --add-dir "{folder}"' in section
    assert "Add Folder to Workspace" in section
    assert "not documented" in section
    assert "^### FrequencyRange" in section
    assert "| `vba_3d/` | " in section
    for gone in ("mcp", "MCP", "cst_help_", "cst-help serve"):
        assert gone not in out


def test_instructions_for_a_release_the_knowledge_base_lacks_fail_clearly(
    vba_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["instructions", "--kb", str(vba_kb), "--release", "2025"])

    assert code == 2
    assert "has no Release '2025'; available: 2024" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["search", "lookup", "browse", "read", "serve", "benchmark"])
def test_the_search_server_commands_are_gone(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main([command, "--kb", "."])

    assert "invalid choice" in capsys.readouterr().err
