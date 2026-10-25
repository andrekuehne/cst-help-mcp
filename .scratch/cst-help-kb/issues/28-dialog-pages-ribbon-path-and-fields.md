# 28: Dialog pages: Ribbon Path as metadata, fields as headings

**What to build:** The RoboHelp reader models dialog pages the way CST wrote them. The Ribbon Path line under the title ("Simulation: Solver > Setup Solver") becomes a Document field, rendered and indexed like a table-of-contents path, instead of the heading of the page's only Section. Dialog frames and fields, which the reader already captures as field definitions, give the page its sub-structure for search. Navigation-only Sections are never search hits.

**Blocked by:** 04, 05

**Status:** wontfix

- [ ] `Document.ribbon_paths` holds each Ribbon Path of a topic, as written, with its popup link reduced to its label. The frontmatter and the Markdown show it as a field under the title ("Ribbon: Simulation: Solver > Setup Solver"), not as a heading. Pages without one are unchanged.
- [ ] Ribbon Paths are indexed in `documents_fts`, in the `toc_paths` column or one of their own at the same weight. A dialog page whose table of contents gives no path, and which has no breadcrumbs, gets its Ribbon Path as the path shown in hits and frontmatter (spec story 32 extended).
- [ ] A dialog page's content Section no longer has the Ribbon Path as its heading. Its anchor is derived from the title, and existing links to the old anchor stay resolved (the old generated anchor is kept in `Section.anchors`).
- [ ] The terms of `field` blocks (frame names and field names) are indexed in the `headings` column of `sections_fts`, in addition to the body, so that "Accuracy" on the Solver Parameters page counts as a heading match. Alternatively, each frame starts a Section; whichever the reader can do reliably on the 3D project is chosen, and the choice is recorded here.
- [ ] Sections that hold nothing but navigation (an empty body, a "Contents" or "See also" list of links, a lone Ribbon Path line) are not indexed as search hits. Their links still resolve and `cst_help_read` still shows them.
- [ ] SOL-01 filtered to `3d` finds the Solver Parameters page among the top 5, and "time domain solver accuracy" finds it unfiltered, with the default `Ranking`. The eight tracked questions keep or improve their recorded ranks.
- [ ] Corpus tests check a dialog page (the Time Domain Solver Parameters page, or the Brick dialog page from ticket 04) by its Markdown: Ribbon Path as a field, one content Section with a title-derived anchor, field definitions intact.

## Comments

**2026-10-25, from the proposal.** On the development `.kb`, 649 of 1,087 3D Documents are one empty title Section plus one content Section whose heading is the Ribbon Path; 935 of 1,042 3D Documents have field definitions; 1,366 Sections have an empty body. The Time Domain Solver Parameters page is 12 KB in one Section with `toc_paths` and `breadcrumbs` both empty, so for "time domain solver accuracy" it ranks 28th behind shorter pages that repeat the same words. As a heading, the Ribbon Path also makes "simulation", "solver" and "setup" heavy and useless on every dialog page. `docs/research/cst-2024-corpus.md` describes the line (an `h2` with an icon, a popup link "Modeling:" and "Shapes > Brick").

**2026-10-25, retired.** A reader change made for the ranker. The Ribbon Path rendered as a heading reads fine to an agent, and the fields are already definition items. Navigation-only Sections are harmless without a ranker. See ADR 0014 and `../files-only-experiment.md`.
