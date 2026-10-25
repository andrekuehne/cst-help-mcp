"""TeX on the MathJax pages: built from synthetic topics and from the real corpus, then read from the pages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kb_helpers import ProseBuild, write_config, write_release

from cst_help_mcp.build import build_collection

# The configuration that 150 of CST's 172 RoboHelp MathJax pages carry.
MATHJAX = """<script type="text/javascript">
MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']]
  },
  svg: {
    fontCache: 'global'
  }
};
</script>
<script type="text/javascript" id="MathJax-script" async="" src="../mathjax/es5/tex-svg.js"></script>"""


LOSS_AND_Q = "3d/special_overview/special_overview_loss_and_q_calculation_overview.htm.md"
FARFIELD = "3d/special_postpr/special_postpr_pp_farfield.htm.md"


def test_the_loss_and_q_formulas_of_theo_01_are_math_with_their_tex_as_written(
    prose_build: ProseBuild,
) -> None:
    md = (prose_build.tree / LOSS_AND_Q).read_text(encoding="utf-8")

    assert (
        "\n**Volume losses**\n: The volume loss power is calculated based on the normal material properties"
        " like the loss angle tangent delta or the corresponding conductivity and the field distribution"
        " in the corresponding shape volume:\n\n$$\n\\begin{equation} P_D = \\pi f \\, \\tan(\\delta) \\,"
        " \\epsilon_0 \\epsilon_r \\, \\int{|\\vec{E}|^2 dV} \\end{equation}\n$$\n"
    ) in md
    assert " by the specified conductivity $\\sigma$, the permeability value" in md
    assert (
        "\n$$\n\\begin{equation} P_W = \\frac{1}{2} \\sqrt{\\frac{\\pi \\mu f}{\\sigma}} \\,"
        " \\int{|\\vec{H}_{\\mathrm{tan}}|^2 dS} \\end{equation}\n$$\n"
    ) in md


def test_the_ludwig_2_angles_of_theo_02_are_math_with_their_entities_decoded(prose_build: ProseBuild) -> None:
    md = (prose_build.tree / FARFIELD).read_text(encoding="utf-8")

    assert (
        "In the Ludwig 2 AE coordinate system, instead of $\\vartheta$ and $\\varphi$, the two angles" in md
    )
    assert (
        "\n$$\n\\begin{align} \\mathrm{Elevation} & = \\arcsin \\left( \\frac{y}{r} \\right) \\\\"
        " \\mathrm{Azimuth} & = \\arctan \\left( \\frac{x}{z} \\right) \\end{align}\n$$\n"
    ) in md


def test_a_field_name_holds_math_too(prose_build: ProseBuild) -> None:
    md = (prose_build.tree / "3d/special_solvopt/special_solvopt_t3solverspecsteady.htm.md").read_text(
        "utf-8"
    )

    # A Tip-Note-Heading paragraph, read as a field name.
    assert "\n**In the delta value formula the infinity norm $|| \\textbf{v}^{n}||_\\infty$ is used," in md


def test_no_corpus_page_has_a_dollar_without_its_partner(prose_build: ProseBuild) -> None:
    # With each page's own configuration and MathJax's runs of text, CST's TeX pairs up everywhere.
    assert prose_build.report["unpaired_math"] == []


def _page(body: str, head: str = MATHJAX) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html><head><title>Losses</title>
<script type="text/javascript" src="../whtopic.js"></script>
{head}</head>
<body>
<h1>Losses</h1>
{body}
</body></html>
"""


def _build(tmp_path: Path, body: str, head: str = MATHJAX) -> str:
    return _build_with_report(tmp_path, body, head)[0]


def _build_with_report(tmp_path: Path, body: str, head: str = MATHJAX) -> tuple[str, dict[str, Any]]:
    release = write_release(tmp_path / "release", {"theory/losses.htm": _page(body, head)})
    result = build_collection(
        write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, []), "cst-2024"
    )
    md = (tmp_path / "kb" / "cst-2024" / "vba_3d/theory/losses.htm.md").read_text(encoding="utf-8")
    return md, json.loads(result.report_path.read_text(encoding="utf-8"))


