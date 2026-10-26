# Spec: CST Help Knowledge Base, version 1

Status: ready-for-agent

Vocabulary follows `GLOSSARY.md`. Decisions that are hard to reverse are recorded in `docs/adr/` (0001–0014) and are only summarised here. Facts about the material come from `docs/research/` (corpus, Library and tool surveys). The acceptance benchmark is `docs/benchmark-draft.md`, run by agents from the folder (`files-only-experiment.md`).

This is the second version of the spec. The first built a read-only MCP server with ranked search over a SQLite index. ADR 0014 retired it after the benchmark was answered from the Markdown tree alone, with grep and read, by agents given a 4.6 KB `AGENTS.md`.

## Problem Statement

I simulate antennas and RF structures in CST Studio Suite. I would like coding agents (Claude Code, Cursor, Codex) to write CST VBA macros and Python scripts for me, to drive CST through a Control Server (mcp-cst-studio), and to answer "how do I do X in CST" questions. Today they do this badly.

- **The documentation is out of reach.** It ships as about 3,300 topics of RoboHelp 11 WebHelp, a Sphinx Python reference, a dozen PDF manuals and a Library of about 700 example code files, inside my installation. An agent can't grep it, can't see the figures without the markup in the way, and doesn't know that the author keyword index or the table of contents exist.
- **Agents invent API calls.** Writing CST VBA by hand is tedious and the API is large, so agents guess method names and argument orders. The Control Server's own reference covers only 33 hand-picked objects.
- **The best knowledge is in examples, not prose.** About three quarters of the Library has no help page, the code uses members the help never documents, and CST's idioms (history-command blocks, Result Template structure, dialogs, settings storage) are spread across hundreds of files.
- **The markup misleads naive tools.** `<h3>` holds prose, VBA headings exist only as CSS classes, code is one paragraph per line, equations are TeX inside ordinary text, and answers sometimes exist only in a figure.
- **Licensing constrains everything.** The documentation is Dassault Systèmes' copyrighted material, licensed to me. The tool is internal and never published, but the corpus and built Knowledge Bases stay out of the repository, so the tool must run on each user's own installation (ADR 0001).

## Solution

A Python tool, `cst-help-mcp` with the CLI `cst-help`, that builds a private, portable Knowledge Base folder from my own CST installation. Agents read the folder with the tools they already have.

- **Build:** `cst-help build` reads a Release's help, Python reference, manuals and Library, and writes a Markdown tree with the images, the Library code and the PDFs copied in beside it. Everything runs locally; no model or cloud service is involved.
- **Navigate:** the folder carries CST's own table of contents and author keyword index as Markdown, an `api.md` listing every API Entry one per line, a `library.md` and a `materials.md` listing the copied files, and an `AGENTS.md` under 8 KB that says what is where and how to find things with grep.
- **Read directly:** every page is a file whose path is its Locator. An agent greps, reads, follows relative links and opens the images and PDF pages from disk.
- **Learn from examples:** the Library is in the tree as plain code, so a grep for an API Entry finds the Macros that use it, and a member the Library uses but no page documents is reported as an Undocumented Member rather than as "not found".
- **Start a help session:** the folder is a ready-to-open agent workspace with `AGENTS.md`, `CLAUDE.md`, a `work/` folder and the skills for writing Guides.
- **Use it from a project:** `cst-help instructions` prints the folder path and the `AGENTS.md` section to add to my own project repositories, next to the Control Server.
- **Guides, later:** agent sessions write Guides into the workspace, marked as generated and citing their sources; `validate` checks the citations exist.

There is no server, no database and no ranking (ADR 0014). A client without file access is not supported.

## User Stories

### Building a Knowledge Base

