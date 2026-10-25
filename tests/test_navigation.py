"""Navigation metadata: table-of-contents paths, author keywords and the entry files.

The real corpus exercises all of it except breadcrumbs, which only fill gaps in projects no Area
reads yet; one small synthetic release covers those.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from kb_helpers import SOLVER_HF, VBA_3D, ProseBuild, write_config, write_release

from cst_help_mcp.build import build_collection

IMPORT_SUB_PROJECT = "3d/common_tools/common_tools_importsubproject.htm.md"


def _frontmatter(path: Path) -> dict[str, object]:
    md = path.read_text(encoding="utf-8")
    head = md.removeprefix("---\n").partition("\n---\n")[0]
    return {key: json.loads(value) for key, _, value in (line.partition(": ") for line in head.splitlines())}


def test_a_document_listed_in_several_places_carries_all_its_toc_paths(prose_build: ProseBuild) -> None:
    front = _frontmatter(prose_build.tree / IMPORT_SUB_PROJECT)

    assert front["toc_paths"] == [
        "3D Simulation > CAD Data Import and Export > EDA Import > Import Sub-Project",
        "3D Simulation > Creating and Visualizing Models > Shapes > Import Sub-Project",
    ]


def test_child_project_tables_of_contents_are_spliced_into_the_root_one(vba_kb: Path) -> None:
    front = _frontmatter(vba_kb / "cst-2024" / SOLVER_HF)

    # The root table of contents places VBA_3D under Automation and Scripting > Visual Basic (VBA).
    solver = "Automation and Scripting > Visual Basic (VBA) > 3D Simulation VBA > VBA Objects > Solver"
    assert front["toc_paths"] == [
        f"{solver} > High Frequency > Solver (HF)",
        # Listed again as special_vbasolver_solver_object.htm#bc-1.
        f"{solver} > Particles > Wakefield Solver",
    ]
    assert "Solver Object" in front["keywords"]  # type: ignore[operator]


def test_documents_carry_their_author_keywords_and_sub_keywords(prose_build: ProseBuild) -> None:
    colormap = _frontmatter(prose_build.tree / "3d/special_postpr/special_postpr_pp_colourmap.htm.md")
    coils = _frontmatter(
        prose_build.tree / "3d/common_preloadedmacro/common_preloadedmacro_construct_coils.htm.md"
    )

    assert "2D Colormap" in colormap["keywords"]  # type: ignore[operator]
    assert "Macros > Construct / Coils" in coils["keywords"]  # type: ignore[operator]


def test_documents_carry_their_context_help_ids(prose_build: ProseBuild) -> None:
    front = _frontmatter(prose_build.tree / "userinterface/views/macroview.htm.md")

    assert front["context_ids"] == ["DS_Online_Help_UserInterface_MacroView"]


def _js(xml: str) -> str:
    """A navigation data file as RoboHelp writes it: XML in an escaped JS string."""
    return 'gXMLBuffer ="' + xml.replace("\\", "\\\\").replace('"', '\\"') + '";'


def _topic(title: str, toc_info: str = "") -> str:
    script = f'<script>if (window.addTocInfo) {{ addTocInfo("{toc_info}"); }}</script>' if toc_info else ""
    return f"""<html><head><title>{title}</title>
