"""Build the VBA 3D Area from the real corpus, then read the files it wrote (the build-then-read seam)."""

from __future__ import annotations

import re
from pathlib import Path

from kb_helpers import SOLVER_HF

VBA_OVERVIEW = "vba/vba_macro_language_overview.htm.md"
EMS_SOLVER = "vba_3d/special_vbasolver/special_vba_ems_solver_object.htm.md"
APPLICATION = "vba_3d/common_vbaapp/common_vbaappapplication_object.htm.md"
MATERIAL = "vba_3d/special_vbalayer/special_vbalayerolayer_object.htm.md"
SOLID = "vba_3d/common_vbasolido/common_vbasolido_solid_object.htm.md"
COLOUR_MAP = "vba_3d/common_vbaplot/colourmapplot_object.htm.md"
MQS_SOLVER = "vba_3d/special_vbatransientsolvers/special_vbatransientsolvers_mqstdsolver_object.htm.md"


def _md(kb: Path, locator: str) -> str:
    return (kb / "cst-2024" / locator).read_text(encoding="utf-8")


def _member(name: str) -> re.Pattern[str]:
    """A member heading, as the identifier recipe of AGENTS.md greps for it."""
    return re.compile(rf"^### {re.escape(name)}( / .*)?$", re.MULTILINE)


def test_a_member_is_an_anchored_heading_with_its_signature_and_description(vba_kb: Path) -> None:
    md = _md(vba_kb, SOLVER_HF)

    assert (
        '<a id="frequencyrange"></a>\n### FrequencyRange\n\n```vba\nFrequencyRange ( double fmin, double fmax )\n'
        "```\n\nSets the frequency range for the simulation."
    ) in md
    assert "all previous simulation results will be deleted" in md


def test_a_member_heading_grep_finds_every_object_that_has_it(vba_kb: Path) -> None:
    pages = {
        p.relative_to(vba_kb / "cst-2024").as_posix()
        for p in (vba_kb / "cst-2024" / "vba_3d").rglob("*.md")
        if _member("FrequencyRange").search(p.read_text(encoding="utf-8"))
    }

    assert {
        SOLVER_HF,
        "vba_3d/special_vbamonitors/special_vbamonitors_monitor_object.htm.md",
        "vba_3d/special_vbaimpexp/special_vbaimp_exp_touchstone.htm.md",
    } <= pages
    # MeshAdaption3D has SetFrequencyRange, which is another member.
    assert not any("meshadaption" in p for p in pages)


def test_same_titled_solver_pages_stay_distinct(vba_kb: Path) -> None:
    assert '\ntitle: "Solver Object"\n' in _md(vba_kb, SOLVER_HF)
    assert '\ntitle: "Solver Object"\n' in _md(vba_kb, EMS_SOLVER)
    assert '<a id="solver"></a>\n# Solver Object (HF)\n' in _md(vba_kb, SOLVER_HF)
    assert '<a id="solver"></a>\n# Solver Object (LF)\n' in _md(vba_kb, EMS_SOLVER)


def test_application_methods_are_members_of_the_application_object(vba_kb: Path) -> None:
    assert _member("AddToHistory").search(_md(vba_kb, APPLICATION))


def test_member_headings_are_recognised_whatever_the_class_case(vba_kb: Path) -> None:
    assert "### SpecificHeat\n\n```vba\nSpecificHeat ( double dValue, string unit )\n```" in _md(
        vba_kb, MATERIAL
    )


def test_multi_name_headings_get_an_anchor_per_name(vba_kb: Path) -> None:
    md = _md(vba_kb, COLOUR_MAP)

    assert (
        '<a id="setxrange"></a>\n<a id="setyrange"></a>\n### SetXRange / SetYRange\n\n'
        "```vba\nSetXRange ( double min, double max )\nSetYRange ( double min, double max )\n```"
    ) in md


def test_signatures_wrapped_over_two_heading_lines_are_joined(vba_kb: Path) -> None:
    assert (
        "```vba\nSetMeshRefinement ( solidname solid1, bool edgeRefine, double edgeRefineFact,"
        " bool volumeRefine, double volumeRefineFact )\n```"
    ) in _md(vba_kb, SOLID)


def test_prose_styled_as_a_member_heading_stays_prose(vba_kb: Path) -> None:
    md = _md(vba_kb, MQS_SOLVER)

    assert "\nSpecifies the duration of the simulation.\n" in md
    assert not _member("Specifies").search(md)


def test_code_samples_render_as_fenced_blocks_that_keep_indentation(vba_kb: Path) -> None:
    md = _md(vba_kb, "vba_3d/common_vbacablestudio/cablebundles/bundlerename.htm.md")

    assert (
        '```vba\nWith CableStudio\n    .Reset\n    .InputName "CSBundle", "OldName", "R5_Bundle_1_1"\n'
    ) in md
    assert '    .Execute "BundleRename"\nEnd With\n```' in md


def test_markdown_has_frontmatter_and_no_model_beside_it(vba_kb: Path) -> None:
    md = _md(vba_kb, SOLVER_HF)

    assert md.startswith(
        "---\n"
        'release: "2024"\n'
        'area: "vba-3d"\n'
        'title: "Solver Object"\n'
        'source: "Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm"\n'
        'toc_paths: ["Automation and Scripting > '
    )
    assert not (vba_kb / "cst-2024" / f"{SOLVER_HF}.json").exists()


def test_navigation_boilerplate_is_left_out(vba_kb: Path) -> None:
    md = _md(vba_kb, SOLVER_HF)

    for boilerplate in ("ds_simulia", "3dexp", "addTocInfo", "CST Studio Suite 2024", "General Methods\n- "):
        assert boilerplate not in md


def test_the_root_vba_overview_belongs_to_the_vba_3d_area(vba_kb: Path) -> None:
    assert _md(vba_kb, VBA_OVERVIEW).startswith(
        '---\nrelease: "2024"\narea: "vba-3d"\ntitle: "VBA Overview"\n'
        'source: "Online Help/vba/vba_macro_language_overview.htm"\n'
    )
