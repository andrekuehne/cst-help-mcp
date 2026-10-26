"""Build the Word manuals from the real corpus, then read the files it wrote (the build-then-read seam)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from kb_helpers import ProseBuild, topic, write_config, write_release
from pypdf import PdfWriter

from cst_help_mcp.build import build_collection

GETTING_STARTED = "CST Studio Suite - Getting Started.pdf"
HIGH_FREQUENCY = "CST Studio Suite - High Frequency Simulation.pdf"


def _md(build: ProseBuild, locator: str) -> str:
    return (build.tree / locator).read_text(encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_a_manual_is_copied_unchanged_into_manuals(manuals_build: ProseBuild, corpus_2024: Path) -> None:
    for name in (GETTING_STARTED, HIGH_FREQUENCY):
        assert _sha(manuals_build.tree / "manuals" / name) == _sha(corpus_2024 / "Documentation" / name)


def test_a_manuals_text_companion_has_a_section_per_page(manuals_build: ProseBuild) -> None:
    md = _md(manuals_build, f"manuals/{GETTING_STARTED}.md")

    assert md.startswith(
        '---\nrelease: "2024"\narea: "manuals"\ntitle: "CST Studio Suite - Getting Started"\n'
        f'source: "Documentation/{GETTING_STARTED}"\npages: 72\n---\n\n'
        '<a id="page-1"></a>\n## page-1\n\nCST Studio Suite 2024\n\nGetting Started\n'
    )
    assert md.count("\n## page-") == 72
    page_12 = md.partition('<a id="page-12"></a>\n## page-12\n')[2].partition("\n## page-13")[0]
    assert (
        "For an automated and silent installation with default settings use the following command:" in page_12
    )
    assert 'start /wait setup.exe /s /v"/l\\*v C:\\InstallCST.log REBOOT=REALLYSUPPRESS /qn' in page_12
    assert "\n## page-119\n" in _md(manuals_build, f"manuals/{HIGH_FREQUENCY}.md")


def test_symbol_font_arrows_and_bullets_become_text(manuals_build: ProseBuild) -> None:
    md = _md(manuals_build, f"manuals/{HIGH_FREQUENCY}.md")

    # Word's symbol-font arrow in a Ribbon Path reads as the help writes it.
    assert "Post-Processing: Tools > Result Templates" in md
    assert "\n• Radar Cross Section (RCS) calculation" in md
    assert not {chr(0xF0F0), chr(0xF06F), chr(0xF0A7), chr(0xF0B7)} & set(md)  # the private-use code points


def test_the_helps_links_to_a_manual_lead_to_its_text_companion(manuals_build: ProseBuild) -> None:
    md = _md(manuals_build, "general/printed_documentation.htm.md")

    assert f"[CST Studio Suite - Getting Started](<../manuals/{GETTING_STARTED}.md>)" in md
    # The manuals this build leaves out stay outside links, rendered as their labels.
    assert "Low Frequency Simulation.pdf" not in md
    assert manuals_build.report["outside_links"][".pdf"] == 6


def test_a_manual_without_a_text_layer_is_a_reported_failure(tmp_path: Path) -> None:
    release = write_release(tmp_path / "release", {"solver.htm": topic("Solver", "Start", "Starts it.")})
    scanned = PdfWriter()
    scanned.add_blank_page(width=595, height=842)
    (release / "Documentation").mkdir()
    scanned.write(release / "Documentation" / GETTING_STARTED)
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, [])

    result = build_collection(config, "cst-2024")

    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert not report["complete"]
    assert report["failures"] == [
        {
            "source": f"Documentation/{GETTING_STARTED}",
            "error": "ValueError: the PDF has no text layer, and it is not read by OCR",
        }
    ]
    assert not (tmp_path / "kb" / "cst-2024" / "manuals").exists()


def test_agents_md_names_the_manuals_and_says_to_grep_the_text_and_read_the_pdf_page(
    manuals_build: ProseBuild,
) -> None:
    agents = _md(manuals_build, "AGENTS.md")

    assert "| `manuals/` | 2 | Word manuals" in agents
    recipe = agents.partition("**A manual**")[2].partition("\n\n")[0]
    assert "`.pdf.md`" in recipe
    assert "`## page-<n>`" in recipe
    assert "open the PDF" in recipe
