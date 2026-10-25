"""Build the 3D Simulation and General Areas from the real corpus, then query them (the build-then-query seam)."""

from __future__ import annotations

import re

from kb_helpers import ProseBuild

from cst_help_mcp.retrieval import KnowledgeBase

BRICK = "3d/common_struct/common_struct_brick.htm.md"
POLARIZATION = "3d/special_theory/special_theory_polarization.htm.md"
MATERIAL_OVERVIEW = "3d/special_overview/special_overview_material_overview_hf.htm.md"
MODELING_RIBBON = "ribbons/3d/common_ribbons_modeling.htm.md"


def _md(build: ProseBuild, locator: str) -> str:
    return (build.tree / locator).read_text(encoding="utf-8")


def test_the_brick_dialog_page_renders_its_prose_and_field_definitions(prose_build: ProseBuild) -> None:
    md = _md(prose_build, BRICK)

    assert md.startswith(
        '---\nrelease: "2024"\narea: "3d"\ntitle: "Create a Brick"\n'
        'source: "Online Help/mergedProjects/3D/common_struct/common_struct_brick.htm"\n'
        'keywords: ["Brick", "Brick Dialog", "Create a Brick"]\n---\n\n# Create a Brick\n'
    )
    # The introduction is <h3> in the source.
    assert (
        "\n\nIn this dialog box you may specify the dimensions of a brick either numerically or by using"
        " [expressions](3d/common_general/common_general_expression.htm.md)."
    ) in md
    assert (
        "\n**Name**\n: Specify the unique [name](3d/common_general/common_general_name.htm.md) for the brick.\n"
        in md
    )
    assert "\n**Cancel**\n: Closes this dialog box without performing any further action.\n" in md
    assert "[Sphere](3d/common_struct/common_struct_sphere.htm.md), [Cylinder](" in md


def test_the_navigation_boilerplate_is_left_out(prose_build: ProseBuild) -> None:
    md = _md(prose_build, BRICK)

    for boilerplate in (
        "ds_simulia",
        "3dexp",
        "3ds.png",
        "addTocInfo",
        "CST Studio Suite 2024",
        "FilePopupInit",
    ):
        assert boilerplate not in md
    # Spacer paragraphs leave no empty blocks.
    assert "\n\n\n" not in md


def test_the_brick_dialog_page_is_found_by_search(prose_kb: KnowledgeBase) -> None:
    hits = prose_kb.search("brick dimensions expressions coordinate system", areas=["3d"])

    assert BRICK in [h.locator.partition("#")[0] for h in hits[:3]]
    # Search records hold the link labels, not their Locators.
    assert all("common_general_expression" not in h.snippet for h in hits)


def test_the_polarization_theory_page_keeps_its_text_and_tex(prose_build: ProseBuild) -> None:
    md = _md(prose_build, POLARIZATION)

    assert "# Polarization\n\nElectromagnetic waves are transversal waves." in md
    assert r"\begin{equation} \vec{E} = \left(\begin{array}{c} e_1 \\ e_2 \\ 0 \end{array}\right)" in md


def test_the_polarization_theory_page_is_found_by_search(prose_kb: KnowledgeBase) -> None:
    hits = prose_kb.search("left circular polarization IEEE convention")

    assert hits[0].locator == POLARIZATION
    assert hits[0].area == "3d"


def test_subheadings_open_sections_and_back_to_top_links_are_dropped(prose_build: ProseBuild) -> None:
    md = _md(prose_build, MATERIAL_OVERVIEW)

    # <h5><a name="Conductivity Model"></a>Conductivity Models</h5>: the name is no valid fragment.
    assert '<a id="conductivity-model"></a>\n#### Conductivity Models\n' in md
    # The source has "up" links back to its contents list before each subheading.
    assert not [line for line in md.split("\n") if line.endswith(" up") or "[up]" in line]


def test_note_paragraphs_become_notes(prose_build: ProseBuild) -> None:
    # <p class="Topic-Text-Indent"><span>Note:</span> ...</p>
    assert "\n> **Note:** For changing the name of a curve item, please choose [Navigation tree:](" in _md(
        prose_build, "3d/common_struct/common_struct_changecurve.htm.md"
    )
    # <p class="Tip-Note-Heading">Note:</p> followed by the note's text.
    assert "\n> **Note:** Selecting the center of the twist by a User defined center" in _md(
        prose_build, "3d/cbls/creating_harness/cable_library/cable_groups.htm.md"
    )


def test_simple_tables_render_as_markdown(prose_build: ProseBuild) -> None:
    md = _md(prose_build, POLARIZATION)

    # A figure grid: the figures in the first row, their captions below them.
    assert re.search(
        r"\n\| !\[\]\(assets/\w+\.png\) \| !\[\]\(assets/\w+\.png\) \|\n\|---\|---\|\n"
        r"\| Left circular polarization \(LCP\) \| Right circular polarization \(RCP\) \|\n",
        md,
    )


def test_tables_with_merged_cells_stay_html(prose_build: ProseBuild) -> None:
    md = _md(prose_build, "3d/special_solvopt/special_solvopt_lumpedelements.htm.md")

    assert '<td colspan="3">Multipin sub-element Define an element to be used with a <a href="3d/' in md


def test_commented_out_content_is_dropped(prose_build: ProseBuild) -> None:
    # Every "Modal Analysis" in the source sits inside an HTML comment.
    assert "Modal Analysis" not in _md(prose_build, "3d/special_overview/special_overview_whichsolver.htm.md")