1. As a CST user, I want to point the tool at my CST installation folder, so that I can build a Knowledge Base without copying files around.
2. As a CST user, I want to describe my Knowledge Base in one TOML file (its path, Collections, Sources and preferences), so that a build is repeatable.
3. As a CST user, I want a `cst-release` Source that already knows a release folder's layout (help, manuals, Library) and what to exclude, so that I don't have to configure dozens of paths.
4. As a CST user, I want to build one Collection at a time, so that adding a few PDFs doesn't rebuild a whole Release.
5. As a CST user, I want a new Build to take over only once it is complete, so that a session never reads a half-written folder.
6. As a CST user, I want the build to stop with a clear error when a Source's expected structure isn't recognised, so that I never get a silently empty Collection.
7. As a CST user, I want per-Document failures listed in a build report, with the Knowledge Base marked incomplete in its `AGENTS.md`, so that agents can warn me.
8. As a CST user, I want a `--strict` option that turns any Document failure into a failed build, so that I can insist on a clean result.
9. As a CST user, I want the build report to count discovered, converted, skipped and failed Documents, unresolved links, missing Assets and unsupported items, so that I can see coverage at a glance.
10. As a CST user, I want the build to run fully offline on my Windows laptop's CPU, so that I need neither a GPU nor a network connection.
11. As a CST user, I want to build on one machine and copy the folder to another, so that heavy work can happen wherever it is convenient.
12. As a CST user, I want to add a second Release beside the first as a sibling folder, so that I can keep working with projects from an older version.
13. As a CST user, I want to remove an old Release as a deliberate step, so that nothing disappears by accident.
14. As a CST user, I want to add a release-independent Collection of extra PDFs later, rebuilt from its folder, so that new material joins without touching the Releases.
15. As a CST user, I want `cst-help validate` to check a Knowledge Base's files and links, so that I can trust a copied or old folder.
16. As a colleague with my own CST licence, I want to install the tool and build from my own installation, so that I never need someone else's licensed content.

### Content fidelity

17. As an agent, I want navigation boilerplate removed from every topic (logos, breadcrumb scripts, footers, skin pages), so that pages contain only content.
18. As an agent, I want dialog field lists rendered as field definitions, so that I can tell a field's name from its description.
19. As an agent, I want VBA code samples rendered as real code blocks with their indentation, so that I can copy them.
20. As an agent, I want TeX from the MathJax pages kept exactly as written, so that I can read and quote formulas.
21. As an agent, I want equation images kept as images and marked "not transcribed", so that I know to look at them rather than trust missing text.
22. As an agent, I want simple tables as Markdown and tables with merged cells as HTML, so that no cell associations are lost.
23. As an agent, I want popup links to work as ordinary links, so that I can follow them to the text they show.
24. As an agent, I want commented-out and hidden retired content left out, so that I don't quote text CST no longer shows.
25. As an agent, I want every Document to carry its Release, Area, title, original source path, table-of-contents paths and author keywords in its frontmatter, so that I can grep titles and keywords and cite precisely.
26. As an agent, I want topics that CST published identically in several places to appear once, with the other paths as Aliases, so that greps aren't cluttered with copies.
27. As an agent, I want internal links resolved without regard to case and written relative to the linking file, so that I can follow them in any Markdown viewer.
28. As an agent, I want each PDF manual copied as it is with a text companion that has a `page-<n>` section per page, so that I can grep the text and open the page.
29. As an agent, I want topics outside any table of contents (including the Example Projects) included, so that grep reaches all content.
30. As an agent, I want the breadcrumb paths embedded in topics used as table-of-contents paths where the table of contents has none, so that topics carry their context.
31. As an agent, I want every image as an Asset, deduplicated by content, with BMP and SVG converted to PNG, so that my Read tool can open it.
32. As an agent, I want inline icons kept as small images with readable alt text, and logos and chrome dropped, so that "click this icon" still makes sense.
33. As an agent, I want nothing in the tree that is not for reading: no sidecars, no databases, so that a content grep returns pages.

### API Entries

34. As an agent writing a macro, I want to grep `api.md` for `Solver.FrequencyRange` and get its signature and the path to its heading on one line, so that I don't guess.
35. As an agent, I want a bare member name such as `FrequencyRange` to show every object that has it, labelled by Area, so that I can pick the right one.
36. As an agent, I want same-named objects in different Areas (for example the two "Solver Object" pages and the two "Project Object" pages) kept apart in `api.md` and in the tree, so that I don't mix the 3D and schematic APIs.
37. As an agent, I want WinWrap Basic built-ins (`Left$`, `Begin Dialog`) as API Entries, so that I can check the language as well as the CST objects.
38. As an agent, I want the Python reference's classes, methods, properties and functions as API Entries under their dotted names, so that Python scripts are as checkable as VBA.
39. As an agent, I want the methods that VBA code calls without an object (`AddToHistory`, `SelectTreeItem`) listed under the Application object, so that I find them.
40. As an agent, I want `AGENTS.md` to tell me that a member absent from `api.md` and the VBA pages but present in the Library is an Undocumented Member, so that I use it knowingly and say so.
41. As an agent, I want a member that is neither documented nor used anywhere reported plainly as not documented, so that I don't invent it.

### The Library

