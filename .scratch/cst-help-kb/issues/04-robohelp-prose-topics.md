# 04: RoboHelp prose topics for 3D Simulation and General

**What to build:** The `cst-release` Source also reads the 3D Simulation project and the root project's own subtrees (general features, user interface, ribbons, advanced, license, simulation acceleration) into Areas `3d` and `general`. Content comes through faithfully, without the navigation boilerplate, and links between topics work as Locators.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] Topic content is taken from between the logo header and the footer. WebHelp shell pages, breadcrumb scripts, footers, logos and spacer paragraphs are dropped.
- [x] The per-project map from CSS class to block role turns prose held in `<h3>` into paragraphs, dialog field lists into field definitions, and "Note:" paragraphs into notes.
- [x] Simple tables render as Markdown tables. Tables with merged cells stay as HTML.
- [x] Popup links become ordinary links, and commented-out content is dropped.
- [x] Topics that appear in no table of contents are included.
- [x] Topics published identically in several places become one Document, with the other paths as Aliases.
- [x] Links are resolved in two passes, without regard to case, and rewritten as Locators. Each link is marked resolved, unresolved, external or outside the corpus, and the report lists the unresolved ones.
- [x] Corpus tests check representative pages, such as the Brick dialog page and the polarization theory page, by their rendered Markdown and by search.

## Comments

**Implemented (2026-10-24), revised the same day.** 21 corpus tests in `tests/test_3d_general.py` check real topics (Brick, Polarization, material overview, lumped elements and others) by their Markdown, search and the build report. There are no synthetic fixtures for this ticket, because the corpus exercises every rule (spec, "Synthetic fixtures stay minimal"). The full suite has 88 tests. The development `.kb` now builds every Area read so far: 1,514 Documents, 46 Aliases, 7 unresolved links (genuinely broken in CST's help, or into the missing `Videos/` folder), 7 missing anchors and no failures, and it validates.

Decisions for later tickets:

- **Projects.** `build._CST_RELEASE_PROJECTS` lists the Area, folder and Profile of each project.
  - General is `general`, `userinterface`, `ribbons`, `advanced`, `license` and `simulation_acceleration`.
  - The root `vba/` folder holds the VBA Overview, the macro language's overview topic. It is read into `vba-3d`, not `general`, because macro questions search VBA 3D (spec story 62).
  - The root `menu.htm` and `user_scipts.htm` (the Python menu topics) are read into `general`. They don't load `whtopic.js`, so their project lists them by name (`_Project.topics`) and they are read as topics without that check. They could move to `python` once ticket 12 exists.
  - A release folder missing any listed project fails as unrecognised.
- **Profiles** (`robohelp.Profile`) map CSS class (lowercase) and tag to a role.
  - In `PROSE` (3D and General), `h3` is a paragraph and `h4`–`h6` are headings of levels 3–5.
  - `Tip-Note-Heading` is a field name, described by the `Topic-Text-Indent` or `Tip-Note-Text` paragraph that follows it.
  - Any paragraph that starts with "Note:" or "Please note:" is a note, and so is a field named "Note:".
  - Note detection applies to VBA too, and an API Entry's description includes its notes as "Note: …".
- **Link spans.** A block's text marks each link as `[label](@N)`, N indexing `Document.links`. Search text strips the spans (`model.plain`). Rendering turns them into Markdown links, or `<a>` inside HTML tables. Headings keep their links.
- **Link status** (`links.py`, run after every Document is read):
  - **resolved:** the path matches a Document or Alias without regard to case. The fragment matches an anchor case-insensitively, or through `anchor_for`; otherwise the link leads to the Document itself.
  - **external:** a URL.
  - **outside:** a file that exists in the release folder but is no Document of this Build: a project not read yet or filtered out, a PDF, an image or a download. The report's `outside_links` counts them by project folder, or by file type for files that aren't topics.
  - **unresolved:** a file that exists nowhere in the release folder, including paths above it. In `.ingestion/2024` that includes the links to `Videos/`, which isn't shipped there. Unresolved links never fail a build, even with `--strict`.
  - **missing anchors:** a resolved link whose fragment matches no Section anchor and no `id` or `name` in the target's source (`Document.source_anchors`) is listed in the report's `missing_anchors`. The 7 in the corpus are anchors CST renamed, such as `#Mesh_Control_Regions` for `Mesh_Control_Items`.
  - Links render as Collection-relative Locators (`[label](3d/….htm.md#anchor)`), not file-relative paths, as the ticket asks. Ticket 26 makes them work in ordinary Markdown readers. Unresolved and outside links render as their label only.
  - The report has `links` (counts by status) and `unresolved_links` (source and href of each).
  - **Ticket 08** can list a Section's outgoing links from its spans.
- **Aliases.**
  - Documents with the same title and whitespace-normalised text are merged. Text rather than structure is compared, because VBA_3D parses its ribbon copies with another Profile.
  - The first in project order wins (general, 3d, vba-3d), so the ribbon topics belong to General.
  - The kept Document records the other Areas of its Aliases (`alias_areas`, also in frontmatter). The index's `section_areas` table lists every Area a Section is found under, so a search narrowed to `3d` still finds the Modeling ribbon topic. Hits report the Document's own Area.
  - Locator collisions are checked before merging.
  - Frontmatter lists the `aliases`, and the report counts them.
- **Tables.**
  - A table with a rowspan or colspan above 1 keeps every row and renders as HTML, with `Block.spans`.
  - Only direct rows are read, so a nested table's text lands in its cell.
- **Dropped:** comments and processing instructions, "up" links back to a topic's own contents, and the anchors of popup links (a heading's anchor is a bare `<a name>`).
- **Open points.**
  - Text such as `<Curve item name>` is written to the Markdown unescaped, so a renderer may take it for HTML (ticket 26).
  - Inline bold and italics are not kept.
  - A field name followed by several description paragraphs keeps only the first as its description.
