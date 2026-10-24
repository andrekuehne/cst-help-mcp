# Spec: CST Help Knowledge Base, version 1

Status: ready-for-agent

Vocabulary follows `GLOSSARY.md`. Decisions that are hard to reverse are recorded in `docs/adr/` (0001–0013) and are only summarised here. Facts about the material come from `docs/research/` (corpus, Library and tool surveys), and the acceptance benchmark is `docs/benchmark-draft.md`.

## Problem Statement

I simulate antennas and RF structures in CST Studio Suite. I would like coding agents (Claude Code, Cursor, Codex) to write CST VBA macros and Python scripts for me, to drive CST through a Control Server (mcp-cst-studio), and to answer "how do I do X in CST" questions. Today they do this badly.

- **The documentation is out of reach.** It ships as about 3,300 topics of RoboHelp 11 WebHelp, a Sphinx Python reference, a dozen PDF manuals and a Library of about 700 example code files, inside my installation. An agent can't search it, can't see the figures, and doesn't know that the author keyword index or the table of contents exist.
- **Agents invent API calls.** Writing CST VBA by hand is tedious and the API is large, so agents guess method names and argument orders. The Control Server's own reference covers only 33 hand-picked objects.
- **The best knowledge is in examples, not prose.** About three quarters of the Library has no help page, the code uses members the help never documents, and CST's idioms (history-command blocks, Result Template structure, dialogs, settings storage) are spread across hundreds of files.
- **The markup misleads naive tools.** `<h3>` holds prose, VBA headings exist only as CSS classes, code is one paragraph per line, equations are TeX inside ordinary text, and answers sometimes exist only in a figure.
- **Licensing constrains everything.** The documentation is Dassault Systèmes' copyrighted material, licensed to me. The tool is internal and never published, but the corpus and built Knowledge Bases stay out of the repository, so the tool must run on each user's own installation (ADR 0001).

## Solution

A Python tool, `cst-help-mcp` with the CLI `cst-help`, that builds a private, portable Knowledge Base from my own CST installation and serves it to agents:

- **Build:** `cst-help build` reads a Release's help, Python reference, manuals and Library, and writes a Markdown tree with the original files, the images and a search index. Expensive work is cached, everything runs locally, and no model or cloud service is involved.
- **Serve:** a read-only MCP server, `cst-help`, gives agents five tools: exact lookup of API Entries, Helpers, Display Names and materials; ranked search; reading by Locator; images; and browsing the table of contents, keyword index and Library tree. One server serves exactly one Release.
- **Read directly:** every search hit's Locator is also a file path, so agents with file access can open or grep the same content.
- **Learn from examples:** each API Entry shows the Library Sections that use it. Members that Library code uses but the help doesn't document are reported as such, instead of "not found".
- **Start a help session:** the Knowledge Base folder is a ready-to-open agent workspace, with a generated `AGENTS.md`, MCP configuration for each client, and the skills for writing Guides.
- **Use it from a project:** `cst-help instructions` prints the MCP entry and AGENTS.md section to add to my own project repositories, next to the Control Server.
- **Guides, later:** agent sessions write Guides summarising patterns and pitfalls. They're marked as generated, cite their sources, and are checked against the documentation when ingested.

## User Stories

### Building a Knowledge Base

