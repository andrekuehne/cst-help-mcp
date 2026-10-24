# 26: Markdown that ordinary readers render correctly

**What to build:** The Markdown tree reads correctly in ordinary Markdown viewers and editors (VS Code, GitHub, Obsidian), not only for agents. Links work when followed from the file they are in, and source text is never mistaken for markup.

**Blocked by:** 16

**Status:** ready-for-agent

- [ ] Links between Documents are written relative to the linking file (`../common_general/common_general_name.htm.md#rules`) instead of as Collection-relative Locators. The persisted model keeps each link's Locator, and `cst_help_read` still reports every outgoing link with its Locator and status (ticket 08).
- [ ] The entry files (`toc.md`, `keywords.md`, `api-index.md` and the rest) and the Guides follow the same rule.
- [ ] Source text that Markdown would read as HTML or emphasis is escaped outside code blocks, for example `<Curve item name>` in `3d/common_struct/common_struct_changecurve.htm.md`. TeX that MathJax renders (ticket 10) is left intact.
- [ ] Rendered against a real Markdown renderer (CommonMark plus GitHub tables), a sample of corpus topics loses no text and every internal link resolves to an existing file.
- [ ] The spec's "rewritten as Locators" wording and ticket 04's decision note are updated.
