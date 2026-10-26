"""Build the WinWrap Basic Area from the real corpus, then read the files it wrote (the build-then-read seam)."""

from __future__ import annotations

import json
from pathlib import Path

from cst_help_mcp.validate import validate

DIR = "sax_basic/ww_00069.htm.md"


def _md(kb: Path, locator: str) -> str:
    return (kb / "cst-2024" / locator).read_text(encoding="utf-8")


def test_a_language_page_has_its_syntax_group_and_description_as_blocks(winwrap_kb: Path) -> None:
    md = _md(winwrap_kb, DIR)

    assert '\narea: "winwrap-basic"\n' in md
    assert (
        '<a id="dir"></a>\n# Dir$ Function\n\n```vba\nDir[$]([Pattern$][, AttribMask])\n```\n\n'
        "**Group**\n: [File](ww_00309.htm.md)\n\n"
        "Scan a directory for the first file matching [Pattern$](ww_00288.htm.md).\n"
    ) in md


def test_lines_that_the_import_turned_into_lists_get_back_their_first_character(winwrap_kb: Path) -> None:
    msgbox = _md(winwrap_kb, "sax_basic/ww_00166.htm.md")
    # Word took the "v" of each constant for a bullet, and a leading number for a numbered list's start.
    assert "\nvbOK 1 OK button\n" in msgbox
    assert "\nvbAbortRetryIgnore 2 Abort, Retry, Ignore buttons\n" in msgbox
    assert "bOK" not in msgbox.replace("vbOK", "")
    assert "\n1 Dialog box initialization." in _md(winwrap_kb, "sax_basic/ww_00067.htm.md")
    assert "\nq Quarter\n" in _md(winwrap_kb, "sax_basic/ww_00050.htm.md")


def test_every_language_reference_page_becomes_a_document(winwrap_kb: Path) -> None:
    pages = list((winwrap_kb / "cst-2024" / "sax_basic").glob("ww_*.htm.md"))
    report = json.loads(next((winwrap_kb / "builds" / "cst-2024").glob("*/report.json")).read_text("utf-8"))

    assert len(pages) == 315
    assert report["counts"]["failed"] == 0
    assert report["counts"]["unresolved_links"] == 0


def test_an_example_whose_keywords_are_links_renders_as_code_with_its_line_breaks(winwrap_kb: Path) -> None:
    # In the source, each <br /> sits inside the link of the keyword that starts the next line.
    assert (
        '<a id="example"></a>\n## Example\n\n```vba\nSub Main\nF$ = Dir$("*.*")\nWhile F$ <> ""\n'
        "Debug.Print F$\nF$ = Dir$()\nWend\nEnd Sub\n```"
    ) in _md(winwrap_kb, DIR)


def test_keywords_and_built_ins_are_listed_in_api_md_under_their_names_as_written(winwrap_kb: Path) -> None:
    api = (winwrap_kb / "cst-2024" / "api.md").read_text(encoding="utf-8")

    assert "| Left$ | winwrap-basic | `Left[$](S$, Len)` | `sax_basic/ww_00145.htm.md#left` |" in api
    assert (
        "| Dir$ | winwrap-basic | `Dir[$]([Pattern$][, AttribMask])` | `sax_basic/ww_00069.htm.md#dir` |"
        in api
    )
    assert "| Print | winwrap-basic | `Print #StreamNum, [expr[; ...][;]]` |" in api
    assert "| Begin Dialog | winwrap-basic | `Begin Dialog UserDialog " in api
    assert "| Line Input | winwrap-basic |" in api
    assert "| CheckBox | winwrap-basic |" in api
    # The name comes from the heading; this page's <title> misspells its kind ("Definintion").
    assert "| Attribute | winwrap-basic |" in api
    # Group pages and the definitions of syntax terms document no keyword.
    assert "File Group" not in api
    assert "| str | winwrap-basic" not in api


def test_agents_md_says_where_the_language_reference_is(winwrap_kb: Path) -> None:
    agents = (winwrap_kb / "cst-2024" / "AGENTS.md").read_text(encoding="utf-8")

    assert "| `sax_basic/` | 315 | WinWrap Basic language reference" in agents
    assert "`sax_basic/`" in agents.split("## Page anatomy")[1]


def test_signatures_that_look_like_links_leave_the_knowledge_base_valid(winwrap_kb: Path) -> None:
    # `Left[$](S$, Len)` in api.md is code, not a link to "S$, Len".
    assert validate(winwrap_kb).problems == []


def test_a_line_that_starts_with_a_list_marker_stays_a_paragraph(winwrap_kb: Path) -> None:
    # The unary minus of the operator table, not a bullet.
    assert "\n\\- [n1](ww_00278.htm.md) Negate" in _md(winwrap_kb, "sax_basic/ww_00179.htm.md")