1. As a CST user, I want to point the tool at my CST installation folder, so that I can build a Knowledge Base without copying files around.
2. As a CST user, I want to describe my Knowledge Base in one TOML file (its path, Collections, Sources and preferences), so that a build is repeatable.
3. As a CST user, I want a `cst-release` Source that already knows a release folder's layout (help, manuals, Library) and what to exclude, so that I don't have to configure dozens of paths.
4. As a CST user, I want to build one Collection at a time, so that adding a few PDFs doesn't rebuild a whole Release.
5. As a CST user, I want a new Build to take over only once it is complete, so that a running server never sees a half-written Knowledge Base.
6. As a CST user, I want a running server to keep the Build it opened until it restarts, so that rebuilding on Windows never fails on locked files.
7. As a CST user, I want PDF conversion cached by file content and converter settings, so that rebuilds after small changes take seconds or minutes, not the full conversion time.
8. As a CST user, I want the build to stop with a clear error when a Source's expected structure isn't recognised, so that I never serve a silently empty Collection.
9. As a CST user, I want per-Document failures listed in a build report, with the Knowledge Base marked incomplete, so that I can judge whether the result is good enough.
10. As a CST user, I want a `--strict` option that turns any Document failure into a failed build, so that I can insist on a clean result.
11. As a CST user, I want the build report to count discovered, converted, skipped and failed Documents, unresolved links, missing Assets and unsupported items, so that I can see coverage at a glance.
12. As a CST user, I want the build to run fully offline on my Windows laptop's CPU, so that I need neither a GPU nor a network connection.
13. As a CST user, I want to build on one machine and copy the Knowledge Base to another, so that heavy work can happen wherever it is convenient.
14. As a CST user, I want to add a second Release beside the first, so that I can keep working with projects from an older version.
15. As a CST user, I want to remove an old Release as a deliberate step, so that nothing disappears by accident.
16. As a CST user, I want to add a release-independent Collection of extra PDFs later, rebuilt from its folder, so that new material joins without touching the Releases.
17. As a CST user, I want `cst-help validate` to check a Knowledge Base's integrity, so that I can trust a copied or old bundle.
18. As a colleague with my own CST licence, I want to install only the lightweight serving part and build from my own installation, so that I never need someone else's licensed content.

### Content fidelity

19. As an agent, I want navigation boilerplate removed from every topic (logos, breadcrumb scripts, footers, skin pages), so that Sections contain only content.
20. As an agent, I want dialog field lists rendered as field definitions, so that I can tell a field's name from its description.
21. As an agent, I want VBA code samples rendered as real code blocks with their indentation, so that I can copy them.
22. As an agent, I want TeX from the MathJax pages kept exactly as written, so that I can read and quote formulas.
23. As an agent, I want equation images kept as images and marked "not transcribed", so that I know to look at them rather than trust missing text.
24. As an agent, I want simple tables as Markdown and tables with merged cells as HTML, so that no cell associations are lost.
25. As an agent, I want popup links to work as ordinary links, so that I can follow them to the text they show.
26. As an agent, I want commented-out and hidden retired content left out, so that I don't quote text CST no longer shows.
27. As an agent, I want every Document to carry its Release, Area, title, original source path, table-of-contents paths and author keywords in its frontmatter, so that I can cite it precisely.
28. As an agent, I want topics that CST published identically in several places to appear once, with the other paths as Aliases, so that results aren't cluttered with copies.
29. As an agent, I want internal links resolved without regard to case and rewritten as Locators, so that I can follow them in the Knowledge Base.
30. As an agent, I want each PDF manual as one Document with page and section anchors, so that I can cite page numbers.
31. As an agent, I want topics outside any table of contents (including the Example Projects) included, so that search reaches all content.
32. As an agent, I want the breadcrumb paths embedded in topics used as table-of-contents paths where the table of contents has none, so that topics carry their context.
33. As an agent, I want every image as an Asset, deduplicated by content, with BMP and SVG converted to PNG, so that every client can display it.
34. As an agent, I want inline icons kept as small images with readable alt text, and logos and chrome dropped, so that "click this icon" still makes sense.

### API Entries and lookup

