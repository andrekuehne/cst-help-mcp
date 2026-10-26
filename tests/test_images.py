"""Images as Assets: built from the real corpus, then read from the pages and the Build's list of Assets."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

from kb_helpers import ProseBuild, topic, write_config, write_release
from PIL import Image

from cst_help_mcp.build import build_collection

WAVEGUIDE = "3d/special_overview/special_overview_waveguideover.htm.md"
WHICH_SOLVER = "3d/special_overview/special_overview_whichsolver.htm.md"
UNITS = "userinterface/overview/units.htm.md"


def test_a_figure_is_a_png_asset_that_its_section_shows(prose_build: ProseBuild) -> None:
    [dims] = [a for a in _assets(prose_build) if a["sources"][0].endswith("/microstrip_dims_kh.png")]
    md = (prose_build.tree / WAVEGUIDE).read_text(encoding="utf-8")

    assert dims["kind"] == "figure"
    assert (dims["width"], dims["height"]) == (294, 150)
    assert dims["documents"] == [WAVEGUIDE]
    section = md.partition('<a id="Port_Modes_Microstrips"></a>')[2].partition("<a id=")[0]
    assert f"](../../{dims['file']})" in section
    with Image.open(prose_build.tree / dims["file"]) as image:
        assert (image.format, image.size) == ("PNG", (294, 150))


def test_the_markdown_shows_figures_and_icons_and_leaves_out_logos(prose_build: ProseBuild) -> None:
    md = (prose_build.tree / WHICH_SOLVER).read_text(encoding="utf-8")
    [chart] = [a for a in _assets(prose_build) if a["sources"][0].endswith("/which_solver.png")]

    assert f"\n![](../../{chart['file']})\n" in md
    assert re.search(
        r"\*\*Time Domain Solver !\[solver transient icon\]\(\.\./\.\./assets/[0-9a-f]{12}\.png\)\*\*", md
    )
    assert (prose_build.tree / chart["file"]).is_file()
    assert chart["documents"] == [WHICH_SOLVER]
    assert not any("ds_simulia" in s or "3ds.png" in s for a in _assets(prose_build) for s in a["sources"])


def test_equation_images_are_marked_as_not_transcribed(prose_build: ProseBuild) -> None:
    md = (prose_build.tree / UNITS).read_text(encoding="utf-8")
    files = re.findall(r"\n!\[equation image, not transcribed\]\(\.\./\.\./(assets/\w+\.png)\)\n", md)

    assert files
    assert {a["kind"] for a in _assets(prose_build) if a["file"] in files} == {"equation"}


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


def test_svg_and_oversized_images_become_png_with_a_copy_within_the_client_limit(tmp_path: Path) -> None:
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

    view = tmp_path / "kb" / "cst-2024"
    md = (view / "vba_3d/widgets/widget.htm.md").read_text(encoding="utf-8")
    curve, scaled = json.loads((result.report_path.parent / "assets.json").read_text("utf-8"))
    assert (curve["caption"], curve["width"], curve["height"]) == ("Return loss curve", 120, 60)
    assert f"![Return loss curve](../../{curve['file']})" in md
    with Image.open(view / curve["file"]) as image:
        assert image.format == "PNG"
    assert (scaled["served_width"], scaled["served_height"]) == (1_568, 392)
    with Image.open(view / scaled["served"]) as image:
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

    md = (tmp_path / "kb" / "cst-2024" / "vba_3d/widgets/widget.htm.md").read_text(encoding="utf-8")
    assert "[Spin](https://example.com/spin) ![spin icon](../../assets/" in md
    # An inline symbol named like a formula is an equation image, however small.
    assert " at ![equation image, not transcribed](../../assets/" in md


def _assets(build: ProseBuild) -> list[dict[str, Any]]:
    """The Build's list of its Assets, which lies beside its tree, not in it."""
    [folder] = (build.kb / "builds" / "cst-2024").iterdir()
    assert not (build.tree / "assets" / "assets.json").exists()
    assets: list[dict[str, Any]] = json.loads((folder / "assets.json").read_text("utf-8"))
    return assets