42. As a CST user, I want to say "build it like the Farfield Result template" and have the agent find that template by grepping `library.md`, so that it can copy CST's own way of doing things.
43. As an agent, I want the Library's text files in the tree with their original names and folders, so that I grep them like any code.
44. As an agent, I want `library.md` to list each file with its kind, menu path, Display Name, Application Filter, Variants and first comment line, so that loose names still lead to the right file and I prefer the MWS Variant.
45. As an agent, I want `'#include "X"` to point at `library/Includes/X`, and `AGENTS.md` to say that an Include's public procedures are Helpers and not documented CST API Entries, so that I reuse them correctly.
46. As an agent, I want scrambled Macros listed by name and menu path only, so that I know they exist without seeing unreadable content.
47. As an agent, I want the Library's dialog bitmaps as PNG Assets next to the Macros that load them, so that I can see what a dialog shows.
48. As an agent, I want Material Definitions copied as they are and `materials.md` to list each exact name with its base name, so that I find the exact name to put in `.Material "…"`.

### Reading and navigating

49. As an agent, I want `AGENTS.md` under about 12 KB that says what each folder holds, how pages are built, and which grep finds an identifier, a concept, a dialog, a UI location or a figure, so that I know how to look from the first turn.
50. As an agent, I want CST's table of contents as `toc.md` and the author keyword index as `keywords.md`, so that I can start from the vendor's own vocabulary.
51. As an agent, I want descriptive file names and folder names that say what a page is (`special_solvopt_` for dialogs, `special_overview_` for overviews), so that a list of matching files is already a ranking.
52. As an agent, I want the Ribbon Path under a dialog's title, so that I can tell the user where a setting lives.
53. As an agent, I want each Release in its own folder with its own `AGENTS.md` naming the Release, so that I never mix methods from two versions.
54. As an agent, I want `AGENTS.md` to say when the Knowledge Base is incomplete, so that I can warn the user.

### Agent integration

55. As a CST user, I want to open Claude Code, Cursor or Codex in the Knowledge Base folder and start asking, so that a help session needs no setup.
56. As an agent in a help session, I want a `work/` folder that builds never touch, so that I have a safe place for the macros I write.
57. As a CST user, I want `cst-help instructions` to print the folder path and the `AGENTS.md` section for my own repositories, so that project sessions next to the Control Server can consult the Knowledge Base.
58. As a CST user, I want the folder usable on its own, without the Control Server, so that it is useful even when CST isn't running.

### Guides

59. As an agent in a help session, I want skills that tell me how to write a Guide (frontmatter, citations, no vendor text copied), so that Guides are consistent.
60. As an agent, I want Guides listed in `AGENTS.md` and marked as generated, so that I know to verify them against the cited pages.
61. As a CST user, I want `validate` to report Guide citations that point nowhere, so that stale Guides are caught.

### Developing the tool

62. As a developer, I want tests that build from the real corpus and check the files the build wrote, so that the tests measure what users get.
63. As a developer, I want a benchmark of real questions that agents answer from the folder, scored by whether they read an expected Document and in how many calls, so that a build change is judged by what an agent can do with it.

## Implementation Decisions

### Packaging and platform

- **One package.** The install covers the build and the CLI. Serving needs nothing: the folder is the product.
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

  Every Source accepts include and exclude filters, so a Release can be built in parts.
- **CLI commands:** `cst-help build <collection>`, `assemble`, `validate` and `instructions`. The Knowledge Base path is always explicit.

### Collections, Releases and Areas

- **Collections:** `cst-<release>` holds everything shipped with a Release, in the folder `cst-<release>/`. Release-independent Collections are sibling folders.
- **Sessions:** an agent works in one Release folder, whose `AGENTS.md` names the Release (ADR 0005 as amended).
- **Areas of a release Collection:** each is a folder or a set of folders inside the Release folder.

  | Area | Contents |
  |---|---|
  | `general` | General features, user interface, ribbons, advanced, license, simulation acceleration, and the Python menu topics at the help root until the `python` Area exists |
  | `3d` | 3D Simulation |
  | `circuits` | DES |
  | `pcb` | PCB |
  | `filter-designer` | Filter Designer 3D |
  | `chip-interface` | CHI |
  | `vba-3d` | VBA for the 3D modeler, and the root project's VBA overview |
  | `vba-schematic` | VBA_DES |
  | `winwrap-basic` | WinWrap Basic language reference |
  | `python` | Python reference, its RoboHelp overview topic, and the Python menu topics at the help root |
  | `example-projects` | `EXP_*` |
  | `manuals` | Word manuals and release notes, as PDFs with text companions |
  | `library` | Macros, Result Templates, Includes, Material Definitions and Python apps, copied as files |