35. As an agent writing a macro, I want to look up `Solver.FrequencyRange` and get its signature, parameters, description and Locator in one call, so that I don't guess.
36. As an agent, I want a bare member name such as `FrequencyRange` to return every object that has it, labelled by Area, so that I can pick the right one.
37. As an agent, I want same-named objects in different Areas (for example the two "Solver Object" pages and the two "Project Object" pages) kept apart, so that I don't mix the 3D and schematic APIs.
38. As an agent, I want lookups to ignore case, so that `solver.frequencyrange` works as VBA does.
39. As an agent, I want WinWrap Basic built-ins (`Left$`, `Begin Dialog`) as API Entries, so that I can check the language as well as the CST objects.
40. As an agent, I want the Python reference's classes, methods, properties and functions as API Entries under their dotted names, so that Python scripts are as checkable as VBA.
41. As an agent, I want the methods that VBA code calls without an object (`AddToHistory`, `SelectTreeItem`) resolved to the Application object, so that lookups for them succeed.
42. As an agent, I want each API Entry to list the best few Library Usages, so that I can see working code before I write my own.
43. As an agent, I want a member that the help doesn't document but Library code uses (such as `Units.GetFrequencyUnit`) reported as an Undocumented Member with its Usages, so that I can still use it knowingly.
44. As an agent, I want a member that is neither documented nor used anywhere reported plainly as not documented, so that I don't invent it.
45. As an agent, I want `api-index.md` listing every API Entry with its signature and Locator, one per line, so that I can grep it.

### The Library

46. As a CST user, I want to say "build it like the Farfield Result template" and have the agent find that template, so that it can copy CST's own way of doing things.
47. As an agent, I want Display Names (the menu path plus file stem) as lookup keys, with a ranked shortlist when names are ambiguous, so that loose names still lead to the right file.
48. As an agent, I want a Library item's Application Filter shown and filterable, with MWS Variants preferred, so that I use the version meant for the high-frequency solver.
49. As an agent, I want each Macro, Result Template and Include split into a header Section and one Section per procedure, so that a result points at the relevant procedure in a 4,000-line file.
50. As an agent, I want each Library Document's metadata to list its Includes, the Helpers it calls, its help page and its Aliases, so that I know what code depends on.
51. As an agent, I want Helpers such as `GetLastResult_LIB` resolvable by name, showing their signature, comments, defining Include, the `'#include` lines to paste and their Usage count, and labelled "not a documented CST API Entry", so that I can reuse them correctly.
52. As an agent, I want scrambled Macros listed by name and menu path only, so that I know they exist without seeing unreadable content.
53. As an agent, I want legacy templates flagged and ranked lower, so that I learn the current layout first.
54. As an agent, I want the Library's dialog bitmaps as Assets of the Documents that load them, so that I can see what a dialog shows.
55. As an agent, I want to filter search to prose or to code, so that I can look for an explanation or for working code.
56. As an agent, I want to look up a material by its exact name, its base name, its name without vendor, or a normalised form (`FR4` → `FR-4`), so that I find the exact name to put in `.Material "…"`.
57. As an agent, I want a Material Definition rendered as a table per Material Set with units, CST's own attribute summary, its description, its Variants and its verbatim definition, so that I can compare materials and use one correctly.
58. As an agent, I want permittivity ranges for fitted materials computed from their tables and labelled as computed, so that I don't read the placeholder `ε = 1`.
59. As an agent, I want the history block that loads a library material, labelled as inferred until it is confirmed, so that I can send it through the Control Server.
60. As an agent, I want large material families grouped by product in lookup results, so that 334 Panasonic variants don't drown everything else.

### Searching and reading

61. As an agent, I want ranked search over titles, author keywords, table-of-contents paths, headings and body text, weighted in that order, so that the defining page comes first.
62. As an agent, I want search narrowed to one or more Areas, so that a macro question searches only VBA 3D, WinWrap Basic and the Library.
63. As an agent, I want CST's vocabulary bridged through Synonym Sets (time domain ↔ transient ↔ T-solver ↔ `Solver`), so that my words find the page's words.
64. As an agent, I want partial identifiers like `MeshProp` to match, so that half-remembered names still work.
65. As an agent, I want raw query text never to cause a search syntax error, so that dotted names and punctuation are safe.
66. As an agent, I want each hit to show its Locator, Release, Area, kind, title, heading path, a snippet, and whether it is generated or heuristic, so that I can judge it before reading.
67. As an agent, I want at most 10 hits, in about 3,000 tokens, so that a search never floods my context.
68. As an agent, I want `cst_help_read` to return a Section's Markdown in pages of about 8,000 tokens, with a cursor for the rest, so that I can read long Documents in steps.
69. As an agent, I want `cst_help_read` to list a Section's outgoing links and images, so that I can follow them.
70. As an agent, I want to request one image, all figures of a Section, or a figure with its neighbours, as actual image content, so that I can see what the text refers to.
71. As an agent, I want a PDF page or page region rendered on demand, so that I can check layout the text extraction lost.
72. As an agent, I want at most 4 images per call, scaled to 1,568 px on the long edge, so that images fit my client's limits.
73. As an agent, I want to browse the table of contents, the author keyword index and the Library menu tree, so that I can explore a topic systematically, for example everything under "Solvers > Time Domain Solver".
74. As an agent with file access, I want to open and grep the Markdown tree directly using the same Locators, so that I can use my own tools.
75. As a CST user, I want a server to serve exactly one Release, fixed when it starts, so that an agent never mixes methods from two versions.
76. As a CST user, I want the server to say when the Knowledge Base is incomplete, so that agents can warn me.
77. As a CST user, I want `cst-help search` and lookups on the command line, so that I can check results myself.

