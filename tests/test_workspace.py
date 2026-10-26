"""Every assembly makes each Release folder a ready-to-open agent workspace (ADR 0013, ADR 0014).

Synthetic release folders stand in for the corpus where a test needs a small, known tree.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from kb_helpers import ProseBuild, topic, write_config, write_release

from cst_help_mcp.build import build_collection
from cst_help_mcp.cli import main

WIDGET = "vba_3d/widgets/widget.htm.md"


def _build(tmp_path: Path, files: dict[str, str | bytes] | None = None) -> Path:
    release = write_release(
        tmp_path / "release",
        files or {"widgets/widget.htm": topic("Widget", "Spin", "Spins the widget.")},
    )
    build_collection(write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, []), "cst-2024")
    return tmp_path / "kb" / "cst-2024"


def test_what_agents_write_survives_every_build_and_assembly(tmp_path: Path) -> None:
    folder = _build(tmp_path)
    assert (folder / "work").is_dir()
    assert (folder / "guides").is_dir()
    (folder / "work" / "sweep.bas").write_text("Sub Main\nEnd Sub\n", encoding="utf-8")
    (folder / "guides" / "ports.md").write_text("# Ports\n", encoding="utf-8")

    _build(tmp_path, {"widgets/widget.htm": topic("Widget", "Spin", "Spins it faster.")})
    assert main(["assemble", "--kb", str(tmp_path / "kb")]) == 0

    assert "Spins it faster." in (folder / WIDGET).read_text(encoding="utf-8")
    assert (folder / "work" / "sweep.bas").read_text(encoding="utf-8") == "Sub Main\nEnd Sub\n"
    assert (folder / "guides" / "ports.md").read_text(encoding="utf-8") == "# Ports\n"


def test_claude_md_imports_agents_md(tmp_path: Path) -> None:
    folder = _build(tmp_path)

    assert (folder / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"


def test_agents_md_names_the_release_and_puts_the_read_rule_first(tmp_path: Path) -> None:
    folder = _build(tmp_path)

    agents = (folder / "AGENTS.md").read_text(encoding="utf-8")

    assert agents.startswith("# CST Studio Suite 2024 help, as files\n")
    rules = agents.partition("## Rules\n\n")[2].partition("\n## ")[0]
    assert rules.startswith("- **Grep finds pages; it never answers.**")
    assert "no context lines" in rules
    assert "Cite the file path and the Release" in rules
    assert "not documented in Release 2024" in rules
    assert "Undocumented Member" in rules
    assert "Open the image file" in rules
    assert "`work/`" in agents
    assert "incomplete" not in agents


def test_agents_md_counts_the_pages_of_each_folder_and_lists_the_index_files(tmp_path: Path) -> None:
    folder = _build(
        tmp_path,
        {
            "widgets/widget.htm": topic("Widget", "Spin", "Spins the widget."),
            "widgets/gadget.htm": topic("Gadget", "Turn", "Turns the gadget."),
        },
    )

    agents = (folder / "AGENTS.md").read_text(encoding="utf-8")

    assert "| `vba_3d/` | 2 |" in agents
    assert "`3d/`" not in agents.partition("## What is where")[2].partition("## ")[0]
    for name in ("toc.md", "keywords.md", "api.md"):
        assert f"`{name}`" in agents
    assert "`api.md`" in agents.partition("## Recipes")[2]


def test_agents_md_lists_the_guides_and_says_they_are_generated(tmp_path: Path) -> None:
    folder = _build(tmp_path)
    agents = (folder / "AGENTS.md").read_text(encoding="utf-8")
    assert "There are no Guides yet" in agents
    # Links between pages, and from a Guide, are relative to the file that holds them (ticket 26).
    assert "relative to the page that holds them" in agents
    assert "`../`" in agents.partition("## Guides\n")[2]
    (folder / "guides" / "ports.md").write_text("# Ports\n", encoding="utf-8")

    assert main(["assemble", "--kb", str(tmp_path / "kb")]) == 0

    guides = (folder / "AGENTS.md").read_text(encoding="utf-8").partition("## Guides\n")[2]
    assert "- `guides/ports.md`" in guides
    assert "generated" in guides


def test_agents_md_says_when_the_knowledge_base_is_incomplete(tmp_path: Path) -> None:
    folder = _build(
        tmp_path,
        {
            "widgets/widget.htm": topic("Widget", "Spin", "Spins the widget."),
            "widgets/broken.htm": topic("Broken", "Fail", "Café.").encode("cp1252"),
        },
    )

    agents = (folder / "AGENTS.md").read_text(encoding="utf-8")

    assert "This Knowledge Base is incomplete: 1 Document of Collection cst-2024 failed to build" in agents


def test_validate_ignores_what_agents_write_into_work(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _build(tmp_path)
    (folder / "work" / "notes.md").write_text("[draft](nowhere.md)\n", encoding="utf-8")

    assert main(["validate", "--kb", str(tmp_path / "kb")]) == 0, capsys.readouterr().out


def test_an_assembly_that_stopped_between_its_renames_loses_no_work(tmp_path: Path) -> None:
    folder = _build(tmp_path)
    # As if an assembly had moved the workspace folders aside and stopped before the new view was in place.
    stopped = tmp_path / "kb" / ".cst-2024.view-retired-1"
    stopped.mkdir()
    (folder / "work").rename(stopped / "work")
    (stopped / "work" / "sweep.bas").write_text("Sub Main\nEnd Sub\n", encoding="utf-8")

    assert main(["assemble", "--kb", str(tmp_path / "kb")]) == 0

    assert (folder / "work" / "sweep.bas").read_text(encoding="utf-8") == "Sub Main\nEnd Sub\n"
    assert not stopped.exists()


def test_agents_md_of_a_real_build_stays_under_12_kb(prose_build: ProseBuild) -> None:
    agents = (prose_build.tree / "AGENTS.md").read_text(encoding="utf-8")

    assert len(agents.encode("utf-8")) < 12 * 1024
    assert "| `3d/` | 1," in agents  # over a thousand pages, with a thousands separator


def test_api_md_lists_every_api_entry_on_one_line(tmp_path: Path) -> None:
    folder = _build(tmp_path)

    lines = (folder / "api.md").read_text(encoding="utf-8").splitlines()

    assert "| Widget | vba-3d | `Widget Object` | `vba_3d/widgets/widget.htm.md#widget` |" in lines
    assert "| Widget.Spin | vba-3d | `Spin ( int turns )` | `vba_3d/widgets/widget.htm.md#spin` |" in lines


def test_api_md_of_a_real_build_finds_every_object_with_a_member(vba_kb: Path) -> None:
    api = (vba_kb / "cst-2024" / "api.md").read_text(encoding="utf-8")

    owners = {
        line.split(" | ")[0].removeprefix("| ") for line in api.splitlines() if ".FrequencyRange " in line
    }

    assert {"Solver.FrequencyRange", "Monitor.FrequencyRange", "TOUCHSTONE.FrequencyRange"} <= owners
    assert not any("SetFrequencyRange" in owner for owner in owners)
    assert (
        "| Solver.FrequencyRange | vba-3d | `FrequencyRange ( double fmin, double fmax )` | "
        "`vba_3d/special_vbasolver/special_vbasolver_solver_object.htm.md#frequencyrange` |"
    ) in api
