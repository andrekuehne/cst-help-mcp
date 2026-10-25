# 01: Tracer: VBA 3D build and lookup

**What to build:** A CST user writes a minimal TOML configuration naming a Knowledge Base path and a `cst-2024` Collection whose `cst-release` Source points at a release folder (the installation or `.ingestion/2024`), filtered to the VBA 3D project. `cst-help build cst-2024` turns those topics into Documents, Markdown files and a SQLite index. `cst-help lookup Solver.FrequencyRange` then prints the API Entry with its signature, description and Locator.

This is the thinnest path through every layer: configuration, the RoboHelp reader (VBA pages only), the persisted Document model (ADR 0007), the Locator rule (ADR 0011), Markdown rendering, the exact API Entry table (ADR 0008), the retrieval core and the CLI.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] The configuration is read from TOML. Missing or wrong paths fail with a clear message.
- [x] VBA 3D topics become Documents in Area `vba-3d`. Their Locators follow ADR 0011, and a Locator collision stops the build.
- [x] VBA object, category and method headings are recognised by CSS class without regard to case, and multi-name headings ("A / B") are split.
- [x] Every documented member becomes an API Entry identified by Area plus `Object.Member`, with an anchor generated from the member name.
- [x] VBA code samples (one paragraph per line) render as fenced code blocks that keep their indentation.
- [x] Each Markdown file has frontmatter with the Release, Area, title and original source path. The Document model is persisted next to it.
- [x] `cst-help lookup` ignores case. A bare member name returns every object that has it, and same-titled pages (the two "Solver Object" pages) stay distinct. Methods documented on the Application object ("Project Object") resolve by bare name, for example `AddToHistory`.
- [x] `cst-help search` finds VBA topics by plain words.
- [x] A corpus test at the build-then-query seam passes, and benchmark question API-01 resolves through lookup.
- [x] Corpus tests find the corpus from any checkout, in the order the spec gives: an environment variable naming the release folder, then `.ingestion/<release>/` in the current checkout, then the same in the repository's main checkout. Run from a git worktree with no `.ingestion/`, they still find and use the corpus.
- [x] A configured corpus location that is missing fails the run. Finding no corpus at all fails too, unless the explicit skip opt-out is set. Every run reports which corpus it used, or that the corpus tier was skipped and why.
- [x] Test Knowledge Bases are built in temporary directories, never inside the checkout.

## Comments

**Implemented (2026-10-24).** All criteria are covered by 28 tests (`uv run pytest`). The worktree case was checked by hand: a git worktree with no `.ingestion/` reported "via main checkout" and passed. The full VBA 3D Area builds in about 4 s, giving 372 Documents and 5,539 API Entries.

Decisions for later tickets:

- **Layout.** The Markdown for a Collection is written to `<kb>/<collection>/<locator>`. The persisted model sits next to it as `<locator>.json`. One `<kb>/index.sqlite` holds every Collection, with a column saying which one each row belongs to. The build writes to a staging folder, indexes, then swaps the folder in. Ticket 03 replaces this with immutable Builds and a pointer switch.
- **Configuration.**
  - Relative paths resolve against the folder of the config file.
  - A collection without `release` takes it from its name (`cst-<release>`).
  - Source `include`/`exclude` patterns are case-insensitive globs, matched against the path relative to the release folder.
- **Object names.** An object's name comes from its heading: drop " Object" and any parenthetical, then join the words (`Coil Group Object` becomes `CoilGroup`).
  - Global methods live on the 3D "Project Object" (`Project.AddToHistory`). `Application.<member>` also resolves to it.
  - A page that documents no members, such as a ribbon page, gets no API Entry.
- **Member headings.**
  - A member heading whose parenthesis is still open continues into the next one (wrapped signatures).
  - A heading with prose words before the parameter list stays a paragraph.
- **Anchors.** Member anchors are generated from the member name; repeats get `-2`, `-3`. A category keeps its source anchor only when that is a valid fragment, so `General Methods` gets a generated anchor.
- **Search.** The query's words are OR-ed and ranked by BM25 over title, headings and body. Ticket 06 owns ranking.
- **Tests.** The corpus variables are `CST_HELP_CORPUS_2024` and `CST_HELP_SKIP_CORPUS=1`.
- **Open points from review.**
  - Tables with merged cells still render as Markdown, not HTML; this belongs to ticket 04.
  - Hyperlinks inside paragraphs are reduced to their text; ticket 04 resolves links.