### Agent integration

78. As a CST user, I want to open Claude Code, Cursor or Codex in the Knowledge Base folder and start asking, so that a help session needs no setup.
79. As an agent, I want a generated `AGENTS.md` under about 8 KB, holding the routing rules, the citation and "not documented" rules, and an index of each Area's entry files and every Guide, so that I know what's available from the first turn.
80. As an agent, I want server instructions whose first 512 characters say when to use lookup and when to use search, so that I route correctly even when only that much is shown.
81. As an agent in a help session, I want a `work/` folder that builds never touch, so that I have a safe place for the macros I write.
82. As a CST user, I want `cst-help instructions` to print the MCP entry and AGENTS.md section for my own repositories, so that project sessions next to the Control Server can consult the Knowledge Base.
83. As a CST user, I want the server usable on its own, without the Control Server, so that the Knowledge Base is useful even when CST isn't running.
84. As a CST user, I want tool names (`cst_help_*`) that can't be confused with the Control Server's `cst_*` tools, so that agents call the right server.

### Guides

85. As a CST user, I want to run a help session in which an agent, guided by a skill, writes a Guide on one topic (history commands, Result Template anatomy, dialogs, settings storage, `cst.interface` sessions) into `work/guides/<release>/`, so that hard-won patterns are written down once.
86. As a CST user, I want `cst-help build` to ingest those Guides as their own Collection, tied to the Release, so that they are served with it.
87. As a CST user, I want ingestion to flag any Guide whose cited Locators don't exist, or whose code uses identifiers that are neither API Entries, Helpers nor Undocumented Members, so that invented methods are caught mechanically.
88. As an agent, I want every Guide marked as generated, citing its sources, with no ranking boost, so that I treat it as a map and verify details in the cited Documents.

### Developing the tool

89. As a developer, I want tests to run against the real corpus on my machine, so that the tests exercise what users will actually build.
90. As a developer, I want the benchmark scored automatically (whether an expected source is in the top five, and how high), per category, so that I can see whether a change helps.
91. As a developer, I want to build a subset of a Release (for example only VBA 3D and WinWrap Basic), so that tests and experiments run quickly.

## Implementation Decisions

### Packaging and platform

- **One package, two install profiles.** The default install covers serving, search and the CLI. A `build` extra pulls in the conversion stack. Serving needs only the official `mcp` 2.x SDK, the standard library's SQLite, and a small PDF page renderer.
- **Python 3.13, Windows first.** Code stays portable; nothing is tested on Linux for now.
- **License:** MIT. Every dependency must be permissive, so no AGPL (PyMuPDF), no GPL (html2text, the pandoc binary), and no restricted model weights.

### Configuration and CLI

- **Configuration:** a TOML file names the Knowledge Base path, its Collections and their Sources, and preferences (the preferred application, MWS).
- **Source types:**
  - `cst-release`: a release folder, which may be the installation itself. It knows the `Online Help` + `Documentation` + `Library` layout and its exclusions:
    - FEST3D, SPARK3D and IdEM, and their PDFs;
    - the FlexNet guide;
    - MathJax copies and the WebHelp runtime;
    - wheels, executables, registry and batch files, Excel workbooks and project files;
    - `Bio Models`, `Misc`, `ADS`, the wizard web apps and the component databases;
    - PPT and DOC companions.
  - `pdf-folder`: release-independent PDFs.
  - `guides-folder`: Guides.

  Every Source accepts include and exclude filters, so a Release can be built in parts.