def test_links_are_resolved_without_regard_to_case_and_rewritten_as_locators(prose_build: ProseBuild) -> None:
    # The source links to userinterface/views/ParametricResultsOverview.htm; the file is lowercase.
    assert "[Parametric Results Overview](userinterface/views/parametricresultsoverview.htm.md)" in _md(
        prose_build, "3d/special_postpr/special_postpr_sensitivity_tuning.htm.md"
    )
    # A fragment into another project resolves to the target Section's anchor.
    assert "The [Preferences](userinterface/dialog/options.htm.md#options_preferences) dialog" in _md(
        prose_build, "general/common_overview_autoupdate.htm.md"
    )


def test_popup_links_become_ordinary_links(prose_build: ProseBuild) -> None:
    # A BSSCPopup link names its target only in its onclick script.
    md = _md(prose_build, "3d/special_solvopt/special_solvopt_cht_time_step_settings.htm.md")

    assert (
        ".png) [Simulation:](3d/common_ribbons/3d/common_ribbons_simulation_hf.htm.md) Solver > Setup Solver"
        in md
    )


def test_external_links_keep_their_url_and_links_outside_the_corpus_their_label(
    prose_build: ProseBuild,
) -> None:
    assert "[3ds.com/Support](https://www.3ds.com/support)" in _md(prose_build, "general/welcome_de.htm.md")
    # PCB is a project outside these Areas.
    family = _md(prose_build, "general/cst_studio_family.htm.md")
    assert "<td>CST PCB Studio™ is a tool" in family
    assert "mergedprojects/pcb" not in family.lower()


def test_topics_outside_any_table_of_contents_are_included(prose_kb: KnowledgeBase) -> None:
    # No ribbon topic appears in a table of contents (research §3.1).
    hits = prose_kb.search("modeling ribbon", areas=["general"])

    assert MODELING_RIBBON in [h.locator.partition("#")[0] for h in hits]


def test_ribbon_topics_copied_into_the_3d_project_are_aliases_of_the_general_ones(
    prose_build: ProseBuild, prose_kb: KnowledgeBase
) -> None:
    md = _md(prose_build, MODELING_RIBBON)

    assert 'area: "general"' in md
    assert '"Online Help/mergedProjects/3D/common_ribbons/3d/common_ribbons_modeling.htm"' in md
    assert not (prose_build.tree / "3d/common_ribbons/3d/common_ribbons_modeling.htm.md").exists()
    # A link to the 3D copy reaches the Document (the Brick dialog's ribbon path).
    assert "## ![shape brick icon](assets/" in _md(prose_build, BRICK)
    assert f" [Modeling:]({MODELING_RIBBON}) Shapes > Brick\n" in _md(prose_build, BRICK)
    assert len({h.locator for h in prose_kb.search("Modeling ribbon")} & {MODELING_RIBBON}) <= 1
    assert prose_build.report["counts"]["aliases"] > 10


def test_the_report_counts_links_by_status_and_lists_the_unresolved_ones(prose_build: ProseBuild) -> None:
    report = prose_build.report

    assert report["complete"] is True
    assert report["links"]["resolved"] > 5000
    assert report["links"]["external"] > 0
    assert report["links"]["outside"] > 0
    # A fragment written without its "#" (research §8).
    assert {
        "source": "Online Help/mergedProjects/3D/cbls/creating_harness/export_to_mws.htm",
        "href": "Online Help/mergedProjects/3D/cbls/creating_harness/+Selected_Segments",
    } in report["unresolved_links"]
    assert report["counts"]["unresolved_links"] == len(report["unresolved_links"]) < 20


def test_the_python_menu_topics_at_the_help_root_belong_to_general(prose_kb: KnowledgeBase) -> None:
    # Neither loads whtopic.js, which marks the other topics.
    apps = prose_kb.search("CST Apps python wheel repo", areas=["general"])
    scripts = prose_kb.search("user scripts library directories update", areas=["general"])

    assert apps[0].locator == "menu.htm.md"
    assert scripts[0].locator == "user_scipts.htm.md"


def test_a_search_narrowed_to_an_alias_area_finds_the_document(
    prose_build: ProseBuild, prose_kb: KnowledgeBase
) -> None:
    # The Modeling ribbon topic is a General Document, also published in the 3D project.
    assert 'alias_areas: ["3d"]\n' in _md(prose_build, MODELING_RIBBON)
    hits = [
        h for h in prose_kb.search("modeling ribbon", areas=["3d"]) if h.locator.startswith(MODELING_RIBBON)
    ]

    assert hits
    assert {h.area for h in hits} == {"general"}


def test_links_to_files_missing_from_the_release_folder_are_unresolved_but_do_not_fail_the_build(
    prose_build: ProseBuild,
) -> None:
    report = prose_build.report

    # This release folder ships no Videos/ folder.
    assert {
        "source": "Online Help/general/getting_started_videos.htm",
        "href": "Videos/Quick_Intro_Video/QS_V3.html",
    } in report["unresolved_links"]
    assert report["complete"] is True


def test_outside_links_are_counted_by_where_they_lead(prose_build: ProseBuild) -> None:
    outside = prose_build.report["outside_links"]

    # A project this build does not read, and the manuals in Documentation/.
    assert outside["Online Help/mergedProjects/DES"] > 0
    assert outside[".pdf"] >= 9
    assert "Online Help/mergedProjects/3D" not in outside
    assert sum(outside.values()) == prose_build.report["links"]["outside"]


def test_fragments_that_match_no_anchor_are_listed(prose_build: ProseBuild) -> None:
    report = prose_build.report

    # The target names its Section "Mesh_Control_Items".
    assert {
        "source": "Online Help/mergedProjects/3D/common_modi/common_modi_meshmode.htm",
        "href": "Online Help/mergedProjects/3D/common_overview/common_overview_mesh.htm#Mesh_Control_Regions",
    } in report["missing_anchors"]
    assert report["counts"]["missing_anchors"] == len(report["missing_anchors"])