<script type="text/javascript" src="../whtopic.js"></script>{script}</head>
<body><p>{title} text.</p></body></html>
"""


def test_navigation_paths_resolve_without_regard_to_case_and_breadcrumbs_fill_gaps(tmp_path: Path) -> None:
    # In the corpus, only the example projects have topics in no table of contents; they aren't read yet.
    release = write_release(
        tmp_path / "release",
        {
            "listed/listed.htm": _topic("Listed"),
            "unlisted/unlisted.htm": _topic("Unlisted", r"3D Simulation VBA\nExamples\nUnlisted ®"),
            "whxdata/whtoc_xml.js": _js('<toc root="whtdata0.xml"></toc>'),
            "whxdata/whtdata0_xml.js": _js(
                '<tocdata><book name="3D Simulation VBA">'
                '<item name="Listed &amp; &quot;found&quot;" url="Listed\\LISTED.htm" /></book></tocdata>'
            ),
        },
    )
    root = release / "Online Help" / "whxdata"
    root.mkdir(parents=True)
    (root / "whtoc_xml.js").write_text(_js('<toc root="whtdata0.xml"></toc>'), encoding="utf-8")
    (root / "whtdata0_xml.js").write_text(
        _js(
            '<tocdata><book name="Scripting"><project name="VBA_3D" ref="mergedProjects/VBA_3D" /></book></tocdata>'
        ),
        encoding="utf-8",
    )
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [f"{VBA_3D}/*"])

    build_collection(config, "cst-2024")

    tree = tmp_path / "kb" / "cst-2024" / "vba_3d"
    assert _frontmatter(tree / "listed/listed.htm.md")["toc_paths"] == [
        'Scripting > 3D Simulation VBA > Listed & "found"'
    ]
    assert _frontmatter(tree / "unlisted/unlisted.htm.md")["toc_paths"] == [
        "Scripting > 3D Simulation VBA > Examples > Unlisted ®"
    ]


def _links(md: str) -> list[str]:
    return re.findall(r"\]\((<[^>]+>|[^)\s]+)\)", md)


def test_toc_md_lists_the_table_of_contents_as_nested_links_within_the_tree(prose_build: ProseBuild) -> None:
    md = (prose_build.tree / "toc.md").read_text(encoding="utf-8")

    assert md.startswith('---\nrelease: "2024"\ntitle: "Table of contents"\n---\n\n# Table of contents\n')
    assert (
        "\n      - Time Domain Solver\n"
        "        - [Time Domain Solver Overview](3d/special_overview/special_overview_fdtd_overview.htm.md)\n"
        "        - [Time Domain Solver Settings](3d/special_overview/special_overview_tsolver.htm.md)\n"
    ) in md
    # A book that is a Document of its own links to it.
    assert "\n      - [EM/Circuit Co-Simulation](3d/special_dslink/ds_link.htm.md)\n" in md
    # Entries leading outside the Build, such as DES topics and Fest3D, are left out.
    assert "Fest3D" not in md
    links = _links(md)
    assert len(links) > 200  # the 3D project lists 212 pages, the root project 35
    for link in links:
        assert (prose_build.tree / link.strip("<>").partition("#")[0]).is_file(), link


def test_keywords_md_lists_the_keyword_index_as_nested_links_within_the_tree(prose_build: ProseBuild) -> None:
    md = (prose_build.tree / "keywords.md").read_text(encoding="utf-8")

    assert md.startswith('---\nrelease: "2024"\ntitle: "Keywords"\n---\n\n# Keywords\n')
    assert (
        "\n- 2D Colormap\n"
        "  - [2D Colormap Plot Overview](3d/special_postpr/special_postpr_pp_colourmap.htm.md)\n"
    ) in md
    assert (
        "\n  - Construct / Coils\n"
        "    - [Construct / Coils](3d/common_preloadedmacro/common_preloadedmacro_construct_coils.htm.md)\n"
    ) in md
    links = _links(md)
    assert len(links) > 1000
    for link in links:
        assert (prose_build.tree / link.strip("<>").partition("#")[0]).is_file(), link


def test_the_report_counts_navigation_entries(prose_build: ProseBuild) -> None:
    navigation = prose_build.report["navigation"]

    assert navigation["toc_entries"] > 300
    assert navigation["keywords"] > 900  # 919 in 3D and 366 in the root project, some shared
    # The DES, PCB and VBA projects are not part of this Build.
    assert navigation["toc_entries_dropped"] > 300
    assert navigation["keyword_topics_dropped"] > 500
    assert navigation["context_ids"] > 0