- **CLI commands:** `cst-help build <collection>`, `assemble`, `validate`, `search`, `lookup`, `serve --kb <path> [--release <id>]`, and `instructions`. The Knowledge Base path is always explicit.

### Collections, Releases and Areas

- **Collections:** `cst-<release>` holds everything shipped with a Release. `cst-<release>-guides` holds the Guides for that Release. Release-independent Collections may be added.
- **Serving:** a server serves one Release, chosen at start and defaulting to the newest, plus every release-independent Collection (ADR 0005).
- **Areas of a release Collection:**

  | Area | Contents |
  |---|---|
  | `general` | General features, user interface, ribbons, advanced, license, simulation acceleration, and the Python menu topics at the help root |
  | `3d` | 3D Simulation |
  | `circuits` | DES |
  | `pcb` | PCB |
  | `filter-designer` | Filter Designer 3D |
  | `chip-interface` | CHI |
  | `vba-3d` | VBA for the 3D modeler, and the root project's VBA overview |
  | `vba-schematic` | VBA_DES |
  | `winwrap-basic` | WinWrap Basic language reference |
  | `python` | Python reference |
  | `example-projects` | `EXP_*` |
  | `manuals` | Word manuals and release notes |
  | `macros` | Macros and Includes |
  | `result-templates` | Result Templates |
  | `python-apps` | Python apps |
  | `materials` | Material Definitions |

  Guides Collections have one Area, `guides`.

### Locators

- **The rule** (ADR 0011):
  - drop the `Online Help/` and `mergedProjects/` prefixes;
  - lowercase every path segment;
  - collapse each run of characters outside `a–z 0–9 . _ - + ^` to one `-`, and trim `-` at segment ends;
  - append `.md` to the full file name.
- **Collisions** stop the build.
- **Anchors** are the source's own ids where present. Otherwise they're generated: from the member name for API Entries, from the procedure name for code, from headings for PDF sections, and `page-<n>` for PDF pages.
- **Original source paths** are always kept in frontmatter and in results.

### The Document model and readers

- **The model** (ADR 0007): readers parse each Source into our own Document model:
  - Documents have a kind, an Area, a Locator, a source path, Aliases, Sections, Assets, links and metadata.
  - Sections hold typed blocks: heading, paragraph, list, field definition, code, table, equation, figure, API signature.
  - The model is persisted, so rendering and indexing can change without re-parsing.
  - The Markdown and the search records are both rendered from this model, never from raw HTML.
- **RoboHelp reader** (classic WebHelp 5.x):
  - **Navigation data:** reads the table of contents, keyword index and context-help maps from `gXMLBuffer` JS strings by decoding the string escapes, never by running JS. Breadcrumbs come from `addTocInfo`.
  - **Content:** the content runs between the logo header and the footer. A per-project map from CSS class to block role identifies VBA object, category and method headings, dialog fields, code lines and notes. Class names are matched without regard to case, and multi-name headings ("A / B") are split.
  - **TeX:** recognised only on pages that load MathJax, honouring the page's delimiter configuration.
  - **Other markup:** popups become links, and commented-out content is dropped.
- **Sphinx reader:** reads the main content region, takes API Entries from the inventory, and uses entry anchors equal to the qualified names.
- **PDF reader:**
  - Docling with OCR off, recording page and position for every block. A PDF without a text layer is a reported failure.
  - The formula model is switched on only if the proof of concept finds equations rendered as text glyphs.
  - Running headers and footers are removed.
