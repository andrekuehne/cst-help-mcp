"""Images as Assets: built from the real corpus, then retrieved through the retrieval core."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

import pytest
from kb_helpers import ProseBuild, topic, write_config, write_release
from PIL import Image

from cst_help_mcp.build import build_collection
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.reading import PageImage
from cst_help_mcp.retrieval import KnowledgeBase

WAVEGUIDE = "3d/special_overview/special_overview_waveguideover.htm.md"
WHICH_SOLVER = "3d/special_overview/special_overview_whichsolver.htm.md"
UNITS = "userinterface/overview/units.htm.md"


def test_the_figures_of_a_section_are_returned_as_png_with_their_sources(prose_kb: KnowledgeBase) -> None:
    result = prose_kb.images(f"{WAVEGUIDE}#Port_Modes_Microstrips")

    [dims] = [i for i in result.images if i.sources[0].endswith("/microstrip_dims_kh.png")]
    assert dims.kind == "figure"
    assert dims.mime_type == "image/png"
    assert (dims.width, dims.height) == (294, 150)
    assert dims.locator == f"{WAVEGUIDE}#Port_Modes_Microstrips"
    with Image.open(dims.path) as image:
        assert (image.format, image.size) == ("PNG", (294, 150))


def test_a_figure_comes_with_its_neighbours_in_document_order(prose_kb: KnowledgeBase) -> None:
    [dims] = [
        i
        for i in prose_kb.images(f"{WAVEGUIDE}#Port_Modes_Microstrips").images
        if i.sources[0].endswith("/microstrip_dims_kh.png")
    ]

    result = prose_kb.images(assets=[dims.asset], neighbours=1)

    assert [i.sources[0].rsplit("/", 1)[-1] for i in result.images] == [
        "microstrip_mode_high.png",
        "microstrip_dims_kh.png",
        "microstrip_pickface.png",
    ]
    assert result.images[2].locator == f"{WAVEGUIDE}#Port_Definition___Construction_Microstrips"


def test_a_page_lists_the_images_its_text_shows_with_their_asset_ids_and_captions(
    prose_kb: KnowledgeBase,
) -> None:
    page = prose_kb.read(f"{WHICH_SOLVER}#CST_MICROWAVE_STUDIO_")
    [chart] = prose_kb.images(f"{WHICH_SOLVER}#CST_MICROWAVE_STUDIO_").images

    assert (page.images[0].kind, page.images[0].caption) == ("icon", "solver transient icon")
    assert PageImage(chart.asset, "figure", "") in page.images
    assert f"no caption -> {chart.asset} (figure)" in [str(i) for i in page.images]
    assert all(i.asset in page.text for i in page.images)


def test_icons_are_left_out_unless_asked_for_and_named_after_their_file(prose_kb: KnowledgeBase) -> None:
    figures = prose_kb.images(f"{WHICH_SOLVER}#CST_MICROWAVE_STUDIO_")
    with_icons = prose_kb.images(f"{WHICH_SOLVER}#CST_MICROWAVE_STUDIO_", include_icons=True)

    assert [i.sources for i in figures.images] == [
        ["Online Help/mergedProjects/3D/common_preloadedmacro/which_solver.png"]
    ]
    assert figures.left_out == []
    assert len(with_icons.images) == 4
    assert with_icons.images[0].kind == "icon"
    assert with_icons.images[0].caption == "solver transient icon"
    assert "which_solver.png" in with_icons.left_out[-1].sources[0]


def test_the_markdown_shows_figures_and_icons_and_leaves_out_logos(prose_build: ProseBuild) -> None:
    md = (prose_build.tree / WHICH_SOLVER).read_text(encoding="utf-8")
    [chart] = [a for a in _assets(prose_build) if a["sources"][0].endswith("/which_solver.png")]

    assert f"\n![]({chart['file']})\n" in md
    assert re.search(r"\*\*Time Domain Solver !\[solver transient icon\]\(assets/[0-9a-f]{12}\.png\)\*\*", md)
    assert (prose_build.tree / chart["file"]).is_file()
    assert chart["documents"] == [WHICH_SOLVER]
    assert not any("ds_simulia" in s or "3ds.png" in s for a in _assets(prose_build) for s in a["sources"])


def test_equation_images_are_marked_as_not_transcribed(
    prose_build: ProseBuild, prose_kb: KnowledgeBase
) -> None:
    md = (prose_build.tree / UNITS).read_text(encoding="utf-8")
    result = prose_kb.images(f"{UNITS}#Logarithmic_Units")

    assert re.search(r"\n!\[equation image, not transcribed\]\(assets/\w+\.png\)\n", md)
    assert [i.kind for i in result.images] == ["equation", "equation"]
    assert "equation image, not transcribed" in str(result.images[0])


def test_bmp_images_become_png_assets(prose_build: ProseBuild) -> None:
    [bmp] = [a for a in _assets(prose_build) if a["sources"][0].endswith("/pcb_import_view_etch.bmp")]

    assert bmp["file"].endswith(".png")
    assert (bmp["kind"], bmp["width"], bmp["height"]) == ("icon", 13, 14)
    with Image.open(prose_build.tree / bmp["file"]) as image:
        assert (image.format, image.size) == ("PNG", (13, 14))


def test_assets_are_deduplicated_by_content_and_counted_in_the_report(prose_build: ProseBuild) -> None:
    assets = _assets(prose_build)
    counts = prose_build.report["counts"]

    assert counts["assets"] == len(assets) > 1_000
    assert len({a["id"] for a in assets}) == len(assets)
    # Ribbon screenshots published in several projects are one Asset each.
    assert any(len({s.split("/")[1] for s in a["sources"]}) > 1 for a in assets)
    assert counts["missing_assets"] == len(prose_build.report["missing_assets"])


def test_svg_and_oversized_images_are_served_as_png_within_the_client_limit(tmp_path: Path) -> None:
    big = io.BytesIO()
    Image.new("RGB", (3_200, 800), "white").save(big, "PNG")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="60"><rect width="120" height="60"/></svg>'
    figures = (
        '<img src="theory/curve.svg" alt="Return loss curve" /> <img src="big.png" />'
        ' <img src="gone.png" alt="A lost figure" />'
    )
    release = write_release(
        tmp_path / "release",
        {
            "widgets/widget.htm": topic("Widget", "Spin", f"Spins it.</p><p>{figures}"),
            "widgets/theory/curve.svg": svg,
            "widgets/big.png": big.getvalue(),
        },
    )
    result = build_collection(
        write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, []), "cst-2024"
    )

    with KnowledgeBase.open(tmp_path / "kb") as kb:
        images = kb.images("vba_3d/widgets/widget.htm.md#spin").images
        md = (kb.path / "cst-2024" / "vba_3d/widgets/widget.htm.md").read_text(encoding="utf-8")

    curve, scaled = images
    assert (curve.caption, curve.mime_type, curve.width, curve.height) == (
        "Return loss curve",
        "image/png",
        120,
        60,
    )
    assert (scaled.width, scaled.height) == (1_568, 392)
    with Image.open(scaled.path) as image:
        assert image.size == (1_568, 392)
    assert "A lost figure" in md
    assert [m.href for m in result.report.missing_assets] == [
        "Online Help/mergedProjects/VBA_3D/widgets/gone.png"
    ]


def test_an_icon_inside_a_link_with_text_is_kept_and_a_small_formula_is_an_equation(tmp_path: Path) -> None:
    icon = io.BytesIO()
    Image.new("RGB", (16, 16), "red").save(icon, "PNG")
    symbol = io.BytesIO()
    Image.new("RGB", (24, 12), "blue").save(symbol, "PNG")
    text = (
        'Click <a href="https://example.com/spin">Spin <img src="spin_16.png" /></a> to spin it'
        ' at <img src="formel_rate.png" /> turns.'
    )
    release = write_release(
        tmp_path / "release",
        {
            "widgets/widget.htm": topic("Widget", "Spin", text),
            "widgets/spin_16.png": icon.getvalue(),
            "widgets/formel_rate.png": symbol.getvalue(),
        },
    )
    build_collection(write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, []), "cst-2024")

    with KnowledgeBase.open(tmp_path / "kb") as kb:
        page = kb.read("vba_3d/widgets/widget.htm.md#spin")

    # An inline symbol named like a formula is an equation image, however small.
    assert [(i.kind, i.caption) for i in page.images] == [("icon", "spin icon"), ("equation", "")]
    assert "[Spin](https://example.com/spin) ![spin icon](assets/" in page.text
    assert " at ![equation image, not transcribed](assets/" in page.text


def test_an_unknown_asset_id_is_a_clear_error(kb: KnowledgeBase) -> None:
    with pytest.raises(KnowledgeBaseError, match=r"No Asset '0123456789ab' in Release 2024"):
        kb.images(assets=["0123456789ab"])
    with pytest.raises(KnowledgeBaseError, match=r"Name a Locator, or the Asset ids"):
        kb.images()


def _assets(build: ProseBuild) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = json.loads((build.tree / "assets" / "assets.json").read_text("utf-8"))
    return assets