### Locators

- **The rule** for rendered Documents (ADR 0011):
  - drop the `Online Help/` and `mergedProjects/` prefixes;
  - lowercase every path segment;
  - collapse each run of characters outside `a–z 0–9 . _ - + ^` to one `-`, and trim `-` at segment ends;
  - append `.md` to the full file name.
- **Copied files** (Library code, Material Definitions) keep their original names and folders; their Locator is their path.
- **PDFs** keep their original names in their Area's folder (`manuals/CST Studio Suite - Getting Started.pdf`); their Locator is their Text Companion beside them, the PDF's path with `.md` appended.
- **Collisions** stop the build.
- **Anchors** are the source's own ids where present. Otherwise they're generated: from the member name for API Entries, from headings elsewhere, and `page-<n>` for PDF pages.
- **Original source paths** are always kept in frontmatter.

### The Document model and readers

- **The model** (ADR 0007): readers parse each Source into our own Document model of typed blocks (heading, paragraph, list, field definition, code, table, equation, figure, API signature), and the Markdown is rendered from it, never from raw HTML. The model is not persisted; a build re-parses.
- **RoboHelp reader** (classic WebHelp 5.x):
  - **Navigation data:** reads the table of contents, keyword index and context-help maps from `gXMLBuffer` JS strings by decoding the string escapes, never by running JS. Breadcrumbs come from `addTocInfo`.
  - **Content:** the content runs between the logo header and the footer. A per-project map from CSS class to block role identifies VBA object, category and method headings, dialog fields, code lines and notes. Class names are matched without regard to case, and multi-name headings ("A / B") are split.
  - **TeX:** recognised only on pages that load MathJax, honouring the page's delimiter configuration.
  - **Other markup:** popups become links, and commented-out content is dropped.
- **Sphinx reader:** reads the main content region, takes API Entries from the inventory, and uses entry anchors equal to the qualified names.
- **PDFs:** copied as they are, with a text companion extracted by pypdf, one section per page. A PDF without a text layer is a reported failure. No Docling, no OCR (ADR 0006), no cache.
- **Library:** copied as files, re-encoded from cp1252 to UTF-8. Files are classified by content for the `library.md` line (Macro, Result Template, Include, helper script, Python, Material Definition, scrambled, binary). Display Names come from the folder path plus the file stem before `^`; the Application Filter is parsed; Variants are linked on the index line. Nothing from the Library is executed or imported, and nothing is descrambled.

### Link resolution and Assets

- **Two passes:** first an inventory of every Document, anchor and Alias, then link resolution.
- **Link status:** each link is resolved, unresolved, external, or outside the corpus, and the report lists every unresolved one.
  - **Outside** means the target file exists in the release folder but is no Document of the Build. The report counts outside links by the project or file type they lead to.
  - **Unresolved** means the target exists nowhere in the release folder. Unresolved links never fail a build.
  - A resolved link whose fragment the target's source names nowhere is reported as a missing anchor.
- **Links are written relative to the linking file**, so ordinary Markdown viewers follow them (ticket 26).
- **Assets:** deduplicated by content hash. BMP and SVG become PNG at build time. Each Asset's alt text stays in the page that references it.

### Entry files and workspace

- **Per Release folder:** `toc.md`, `keywords.md`, `api.md` (one API Entry per line: qualified name, Area, signature, path with anchor), `library.md`, `materials.md`.
- **Workspace files written by assembly** (ADR 0013, ADR 0014):
  - `AGENTS.md` under about 12 KB, generated: rules (cite path and Release; "not documented"; Undocumented Member; look at figures), folder table with counts, page anatomy, grep recipes, index files, Guides, incompleteness notice;
  - `CLAUDE.md`, which imports it; a Cursor rule if ticket 25 finds one is needed;
  - the Guide-writing skills, copied into `.claude/skills/` and `.agents/skills/`;
  - `work/` and `guides/` folders that builds never touch.
- **Root of the Knowledge Base:** an `AGENTS.md` listing the Release folders and release-independent Collections, telling a session to stay in one Release.
- **Build report:** written per Build, outside the tree, and summarised by the CLI. Nothing but pages, Assets, copied files and the entry files is written into the tree.

### Builds and assembly