- **Library reader:**
  - **Classification:** files are classified by content, not extension: Macro (control or structure), Result Template, Include, Python script, Material Definition, preset, data, scrambled, binary.
  - **Encodings:** cp1252 and CRLF are handled.
  - **Display Names and Variants:** a Display Name comes from the folder path plus the file stem before `^`. The Application Filter is parsed, and Variants are linked.
  - **Sections:** one header Section plus one Section per procedure (`Sub`/`Function`, Python `def`/`class`). Files under about 150 lines stay whole, and the change history becomes metadata.
  - **Includes:** `'#include` is resolved without regard to case against the Includes folder, and the dependencies between Includes are computed.
  - **Help links:** `StartHelp` targets are resolved without regard to case.
  - **Material Definitions:** parsed per section and per Material Set.
  - **Python:** only the 5 apps, their descriptors, and the modules that contain VBA strings or `cst.*` calls.
  - **Never:** nothing from the Library is executed or imported, and nothing is descrambled.
- **Guides reader:** Markdown with frontmatter (topic, Release, generated-by) and Locator citations.

### Link resolution and Assets

- **Two passes:** first an inventory of every Document, anchor and Alias, then link resolution.
- **Link status:** each link is resolved, unresolved, external, or outside the corpus, and the report lists every unresolved one.
  - **Outside** means the target file exists in the release folder but is no Document of the Build, such as a project not read or filtered out, a PDF, or an image. The report counts outside links by the project or file type they lead to.
  - **Unresolved** means the target exists nowhere in the release folder, as with links to `Videos/` and `Licenses/` folders a release folder may lack. Unresolved links never fail a build.
  - A resolved link whose fragment the target's source names nowhere is reported as a missing anchor.
- **Aliases and Areas:** a Document keeps the Area of the copy that is kept, but a search narrowed to an Alias's Area finds it too.
- **Assets:** deduplicated by content hash. BMP and SVG become PNG at build time, along with derived images scaled for clients.
- **Image metadata:** each Asset carries its caption or alt text, dimensions, kind (figure, icon, equation image) and the Documents that reference it.

### Identity and lookup tables

- **API Entries:** identified by Area plus qualified name.
  - VBA uses `Object.Member`. Global methods belong to the Application object ("Project Object").
  - WinWrap Basic uses keywords as written.
  - Python uses dotted paths.
  - Matching ignores case.
- **Name table:**
  - Display Names, menu paths and help page titles, plus in-file titles at low weight.
  - Helpers: public Include procedures, with module-level names at lower weight; names that collide with entry points are stored only in qualified form.
  - Material keys: exact name, base without loss qualifier, name without vendor, and a normalised form.
  - Each key returns ranked candidates.
- **Usage index** (ADR 0012), built from Library code:
  - it reads VBA in string literals, maps calls without an object to the Application object, and counts names passed to `CallByName`;
  - it records Undocumented Members;
  - every Usage is labelled heuristic;
  - Material Definitions don't count as Usages; instead each Material member gets a count ("set in N library materials").
- **Synonym Sets:** a small file shipped with the tool, extensible by the user, and grown only when a benchmark question fails for lack of one. Search applies them at lower weight than the literal query.

### Search index

- **One SQLite database per Knowledge Base**, assembled from the active Builds (ADR 0008):
  - an exact table of API Entries, consulted first;
  - the name table;
  - an FTS5 word index with field weights, highest first: title, author keywords, table-of-contents path, headings, body;
  - a trigram index for partial identifiers.
- **Code Sections** get their own field weights. Display Name and menu path weigh high, comments and dialog labels medium, referenced identifiers go in their own field, code bodies weigh low, and change history isn't indexed.
- **Materials:** fitting-table rows aren't indexed.
- **Queries:** raw query text is never passed to FTS5.
- **Ranking:** no embeddings, hybrid search or reranking.

### Builds and assembly

- **Builds** (ADR 0009): each Collection is built into a new, immutable Build directory. Only PDF conversion is cached, keyed by content hash plus converter version and settings. The cache lives outside both the Knowledge Base and the checkout: a per-user cache directory by default, configurable. It is never part of a portable Knowledge Base.
- **Assembly** combines the active Builds into the Knowledge Base's database and entry files, then switches the active pointer atomically.
- **Each Collection's entry files:** `toc.md`, `keywords.md`, `api-index.md`, a Library menu tree, and a materials index.
- **Workspace files written by assembly** (ADR 0013):
  - `AGENTS.md`, `CLAUDE.md` (which imports it);
  - `.mcp.json`, `.cursor/mcp.json` and a Cursor rule, all using relative paths;
  - the Guide-writing skills, copied into `.claude/skills/` and `.agents/skills/`;
  - a `work/` folder that's never touched.