def test_inline_math_is_markdown_math_with_its_tex_as_written(tmp_path: Path) -> None:
    md = _build(tmp_path, r"<p>The conductivity $\sigma_{\mathrm{w}}$ and the frequency \(f_*\) matter.</p>")

    assert r"The conductivity $\sigma_{\mathrm{w}}$ and the frequency $f_*$ matter." in md


def test_a_dollar_on_a_page_without_mathjax_is_text(tmp_path: Path) -> None:
    md = _build(tmp_path, "<p>Left$(s, 1) and Right$(s, 2) return $x$ parts.</p>", head="")

    assert "\n\nLeft$(s, 1) and Right$(s, 2) return $x$ parts.\n" in md


def test_each_page_honours_its_own_delimiters_and_the_classes_it_processes(tmp_path: Path) -> None:
    # The plane wave overview's configuration: only "mathjax..." elements hold math, and \( is no delimiter.
    head = MATHJAX.replace(
        "inlineMath: [['$', '$'], ['\\\\(', '\\\\)']]",
        "inlineMath: [['$', '$']] }, options: { ignoreHtmlClass: '.*', processHtmlClass: 'mathjax.*'",
    )
    md = _build(
        tmp_path,
        r"<p>Files are named $$MONITOR_NAME$$_$$EXCITATION_NAME$$.</p>"
        r'<p class="Tip-Note-Text mathjax_process">Sources $i$ and \(j\), and $$Z$$.</p>',
        head,
    )

    # A dollar outside math is escaped, so that a Markdown renderer does not pair it either.
    assert r"Files are named \$\$MONITOR_NAME\$\$_\$\$EXCITATION_NAME\$\$." in md
    assert "\n\nSources $i$ and \\(j\\), and\n\n$$\nZ\n$$\n\n.\n" in md


def test_an_escaped_dollar_opens_no_math(tmp_path: Path) -> None:
    md, report = _build_with_report(tmp_path, r"<p>A licence costs \$5 per $n$ seats.</p>")

    assert r"A licence costs \$5 per $n$ seats." in md
    assert report["unpaired_math"] == []


def test_a_dollar_without_its_partner_is_reported_and_stays_text(tmp_path: Path) -> None:
    # MathJax looks for math in each run of text between tags, so a pair across paragraphs is no pair.
    md, report = _build_with_report(
        tmp_path, "<p>The impedance $Z = \\sqrt{L/C}</p><p>holds, and $f$ is the frequency.$</p>"
    )

    assert "\n\nThe impedance \\$Z = \\sqrt{L/C}\n\nholds, and $f$ is the frequency.\\$\n" in md
    source = "Online Help/mergedProjects/VBA_3D/theory/losses.htm"
    assert report["unpaired_math"] == [
        {"source": source, "delimiter": "$", "context": "The impedance $Z = \\sqrt{L/C}"},
        {"source": source, "delimiter": "$", "context": "holds, and $f$ is the frequency.$"},
    ]
    assert report["counts"]["unpaired_math"] == 2


def test_display_math_and_environments_are_math_blocks_with_their_entities_decoded(tmp_path: Path) -> None:
    md = _build(
        tmp_path,
        r"<p>The loss power: \begin{align} P &amp;= P_W + P_D \\ Q &amp;&lt; \infty \end{align} and"
        r" $$a&gt;b$$ or \[c\] hold.</p>",
    )

    assert (
        "\n\nThe loss power:\n\n"
        "$$\n\\begin{align} P &= P_W + P_D \\\\ Q &< \\infty \\end{align}\n$$\n\n"
        "and\n\n$$\na>b\n$$\n\nor\n\n$$\nc\n$$\n\nhold.\n"
    ) in md
