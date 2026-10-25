# 13: Two Word manuals

**What to build:** The two Word manuals, "High Frequency Simulation" and "Getting Started", join the tree as files in Area `manuals`: the PDF itself, copied as it is, and beside it a `<name>.pdf.md` with the text of every page under a `page-<n>` anchor, extracted with pypdf. Agents grep the text and open the PDF by page with their Read tool when layout or a figure matters.

**Blocked by:** 29

**Status:** done

- [x] Each manual is copied unchanged and gets a text companion with frontmatter (title, source, page count) and one `## page-<n>` section per page.
- [x] A PDF without a text layer is a reported failure.
- [x] `AGENTS.md` names the `manuals/` folder and says to grep the companion and read the PDF page.
- [x] PDF-01 and PDF-02 reach their pages in the agent run.

## Comments

**2026-10-25.** Shrunk for ADR 0014. Docling, the conversion cache, heading-tagged Sections and on-demand page rendering are gone: Claude Code and Codex read PDF pages from disk, and pypdf text is enough to find the page.

**2026-10-25.** Implemented in `ae14ac4`: a reader of its own, `pdf.py`. Each manual is copied byte for byte to `manuals/<name>.pdf`; its Text Companion `manuals/<name>.pdf.md` is the Document's Locator (spec and GLOSSARY amended), with `pages:` in the frontmatter and, per physical page, `<a id="page-<n>"></a>` and `## page-<n>` above one paragraph per text line. The help's links from `general/printed_documentation.htm` to these two PDFs now resolve to the companions; its six other PDF links stay outside links. A PDF none of whose pages has text fails with "no text layer"; a partly scanned PDF passes with empty pages, which no manual in scope has. Covered by `tests/test_manuals.py` and the page-rule cases in `tests/test_agent_run.py` (136 tests pass).

Agent run from a fresh build of the development `.kb` (1,840 Documents, `validate` clean, `AGENTS.md` 7.8 KB), Claude Code with `--model sonnet`, Read/Grep/Glob only, `scripts/agent-run.py --only PDF-01,PDF-02`: both first expected read at call 3 (of 6 and 4), median 3, PASS. Both reads were of the companion at the given page. In the first run, before the recipe's step 5, PDF-01 hit only through the online-help waveguide overview at call 6 and never opened the manual; PDF-02 read the companion page and then the PDF with `pages: "12"`.

Decisions for later tickets:

- **Page rule in the agent run.** A companion read hits when its lines overlap the page's text below its heading; a PDF read when its `pages` include the page, or when it has none and succeeded. A call whose tool result is an error reaches nothing, so a refused read of a long PDF or companion never scores.
- **Text as extracted.** Whitespace runs collapse, `$` and a tag-like `<` are escaped, the running header and footer stay. pypdf splits some words ("a cceleration") and Word's symbol-font arrows come out as private-use characters (U+F0F0), so a grep for a ribbon path with `>` won't match a manual; mapping them is for ticket 21 if it matters.
- **Which manuals.** `build._MANUALS` lists the two; ticket 21 adds the rest and the release notes.