- **Build report:** written per Build and summarised by the CLI. It shows counts and coverage, failures, unresolved links, missing Assets, unsupported items and Guide check failures. The completeness flag is visible to the server.

### Retrieval core and MCP server

- **Retrieval core:** one interface serves the MCP tools, the CLI and the tests. It is opened on a Knowledge Base and a Release, and reads stay confined to the Knowledge Base root.
  - `search(query, areas?, kind?, limit ≤ 10)` → hits with Locator, Release, Area, kind, title, heading path, snippet, and generated/heuristic flags.
  - `lookup(name, area?, application?)` → ranked candidates. A candidate is an API Entry (signature, parameters, description, Locator, top Usages), a Helper, a Display Name match with its Variants, a Material, or an Undocumented Member with its Usages. If there is none, the result says "not documented".
  - `read(locator, cursor?)` → the Section's Markdown, byte-identical to the file, in pages of about 8,000 tokens, plus outgoing links and image references.
  - `images(locator or asset ids, neighbours?, include_icons?)` → at most 4 PNG or JPEG images, at most 1,568 px on the long edge, with captions. PDF pages and regions are rendered on demand.
  - `browse(target)` → children of a table-of-contents node, keyword index entries, or a Library menu folder.
- **MCP server:** `cst-help`, built on the official SDK over stdio.
  - Its tools wrap the retrieval core one to one: `cst_help_search`, `cst_help_lookup`, `cst_help_read`, `cst_help_images`, `cst_help_browse`.
  - It has no MCP resources or prompts.
  - Its server instructions open with the routing and citation rules in the first 512 characters, followed by the "not documented" rule, the Guide caveat, the include warning for Library code, and the Knowledge Base path for file access.
  - Every response stays under 10,000 tokens.
  - It makes no network calls and logs to stderr only.

### Guides

- **Authoring:** Guide-writing skills ship in the package, one per topic family. Authoring happens in agent sessions, and the tool contains no LLM client (ADR 0010).
- **Ingestion checks:** every cited Locator must exist, and every identifier in a Guide's code blocks must resolve to an API Entry, a Helper or an Undocumented Member. Failures are flagged in the report.
- **Privacy:** Guides stay private with the Knowledge Base.

### Proof of concept, then the rest

- **The proof of concept** is a slice of `cst-2024`:
  - **Areas:** VBA 3D, WinWrap Basic, 3D Simulation, Python, and two Word manuals.
  - **Features:** all five tools; the Markdown tree with its entry files; the workspace files; the benchmark questions for those Areas.
  - **Checks:** by hand in Claude Code and Cursor.
- **Then:**
  - the Library (Macros, Result Templates, Includes, Materials);
  - the remaining Areas and all manuals;
  - several Collections and Releases in one Knowledge Base;
  - Codex;
  - Guides.

## Testing Decisions

- **Real data first.** Every development machine has the CST 2024 corpus, so tests build from it and check what users will get.
- **Finding the corpus from any checkout.** `.ingestion/` is gitignored, so a git worktree (for example one used by an implementer subagent) doesn't contain it. Corpus tests resolve the corpus in this order:
  1. an environment variable naming the release folder. This may be the installation itself, such as `C:\Program Files (x86)\CST Studio Suite 2024`;
  2. `.ingestion/<release>/` in the current checkout;
  3. `.ingestion/<release>/` in the repository's main checkout, found through git's common directory, so worktrees use it automatically.
- **Failing instead of silently skipping.**
  - A location that is configured but missing or unreadable is a test **failure**, never a skip.
  - When nothing is found at all, corpus tests skip only if an explicit opt-out is set (for a future CI without licensed data). Otherwise they fail with a message naming every place searched.
  - Every test run reports which corpus it used, or that the corpus tier was skipped and why. A green run can therefore never hide an empty corpus tier.
