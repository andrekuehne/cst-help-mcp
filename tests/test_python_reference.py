"""Build the Python Area from the real corpus, then read the files it wrote (the build-then-read seam)."""

from __future__ import annotations

from kb_helpers import ProseBuild

from cst_help_mcp.validate import validate

RESULTS = "python/source/cst.results.html.md"


def _md(build: ProseBuild, locator: str) -> str:
    return (build.tree / locator).read_text(encoding="utf-8")


def test_a_sphinx_page_is_its_main_region_without_sidebars_or_navigation_bars(
    python_build: ProseBuild,
) -> None:
    md = _md(python_build, RESULTS)

    assert md.startswith(
        '---\nrelease: "2024"\narea: "python"\ntitle: "cst.results module"\n'
        'source: "Online Help/Python/source/cst.results.html"\n---\n\n'
        '<a id="cst-results-module"></a>\n# cst.results module\n'
    )
    assert '<a id="general-notes"></a>\n## General Notes\n' in md
    # The navigation bar, the sidebar and the footer, and the headings' permalinks.
    for chrome in ("Navigation", "Quick search", "modules |", "Created using", "¶"):
        assert chrome not in md


def test_code_blocks_admonitions_and_math_are_kept(python_build: ProseBuild) -> None:
    results = _md(python_build, RESULTS)
    radar = _md(python_build, "python/source/cst.radar.html.md")

    assert (
        '```bat\n(venv) >> pip install --no-index --find-links "<CST_STUDIO_SUITE_FOLDER>/Library/Python/'
        'repo/simple" cst-results-2024\n```'
    ) in results
    assert (
        "> **Warning**\n>\n> The package cannot be used with the `cst-studio-suite-link`-package simultaneously.\n"
    ) in results
    # TeX as Sphinx wrote it, between Markdown math delimiters; a list inside an item stays inside it.
    assert (
        r"- The linear chirp characterized by $s(t)=cos(2\pi [f_0 t + \frac{f1 - f0}{2 T_c}t^2])$ for "
        r"$t \in [-\frac{T}{2},\frac{T}{2}]$"
        "\n\n  - Lower frequency $f_0$\n"
    ) in radar
    # Text that would read as an HTML tag is escaped.
    assert r"where \<CST_STUDIO_SUITE_FOLDER> should be replaced" in _md(python_build, "python/main.html.md")


def test_an_entry_has_its_heading_signature_description_and_parameters(python_build: ProseBuild) -> None:
    assert (
        '<a id="cst.results.ResultModule.get_run_ids"></a>\n#### `cst.results.ResultModule.get_run_ids`\n\n'
        "```python\nget_run_ids(treepath: str, skip_nonparametric: bool = False) → List[int]\n```\n\n"
        "Get all existing run ids for a tree item."
    ) in _md(python_build, RESULTS)
    assert (
        "\n**Parameters**\n\n- file (os.PathLike) – String specifying the file to be imported\n"
        "- cad_type (str) – Specifies the CAD type"
    ) in _md(python_build, "python/source/cst.interface.html.md")


def test_every_inventory_object_is_an_api_entry_under_its_dotted_name(python_build: ProseBuild) -> None:
    api = (python_build.tree / "api.md").read_text(encoding="utf-8")
    lines = [line for line in api.splitlines() if " | python | " in line]

    # objects.inv lists 86 classes, 263 properties, 340 methods and 36 functions.
    assert len(lines) == 725
    assert python_build.report["counts"]["failed"] == 0
    assert (
        "| cst.results.ResultModule.get_run_ids | python | "
        "`get_run_ids(treepath: str, skip_nonparametric: bool = False) → List[int]` | "
        "`python/source/cst.results.html.md#cst.results.ResultModule.get_run_ids` |"
    ) in lines
    assert (
        "| cst.results.ProjectFile.init | python | "
        "`init(filepath: os.PathLike, allow_interactive: bool = False) → None` | "
        "`python/source/cst.results.html.md#cst.results.ProjectFile.init` |"
    ) in lines
    # A hidden alias shares its entry with the name Sphinx shows.
    assert (
        "| _cst_results.ProjectFile | python | `class ProjectFile` | "
        "`python/source/cst.results.html.md#cst.results.ProjectFile` |"
    ) in lines
    # Modules are the pages' sections, not API Entries.
    assert not any(line.startswith("| cst.results | ") for line in lines)


def test_links_between_the_sphinx_pages_and_the_robohelp_help_resolve(python_build: ProseBuild) -> None:
    assert "[New and Recent](userinterface/elements/backstage.htm.md#The_New_and_Recent_tab)" in _md(
        python_build, RESULTS
    )
    overview = _md(python_build, "python/python_overview.htm.md")
    assert '\narea: "python"\n' in overview
    assert "[CST Python Libraries](python/main.html.md)" in overview
    assert python_build.report["counts"]["unresolved_links"] == 0
    assert python_build.report["counts"]["missing_anchors"] == 0


def test_the_python_menu_topics_at_the_help_root_belong_to_python(python_build: ProseBuild) -> None:
    # Neither loads whtopic.js, which marks the other topics.
    for locator in ("menu.htm.md", "user_scipts.htm.md"):
        assert '\narea: "python"\n' in _md(python_build, locator)


def test_figures_sized_in_millimetres_become_assets(python_build: ProseBuild) -> None:
    assert python_build.report["counts"]["missing_assets"] == 0
    assert "![FMCW RADAR Model](assets/" in _md(python_build, "python/source/cst.radar.html.md")


def test_the_python_area_leaves_the_knowledge_base_valid(python_build: ProseBuild) -> None:
    assert validate(python_build.kb).problems == []


def test_agents_md_says_where_the_python_reference_is_and_how_to_find_a_dotted_name(
    python_build: ProseBuild,
) -> None:
    agents = (python_build.tree / "AGENTS.md").read_text(encoding="utf-8")

    assert "| `python/` | 9 | Python reference (`cst.interface`, `cst.results`" in agents
    assert "`python/source/`" in agents.split("## Page anatomy")[1]
    assert "cst.results.ResultModule.get_run_ids" in agents.split("## Recipes")[1]
    assert "under `vba_3d/`, `sax_basic/` or `python/`" in agents