- **Builds** (ADR 0009): each Collection is built into a new, immutable Build directory. Nothing is cached.
- **Assembly** writes the entry files and workspace files from the active Builds, then switches the active pointer atomically.
- **Removing a Release** is an explicit command.

### Guides

- **Authoring:** Guide-writing skills ship in the package, one per topic family. Authoring happens in agent sessions working from the folder, and the tool contains no LLM client (ADR 0010).
- **Checks:** `validate` reports cited Locators that don't exist.
- **Privacy:** Guides stay private with the Knowledge Base.

### Proof of concept, then the rest

- **The proof of concept** is a slice of `cst-2024`:
  - **Areas:** VBA 3D, WinWrap Basic, 3D Simulation, Python, and two Word manuals.
  - **Features:** the Markdown tree with its entry files and the workspace; the agent-run benchmark for those Areas.
  - **Checks:** by hand in Claude Code and Cursor, from a session opened in the folder.
- **Then:**
  - the Library (Macros, Result Templates, Includes, Materials, Python apps);
  - the remaining Areas and all manuals;
  - several Collections and Releases in one Knowledge Base;
  - Codex;
  - Guides.

## Testing Decisions

- **Real data first.** Every development machine has the CST 2024 corpus, so tests build from it and check what users will get.
- **Finding the corpus from any checkout.** `.ingestion/` is gitignored, so a git worktree doesn't contain it. Corpus tests resolve the corpus in this order:
  1. an environment variable naming the release folder, which may be the installation itself;
  2. `.ingestion/<release>/` in the current checkout;
  3. `.ingestion/<release>/` in the repository's main checkout, found through git's common directory.
- **Failing instead of silently skipping.** A configured but missing location is a failure. When nothing is found, corpus tests skip only if an explicit opt-out is set. Every test run reports which corpus it used.
- **Synthetic fixtures stay minimal.** Only for behaviour the corpus can't exercise: Locator collisions; a Source whose structure isn't recognised; a Guide with a missing Locator; a release-independent `pdf-folder` Collection; several Releases in one Knowledge Base; Build immutability and the pointer switch.
- **Two seams:**
  1. **Build, then read the files.** Build a Collection, or a filtered part of one, into a temporary Knowledge Base. Then check the files the build wrote: rendered Markdown, entry files, `AGENTS.md`, the build report. Reader internals are not tested directly.
  2. **Agent run.** `docs/benchmark.toml` holds the questions. A script, or a documented procedure, runs each scorable question from the folder with an agent that has file tools only, and reports the tool calls to the first expected Document. Thresholds: every question reaches an expected Document; median at most 4 calls. The "not in the documentation" question and the client checks stay manual.
- **Good tests check external behaviour:** files and their contents. They never check private data structures.
- **Speed:** tests build filtered parts of a Release and share one Build per test session. Test Knowledge Bases are written to temporary directories, never into the checkout.

## Out of Scope

- A search server, a search index or a ranking of any kind (ADR 0014). A command-line search over FTS5 may return by its own ticket if the agent run shows a need.
- Clients without file access.
- OCR of any kind (ADR 0006).
- Embeddings, hybrid search and reranking.
- Synonym Sets and a usage index: the keyword index and grep do these.
- FEST3D, SPARK3D and IdEM. The design must not prevent adding them later.
- GPU, MPI and licensing documentation.
- Library folders other than Macros, Result Templates, Includes, Materials and Python apps; the `cstapps` GUI framework; PPT and DOC companions; Office and executable files.
- Personal or company macro folders (Global Library Path). These come later, as their own Collection.
- Changes to mcp-cst-studio. A follow-up in that repository.
- Any LLM client inside the tool, and generating Guides during `cst-help build`.
- CI configuration, Linux testing, a hosted service, a GUI, live file watching.

## Further Notes

- **To verify in CST during the proof of concept** (CST 2024 is installed on the development machine):
  - whether `'#include` resolves for code sent through `add_to_history`;
  - whether "Load from Material Library" records the inferred history block;
  - benchmark questions API-05, API-10 and SOL-02.
- **To verify in the clients:** whether Cursor reads `AGENTS.md` and opens images from disk; whether Codex needs anything beyond `AGENTS.md`.
- **Benchmark next steps:** add Library and Materials questions such as "exact name for Rogers RO4350B" and "which copper for a lossy metal".
- **Prior art:** MuziIsabel/CST-Studio-Suite-Help (MIT) is a reference for ideas only. No code is taken from it.
- **Python coverage** is expected to grow in later Releases (2026), so Python benchmark questions should be reviewed for each Release.
