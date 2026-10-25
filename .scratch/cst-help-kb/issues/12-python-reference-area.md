# 12: Python reference Area

**What to build:** A Sphinx reader turns the Python reference into Area `python`. Its classes, methods, properties and functions become API Entries under their dotted names, taken from the Sphinx inventory and anchored to their entries.

**Blocked by:** 01

**Status:** done

- [x] Content comes from the Sphinx main region, without sidebars or navigation bars, and keeps headings, code blocks, admonitions and math.
- [x] Every inventory object becomes an API Entry with its signature and parameters, taken from its entry on the page.
- [x] Links from Sphinx pages into the RoboHelp help resolve to Locators.
- [x] The RoboHelp topics about Python (`mergedProjects/Python/python_overview.htm`, and the root `menu.htm` and `user_scipts.htm`, which ticket 04 reads into `general`) move to Area `python`. Their links into the Sphinx pages resolve.
- [x] API-08 and API-09 reach their pages in the agent run, and their entries are in `api.md`.

## Comments

**2026-10-25.** Implemented in `8987a12`: a reader of its own, `sphinx.py`. `objects.inv` lists the pages (its `std:doc` entries: `main.html` and the 7 `source/*.html`) and the objects; each page's `div.body` is read. All 725 objects of the roles `py:class`, `py:property`, `py:method` and `py:function` become API Entries on 714 entries: 11 entries carry two names, such as `cst.results.ProjectFile` and its hidden alias `_cst_results.ProjectFile` (priority -1), which share the entry's anchor. An inventory object with no entry on its page fails the page. Covered by `tests/test_python_reference.py` (121 tests pass in all).

Agent run from a fresh build of the development `.kb` (1,838 Documents, 6,510 API Entries, `validate` clean, `AGENTS.md` 6.9 KB), Claude Code with `--model sonnet`, Read/Grep/Glob only, `scripts/agent-run.py --only API-08,API-09`: API-08 first expected read at call 3 of 4, API-09 at call 5 of 7; median 4; PASS. In both runs the first call was not the read of `AGENTS.md`.

Decisions for later tickets:

- **Names as the inventory writes them.** The `cst.eda` geometry and PCB classes are listed as `_cst_eda_interface.geometry2d.Arc`, so that is their API Entry; a grep for `geometry2d.Arc` finds it. Their entry ids drop the leading underscore (`cst_eda_interface...`), and the anchor is the id.
- **Modules** (`py:module`) are no API Entries; they are the pages' Sections (`#module-cst.results`).
- **Entry layout.** Heading with the dotted name as code (so `__init__` isn't read as emphasis), a ```python signature block, the description, and field lists as fields: `**Parameters**` and a list of the parameters. The API Entry's description joins the entry's paragraphs, fields and lists, not its admonitions or code.
- **Model.** New block `admonition` (title in `term`, content in `blocks`), rendered as a quote; lists have a nesting `level`, rendered indented. RoboHelp's `note` stays as it is; the two could merge if another reader needs notes.
- **Text escapes.** On Sphinx pages every `$` is escaped (Sphinx marks all math) and a `<` that could open a tag (`\<CST_STUDIO_SUITE_FOLDER>`). `<cite>`, the default role, renders as code.
- **SVGs** sized in mm render at 96 dpi; resvg gave them no size before, so every Area's mm-sized SVGs were missing Assets.
- **Menu topics.** `menu.htm.md` and `user_scipts.htm.md` are Area `python` and keep their Locators at the top of the Release folder, as the Locator rule says. So that a grep confined to `python/` finds them, the build also writes them to `python/menu.htm.md` and `python/user_scipts.htm.md`, with `copy_of:` in the frontmatter naming the Locator to cite (a project's `copy_to`). Copies are no Documents: they count in no page total, and links and the agent run lead to the Locator.
- **Outside links.** The 3 that remain lead to Sphinx's generated `genindex`, `py-modindex` and `search` pages, which are no Documents.
- **Duplication.** `sphinx.py` repeats small helpers of `robohelp.py` (`_collapse`, `_span`, the table reading, the unique-anchor loop); a third reader is the time to share them.
