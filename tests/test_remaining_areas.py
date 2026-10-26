"""Build the Areas outside the proof-of-concept slice from the real corpus, then read the files it
wrote (the build-then-read seam): Circuits, PCB, Filter Designer, Chip Interface, VBA schematic,
the Example Projects and every manual."""

from __future__ import annotations

import json
import re

from kb_helpers import ProseBuild

FILTER_EXAMPLE = "filter_designer_3d/example/bandpass_filter_combline.htm.md"
PCB_RESULT_VIEWER = "pcb/pcbs/5_simulating_a_pcb/2d_result_viewer.htm.md"
BLOCK = "vba_des/special_vbacommands/blockobject.htm.md"
RELEASE_NOTES = "manuals/CST Studio Suite - Release Notes.pdf.md"


def _md(build: ProseBuild, locator: str) -> str:
    return (build.tree / locator).read_text(encoding="utf-8")


def _frontmatter(build: ProseBuild, locator: str) -> dict[str, object]:
    head = _md(build, locator).removeprefix("---\n").partition("\n---\n")[0]
    return {key: json.loads(value) for key, _, value in (line.partition(": ") for line in head.splitlines())}


def test_each_remaining_project_builds_into_its_area(remaining_build: ProseBuild) -> None:
    areas = {
        "des/components/block/import/capacitancematrixblock.htm.md": "circuits",
        PCB_RESULT_VIEWER: "pcb",
        FILTER_EXAMPLE: "filter-designer",
        "chi/getting_started/welcome.htm.md": "chip-interface",
        BLOCK: "vba-schematic",
        "exp_hf/examplesoverview/patch_antenna.htm.md": "example-projects",
    }

    assert {locator: _frontmatter(remaining_build, locator)["area"] for locator in areas} == areas
    assert remaining_build.report["complete"]


def test_child_projects_carry_their_place_in_the_root_table_of_contents(remaining_build: ProseBuild) -> None:
    paths = _frontmatter(remaining_build, BLOCK)["toc_paths"]

    assert isinstance(paths, list)
    assert any(path.startswith("Automation and Scripting > Visual Basic (VBA) > ") for path in paths)
    assert remaining_build.report["navigation"]["toc_entries"] > 0


def test_a_heading_styled_as_body_text_stays_a_heading(remaining_build: ProseBuild) -> None:
    # <h4 class="Tip-Note-Text">General Description</h4>
    assert re.search(r"^#+ General Description$", _md(remaining_build, FILTER_EXAMPLE), re.MULTILINE)
    # <h2 class="Tip-Note-Text">2D/3D Plot: Plot Type</h2>, a Ribbon Path like its unstyled siblings.
    viewer = _md(remaining_build, PCB_RESULT_VIEWER)
    assert re.search(r"^## \[2D/3D Plot:\]\(.*\) Plot Type$", viewer, re.MULTILINE)
    assert re.search(r"^## \[2D/3D Plot:\]\(.*\) Plot Properties$", viewer, re.MULTILINE)


def test_vba_schematic_entries_stay_apart_from_vba_3d_entries_with_the_same_name(
    remaining_build: ProseBuild,
) -> None:
    api = (remaining_build.tree / "api.md").read_text(encoding="utf-8")
    sweeps = [line for line in api.splitlines() if line.startswith("| ParameterSweep |")]

    assert [line.split(" | ")[1] for line in sweeps] == ["vba-3d", "vba-schematic"]
    assert "`vba_des/special_vbacommands/parametersweepobject.htm.md#parametersweep`" in sweeps[1]
    assert re.search(
        r"^\| Block\.SetDoubleProperty \| vba-schematic \| `SetDoubleProperty \(", api, re.MULTILINE
    )
    assert '<a id="setdoubleproperty"></a>\n### SetDoubleProperty\n' in _md(remaining_build, BLOCK)


def test_example_projects_no_table_of_contents_reaches_are_included(remaining_build: ProseBuild) -> None:
    cables = sorted(p.name for p in (remaining_build.tree / "exp_cbl").rglob("*.md"))

    assert len(cables) == 7
    assert "cs_introduction.htm.md" in cables
    assert "# Cable Examples" in _md(remaining_build, "exp_cbl/cs_introduction.htm.md")


def test_every_manual_and_the_release_notes_build_but_not_fest3d_or_spark3d(
    remaining_build: ProseBuild,
) -> None:
    manuals = sorted(p.name for p in (remaining_build.tree / "manuals").glob("*.pdf"))

    assert len(manuals) == 9
    assert "CST Studio Suite - Release Notes.pdf" in manuals
    assert "CST Studio Suite - Low Frequency Simulation.pdf" in manuals
    assert not any("FEST3D" in name or "SPARK3D" in name for name in manuals)
    page_10 = _md(remaining_build, RELEASE_NOTES).partition("\n## page-10\n")[2].partition("\n## page-11")[0]
    assert "Python" in page_10


def test_agents_md_describes_the_new_folders_and_counts_vba_des_as_documentation(
    remaining_build: ProseBuild,
) -> None:
    agents = _md(remaining_build, "AGENTS.md")

    for folder in ("des", "pcb", "filter_designer_3d", "chi", "vba_des", "exp_cbl", "exp_hf"):
        row = next(line for line in agents.splitlines() if line.startswith(f"| `{folder}/` |"))
        assert not row.endswith("|  |"), row
    assert "no page under `vba_3d/`, `vba_des/`" in agents
    assert "Release Notes" in agents
