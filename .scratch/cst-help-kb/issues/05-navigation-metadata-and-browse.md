# 05: Navigation metadata and browse

**What to build:** The build reads RoboHelp's table of contents, author keyword index and context-help maps from the `gXMLBuffer` data files without running any JavaScript. Child project tables of contents are spliced into the root one. Documents carry their table-of-contents paths and author keywords in frontmatter, using the embedded breadcrumbs where the table of contents has none. Each Collection gets `toc.md` and `keywords.md`. The new `cst_help_browse` tool, with a matching CLI command, walks the table of contents and the keyword index.

**Blocked by:** 02, 04

**Status:** ready-for-agent

- [ ] Every RoboHelp project's navigation data parses after decoding the JS string escapes. Paths with backslashes and mixed case are resolved without regard to case.
- [ ] A Document listed in several places in the table of contents carries all of its paths.
- [ ] Breadcrumbs from `addTocInfo` supply table-of-contents paths for topics that are in no table of contents.
- [ ] `toc.md` and `keywords.md` are generated as nested links that resolve within the tree.
- [ ] Browsing "3D Simulation > Solvers > High Frequency > Time Domain Solver" lists its pages, and browsing a keyword lists its target topics.
