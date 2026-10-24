"""Build the VBA 3D Area from the real corpus, then query it (the build-then-query seam)."""

from __future__ import annotations

import json
from pathlib import Path

from kb_helpers import SOLVER_HF

VBA_OVERVIEW = "vba/vba_macro_language_overview.htm.md"

from cst_help_mcp.retrieval import KnowledgeBase


def test_lookup_returns_signature_description_and_locator(kb: KnowledgeBase) -> None:
    hits = kb.lookup("Solver.FrequencyRange")

    hf = [h for h in hits if h.locator == f"{SOLVER_HF}#frequencyrange"]
    assert len(hf) == 1
    entry = hf[0]
    assert entry.area == "vba-3d"
    assert entry.release == "2024"
    assert entry.qualified_name == "Solver.FrequencyRange"
    assert entry.signature == "FrequencyRange ( double fmin, double fmax )"
    assert entry.description.startswith("Sets the frequency range for the simulation.")
    assert "results will be deleted" in entry.description


def test_lookup_ignores_case(kb: KnowledgeBase) -> None:
    hits = kb.lookup("solver.frequencyrange")

    assert f"{SOLVER_HF}#frequencyrange" in [h.locator for h in hits]


def test_bare_member_name_returns_every_object_that_has_it(kb: KnowledgeBase) -> None:
    names = {h.qualified_name for h in kb.lookup("FrequencyRange")}

    assert {"Solver.FrequencyRange", "Monitor.FrequencyRange", "TOUCHSTONE.FrequencyRange"} <= names
    assert "MeshAdaption3D.SetFrequencyRange" not in names


def test_same_titled_solver_pages_stay_distinct(kb: KnowledgeBase) -> None:
    hits = kb.lookup("Solver")

    assert {h.locator for h in hits} == {
        f"{SOLVER_HF}#solver",
        "vba_3d/special_vbasolver/special_vba_ems_solver_object.htm.md#solver",
    }
    assert {h.signature for h in hits} == {"Solver Object (HF)", "Solver Object (LF)"}


def test_application_methods_resolve_by_bare_name(kb: KnowledgeBase) -> None:
    hits = kb.lookup("AddToHistory")

    assert [h.qualified_name for h in hits] == ["Project.AddToHistory"]
    assert hits[0].locator.startswith("vba_3d/common_vbaapp/common_vbaappapplication_object.htm.md#")


def test_member_headings_are_recognised_whatever_the_class_case(kb: KnowledgeBase) -> None:
    hits = kb.lookup("Material.SpecificHeat")

    assert [h.signature for h in hits] == ["SpecificHeat ( double dValue, string unit )"]


def test_multi_name_headings_are_split_into_one_entry_per_name(kb: KnowledgeBase) -> None:
    hits = kb.lookup("ColourMapPlot.SetYRange")

    assert [h.signature for h in hits] == ["SetYRange ( double min, double max )"]
    assert hits[0].locator.endswith("#setyrange")
    assert kb.lookup("ColourMapPlot.SetXRange")[0].locator.endswith("#setxrange")


def test_code_samples_render_as_fenced_blocks_that_keep_indentation(vba_kb: Path) -> None:
    md = (vba_kb / "cst-2024/vba_3d/common_vbacablestudio/cablebundles/bundlerename.htm.md").read_text(
        encoding="utf-8"
    )

    assert (
        '```vba\nWith CableStudio\n    .Reset\n    .InputName "CSBundle", "OldName", "R5_Bundle_1_1"\n'
    ) in md
    assert '    .Execute "BundleRename"\nEnd With\n```' in md


def test_markdown_has_frontmatter_and_the_model_is_persisted_next_to_it(vba_kb: Path) -> None:
    md_path = vba_kb / "cst-2024" / SOLVER_HF
    md = md_path.read_text(encoding="utf-8")

    assert md.startswith(
        "---\n"
        'release: "2024"\n'
        'area: "vba-3d"\n'
        'title: "Solver Object"\n'
        'source: "Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm"\n'
        "---\n"
    )
    model = json.loads(md_path.with_name(md_path.name + ".json").read_text(encoding="utf-8"))
    assert model["locator"] == SOLVER_HF
    assert model["area"] == "vba-3d"
    assert "Solver.FrequencyRange" in [e["qualified_name"] for e in model["api_entries"]]


def test_navigation_boilerplate_is_left_out(vba_kb: Path) -> None:
    md = (vba_kb / "cst-2024" / SOLVER_HF).read_text(encoding="utf-8")

    for boilerplate in ("ds_simulia", "3dexp", "addTocInfo", "CST Studio Suite 2024", "General Methods\n- "):
        assert boilerplate not in md


def test_benchmark_api_01_resolves_through_lookup(kb: KnowledgeBase) -> None:
    """API-01: "set the solver frequency range to 1–10 GHz" → `Solver.FrequencyRange`."""
    hits = kb.lookup("Solver.FrequencyRange")

    top_sources = [h.source_path for h in hits[:5]]
    assert (
        "Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm"
        in top_sources
    )


def test_search_finds_vba_topics_by_plain_words(kb: KnowledgeBase) -> None:
    hits = kb.search("results deleted when the frequency range changes")

    assert f"{SOLVER_HF}#frequencyrange" in [h.locator for h in hits]
    assert all(h.area == "vba-3d" and h.release == "2024" for h in hits)


def test_search_never_fails_on_punctuation(kb: KnowledgeBase) -> None:
    assert kb.search('Solver.FrequencyRange( "1" ) AND OR NEAR* $') is not None


def test_signatures_wrapped_over_two_heading_lines_are_joined(kb: KnowledgeBase) -> None:
    hits = kb.lookup("Solid.SetMeshRefinement")

    assert [h.signature for h in hits] == [
        (
            "SetMeshRefinement ( solidname solid1, bool edgeRefine, double edgeRefineFact,"
            " bool volumeRefine, double volumeRefineFact )"
        )
    ]
    assert kb.lookup("bool") == []


def test_prose_styled_as_a_member_heading_is_not_an_api_entry(kb: KnowledgeBase) -> None:
    assert kb.lookup("Specifies") == []
    assert "Specifies the duration of the simulation." in "\n".join(
        h.snippet for h in kb.search("duration of the simulation", areas=["vba-3d"])
    )


def test_pages_without_members_do_not_become_api_entries(kb: KnowledgeBase) -> None:
    assert kb.lookup("Home") == []


def test_objects_whose_heading_lacks_the_object_suffix_still_qualify_their_members(
    kb: KnowledgeBase,
) -> None:
    hits = kb.lookup("DopingDensityFieldImport.Reset")

    assert len(hits) == 1
    assert kb.lookup("Reset") and all("." in h.qualified_name for h in kb.lookup("Reset"))


def test_application_object_methods_resolve_under_application_too(kb: KnowledgeBase) -> None:
    hits = kb.lookup("Application.AddToHistory")

    assert [h.qualified_name for h in hits] == ["Project.AddToHistory"]


def test_the_root_vba_overview_belongs_to_the_vba_3d_area(vba_kb: Path, kb: KnowledgeBase) -> None:
    md = (vba_kb / "cst-2024" / VBA_OVERVIEW).read_text(encoding="utf-8")

    assert md.startswith(
        '---\nrelease: "2024"\narea: "vba-3d"\ntitle: "VBA Overview"\n'
        'source: "Online Help/vba/vba_macro_language_overview.htm"\n'
    )
    hits = kb.search("macro editor debugger OLE automation", areas=["vba-3d"])
    assert VBA_OVERVIEW in [h.locator.partition("#")[0] for h in hits[:3]]
