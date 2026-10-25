# 05: Navigation metadata and browse

**What to build:** The build reads RoboHelp's table of contents, author keyword index and context-help maps from the `gXMLBuffer` data files without running any JavaScript. Child project tables of contents are spliced into the root one. Documents carry their table-of-contents paths and author keywords in frontmatter, using the embedded breadcrumbs where the table of contents has none. Each Collection gets `toc.md` and `keywords.md`. The new `cst_help_browse` tool, with a matching CLI command, walks the table of contents and the keyword index.

**Blocked by:** 02, 04

**Status:** done

- [x] Every RoboHelp project's navigation data parses after decoding the JS string escapes. Paths with backslashes and mixed case are resolved without regard to case.
- [x] A Document listed in several places in the table of contents carries all of its paths.
- [x] Breadcrumbs from `addTocInfo` supply table-of-contents paths for topics that are in no table of contents.
- [x] `toc.md` and `keywords.md` are generated as nested links that resolve within the tree.
- [x] Browsing "3D Simulation > Solvers > High Frequency > Time Domain Solver" lists its pages, and browsing a keyword lists its target topics.

## Comments

**Implemented (2026-10-24).** `tests/test_navigation.py` checks the build, `KnowledgeBase.browse`, and with `test_mcp_server.py` and `test_cli.py` the MCP tool and the CLI command, all against the real corpus, except one small synthetic release. The full suite has 110 tests. The development `.kb` now has 689 table-of-contents entries and 1,698 keywords; 573 entries and 1,416 keyword topics lead outside the Build (DES, PCB, Filter Designer, CHI, VBA_DES, Python, FEST3D, Legal Notices) and are dropped.

Decisions for later tickets:

- **Reading** (`navigation.py`): the root project's `whxdata/whtoc_xml.js` names its TOC data file; `<project ref>` entries splice child projects in recursively, and each spliced project's keyword index (`whidx_xml.js` chunks) and context-help map (`whcsh_xml.js`) are read too. Projects the TOC never splices in (the `EXP_*` ones) are not read; in 2024 they hold no TOC, index or map files anyway. Missing data files mean no navigation; a data file that holds no `gXMLBuffer` string or no valid XML fails the build.
- **Paths:** hrefs are normalised like links (`normalise_href`) and resolved through `links.Inventory`, the same case-insensitive, Alias-aware lookup that link resolution now uses. The `bc-N` breadcrumb marker on a fragment (`#bc-1`, `#Anchorbc-3`) is dropped; other fragments resolve to Section anchors.
- **Frontmatter:** `toc_paths` (names joined by " > ", each ending with the entry's own name), `keywords` (a sub-keyword as "Key > Sub"), `context_ids`. Aliases merge theirs into the kept Document.
- **Breadcrumbs** (`addTocInfo`) are kept in the model as `breadcrumbs`, relative to their own project's TOC. A Document in no TOC gets them as `toc_paths`, prefixed with where its project is spliced in. In 2024 only `EXP_*` topics need this, so a synthetic release tests it.
- **Dropped entries:** TOC entries and keyword topics that lead to no Document, and books or keywords left empty, are left out of `toc.md`, `keywords.md` and browse. The report's `navigation` counts what is kept and dropped.
- **Persistence:** each Build has `navigation.json` (the resolved trees); assembly loads it into the `nav_entries` table. `toc.md` and `keywords.md` sit at the root of the Collection's tree, so the Collection-relative Locators resolve as links there.
- **Browse:** `browse(path, tree="toc"|"keywords")` takes names joined by ">", matched without regard to case and spacing, and lists the children with their Locators and the number of entries below them. Same-named books (such as one per Collection) are browsed together. Unknown names fail with the nearest matches. Keywords are merged across projects by name and sorted.
- **Open points.**
  - Search does not weight `toc_paths` and `keywords` yet (ticket 06, ADR 0008).
  - `context_ids` are in the Markdown frontmatter only; `read` (ticket 08) will make them reachable over MCP.
  - The Library menu tree joins browse as a third tree in its own ticket.
  - The glossary has no entries for table of contents, book, keyword index or breadcrumb yet.