- **Synthetic fixtures stay minimal.** They're used only for behaviour the corpus can't exercise:
  - Locator collisions;
  - a Source whose structure isn't recognised, failing the build;
  - Guide check failures;
  - a release-independent `pdf-folder` Collection;
  - several Releases in one Knowledge Base;
  - Build immutability and the pointer switch.

  Fixtures stay small. They may be hand-written or cut from real pages, and test assertions may quote vendor text (ADR 0001).
- **Three seams, all high-level:**
  1. **Build, then query.** Build a Collection, or a filtered part of one, into a temporary Knowledge Base. Then check the results through the retrieval core and the files the build wrote: rendered Markdown, entry files, the build report. Reader internals are not tested directly. A quirk such as MathJax TeX, a VBA heading marked only by CSS class, or a `.mtd` Material Set is tested by what it renders and what lookup returns.
  2. **MCP contract,** through the SDK's in-memory client. Covers tool names and parameter schemas, the start of the server instructions, output budgets, image content types, the Release fixed at start, clear errors, and refusal to read outside the Knowledge Base.
  3. **Benchmark.** `docs/benchmark-draft.md`, turned into a machine-readable form, is scored by whether an expected source is among the top five, and how high, per category. Expected sources are mapped from source paths to Locators mechanically. Pass thresholds are set after the first baseline run. The "not in the documentation" questions and the agent checks in Claude Code, Cursor and later Codex stay manual.
- **Good tests check external behaviour:** search and lookup results, rendered files and MCP responses. They never check private data structures, so the internals can be refactored freely.
- **Speed:** tests build filtered parts of a Release (for example VBA 3D plus WinWrap Basic) and share one Build per test session. The PDF cache keeps repeated runs fast, and because it lives in a per-user directory, worktrees and repeated runs share it. Test Knowledge Bases are written to temporary directories, never into the checkout.
- **Prior art:** none in the repo yet, since the package is a stub. Follow the `tdd` skill: red, green, refactor at these seams.

## Out of Scope

- OCR of any kind: equation images, screenshots, scanned PDFs (ADR 0006). Transcription may come later as an opt-in enrichment, together with a corrections file.
- Embeddings, hybrid search and reranking (ADR 0008), until the benchmark shows a need.
- MCP resources and prompt templates. To revisit after the proof of concept.
- FEST3D, SPARK3D and IdEM. The design must not prevent adding them later.
- GPU, MPI and licensing documentation.
- Library folders other than Macros, Result Templates, Includes, Materials and Python apps; the `cstapps` GUI framework; PPT and DOC companions; Office and executable files.
- Personal or company macro folders (Global Library Path). These come later, as their own Collection.
- Changes to mcp-cst-studio, such as redirecting its `cst_vba_help`. A follow-up in that repository.
- Any LLM client inside the tool, and generating Guides during `cst-help build`.
- Exporting Guides as installable Agent Skills.
- CI configuration (GitHub or GitLab, to be decided), Linux testing, a hosted service, a GUI, live file watching.

## Further Notes

- **To verify in CST during the proof of concept** (CST 2024 is installed on the development machine):
  - whether `'#include` resolves for code sent through `add_to_history`;
  - whether "Load from Material Library" records the inferred history block;
  - benchmark questions API-05, API-10 and SOL-02;
  - how Docling handles the formulas in the Word manuals.
- **To verify in the clients:**
  - images from MCP tools in Claude Code, Cursor and Codex;
  - whether Cursor uses server instructions;
  - whether Codex accepts a project-level MCP configuration.
- **Benchmark next steps:** turn the draft into its machine-readable form, and add Library and Materials questions such as "exact name for Rogers RO4350B" and "which copper for a lossy metal".
- **Prior art:** MuziIsabel/CST-Studio-Suite-Help (MIT) is a reference for ideas only. No code is taken from it.
- **Python coverage** is expected to grow in later Releases (2026), so Python benchmark questions should be reviewed for each Release.
