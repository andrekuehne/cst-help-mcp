"""The Markdown tree reads correctly in ordinary Markdown viewers (ticket 26): rendered by a CommonMark
renderer with GitHub tables, no source text turns into HTML or emphasis, and every link between the
files leads to a file that exists, followed from the file that holds it."""

from __future__ import annotations

import posixpath
import re
from pathlib import Path
from urllib.parse import unquote

import pytest
from kb_helpers import ProseBuild
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from cst_help_mcp.layout import AGENTS_FILE, CLAUDE_FILE, WORK_DIR

# Frontmatter is metadata and TeX between dollars is math, as GitHub, VS Code and Obsidian read them;
# the TeX is left as written (ticket 10), and display math may sit inside a line.
_RENDERER = (
    MarkdownIt("commonmark")
    .enable("table")
    .use(front_matter_plugin)
    .use(dollarmath_plugin, double_inline=True)
)
# The HTML the renderer writes itself: a Section's anchors, and tables with merged cells.
_ANCHOR_TAG = re.compile(r'<a id="[^"]*">|</a>')
_SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:", re.IGNORECASE)


def _problems(view: Path, page: Path, math: bool = True) -> list[str]:
    """What an ordinary reader gets wrong on a page: source text taken for HTML, emphasis or math,
    and links that lead nowhere. Without ``math``, the page holds no formulas, so any is source
    text."""
    rel = page.relative_to(view).as_posix()
    problems = []
    for token in _RENDERER.parse(page.read_text(encoding="utf-8")):
        table = token.content.startswith("<table>")
        if token.type == "html_block" and not table and _ANCHOR_TAG.sub("", token.content).strip():
            problems.append(f"{rel}: HTML block {token.content[:60]!r}")
        children = [c for c in token.children or [] if c.type != "text" or c.content]
        for i, child in enumerate(children):
            found = _inline_problems(view, rel, child, i, math)
            problems.extend(f"{rel}: {p} in {token.content[:80]!r}" for p in found)
    return problems


def _inline_problems(view: Path, rel: str, token: Token, position: int, math: bool) -> list[str]:
    if token.type == "html_inline" and not _ANCHOR_TAG.fullmatch(token.content):
        return [f"HTML {token.content!r}"]
    # Dollars in text that pair up swallow what lies between them, links too.
    if token.type.startswith("math") and (not math or "](" in token.content):
        return [f"math {token.content!r}"]
    if token.type == "em_open":
        return ["emphasis"]
    # Bold is the renderer's own only at the start of a line: a field's term, a note, a title.
    if token.type == "strong_open" and position != 0:
        return ["bold"]
    target = token.attrGet("href") if token.type == "link_open" else token.attrGet("src")
    if not isinstance(target, str) or _SCHEME.match(target) or target.startswith("#"):
        return []
    path = posixpath.normpath(posixpath.join(posixpath.dirname(rel), unquote(target.partition("#")[0])))
    if path.startswith("../") or not (view / path).is_file():
        return [f"link to {target}, which leads nowhere"]
    return []


def _pages(view: Path) -> list[Path]:
    # AGENTS.md and CLAUDE.md are the tool's own text, not the vendor's.
    written = {WORK_DIR, AGENTS_FILE, CLAUDE_FILE}
    return sorted(p for p in view.rglob("*.md") if p.relative_to(view).parts[0] not in written)


def _assert_renders(view: Path, math: bool = True) -> None:
    pages = _pages(view)
    assert pages
    problems = [p for page in pages for p in _problems(view, page, math)]
    assert not problems, f"{len(problems)} problems, such as:\n" + "\n".join(problems[:20])


def test_prose_pages_render_without_lost_text_or_broken_links(prose_build: ProseBuild) -> None:
    _assert_renders(prose_build.tree)


def test_python_pages_render_without_lost_text_or_broken_links(python_build: ProseBuild) -> None:
    _assert_renders(python_build.tree)


def test_winwrap_pages_render_without_lost_text_or_broken_links(winwrap_kb: Path) -> None:
    # No WinWrap page loads MathJax, and its names end in dollars: Left$, Mid$.
    _assert_renders(winwrap_kb / "cst-2024", math=False)


def test_manual_pages_render_without_lost_text_or_broken_links(manuals_build: ProseBuild) -> None:
    _assert_renders(manuals_build.tree)


def test_library_pages_render_without_lost_text_or_broken_links(library_build: ProseBuild) -> None:
    _assert_renders(library_build.tree)


def test_remaining_pages_render_without_lost_text_or_broken_links(remaining_build: ProseBuild) -> None:
    _assert_renders(remaining_build.tree)


@pytest.mark.parametrize("name", ["toc.md", "keywords.md", "api.md"])
def test_entry_files_link_relative_to_themselves(prose_build: ProseBuild, name: str) -> None:
    view = prose_build.tree
    assert not [p for p in _problems(view, view / name)]
