# 26: Markdown that ordinary readers render correctly

**What to build:** The Markdown tree reads correctly in ordinary Markdown viewers and editors (VS Code, GitHub, Obsidian), not only for agents. Links work when followed from the file they are in, and source text is never mistaken for markup.

**Blocked by:** 29

**Status:** done

- [x] Links between Documents are written relative to the linking file (`../common_general/common_general_name.htm.md#rules`) instead of as Collection-relative Locators. `validate` still resolves every link and reports its status.
- [x] The entry files (`toc.md`, `keywords.md`, `api.md`, `library.md`, `materials.md`) and the Guides follow the same rule.
- [x] Source text that Markdown would read as HTML or emphasis is escaped outside code blocks, for example `<Curve item name>` in `3d/common_struct/common_struct_changecurve.htm.md`. TeX that MathJax renders (ticket 10) is left intact.
- [x] Rendered against a real Markdown renderer (CommonMark plus GitHub tables), a sample of corpus topics loses no text and every internal link resolves to an existing file.
- [x] The spec's "rewritten as Locators" wording and ticket 04's decision note are updated.

## Comments

**2026-10-26.** Implemented.

- **Links.** `render_markdown(doc, at)` writes every link and image relative to the file it is written in; a copy (the Python menu topics in `python/`) gets its own relative links. `validate` resolves each link from the page that holds it, and reports one that climbs out of the view as missing. The entry files sit at the Collection root, where Collection-relative and file-relative paths are the same, so their output is unchanged.
- **Guides.** Ticket 24 has not built Guides yet. The generated `AGENTS.md` tells agents that a Guide links to the pages it cites relative to itself, starting with `../`, and `validate` checks `guides/` like any page (`test_a_guide_links_relative_to_itself`).
- **Escaping** happens in the renderer, outside link, image, math and code spans and the readers' own `\$` and `\<`: a backslash before punctuation, `*`, `` ` ``, `~`, `<` before a letter, an entity, and `]` before `(` or `[`. Underscores and dollars are escaped only in a line that holds a pair a viewer would read as emphasis or math (`__init__`; `[App$](…) using [Topic$](…)` on WinWrap pages), so `_cst_eda_interface` and a lone `Dir$` still grep as written. This changes ticket 10's rule for pages without MathJax: their dollars were left raw, and pairs of them are now escaped (`test_a_dollar_on_a_page_without_mathjax_is_text`). Labels in `toc.md`, `keywords.md`, `api.md`, `library.md` and `materials.md` are escaped the same way.
- **Render check.** `tests/test_markdown_render.py` parses the built pages with markdown-it-py (CommonMark, tables, frontmatter, dollar math as GitHub reads it) and fails on source text read as HTML, emphasis, misplaced bold or math holding a link, and on links that lead to no file. It runs over the prose, Python, WinWrap, manual, Library and remaining-Areas builds; WinWrap pages, which load no MathJax, must hold no math at all. It checks markup, not a text-for-text comparison with the source.
- **Verification.** A fresh build of the whole corpus (4,246 Documents) into a scratch Knowledge Base: `validate` clean, and the render check over all 2,932 Markdown pages reports 0 problems. 177 tests pass.
- The development `.kb` was re-assembled once the folder that Windows held open was closed (Build 20261026T141824192757Z-04d9, 4,246 Documents); `validate` reports it valid.
