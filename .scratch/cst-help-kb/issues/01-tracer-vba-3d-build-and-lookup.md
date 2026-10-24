# 01: Tracer: VBA 3D build and lookup

**What to build:** A CST user writes a minimal TOML configuration naming a Knowledge Base path and a `cst-2024` Collection whose `cst-release` Source points at a release folder (the installation or `.ingestion/2024`), filtered to the VBA 3D project. `cst-help build cst-2024` turns those topics into Documents, Markdown files and a SQLite index. `cst-help lookup Solver.FrequencyRange` then prints the API Entry with its signature, description and Locator.

This is the thinnest path through every layer: configuration, the RoboHelp reader (VBA pages only), the persisted Document model (ADR 0007), the Locator rule (ADR 0011), Markdown rendering, the exact API Entry table (ADR 0008), the retrieval core and the CLI.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] The configuration is read from TOML. Missing or wrong paths fail with a clear message.
- [ ] VBA 3D topics become Documents in Area `vba-3d`. Their Locators follow ADR 0011, and a Locator collision stops the build.
- [ ] VBA object, category and method headings are recognised by CSS class without regard to case, and multi-name headings ("A / B") are split.
- [ ] Every documented member becomes an API Entry identified by Area plus `Object.Member`, with an anchor generated from the member name.
- [ ] VBA code samples (one paragraph per line) render as fenced code blocks that keep their indentation.
- [ ] Each Markdown file has frontmatter with the Release, Area, title and original source path. The Document model is persisted next to it.
- [ ] `cst-help lookup` ignores case. A bare member name returns every object that has it, and same-titled pages (the two "Solver Object" pages) stay distinct. Methods documented on the Application object ("Project Object") resolve by bare name, for example `AddToHistory`.
- [ ] `cst-help search` finds VBA topics by plain words.
- [ ] A corpus test at the build-then-query seam passes, and benchmark question API-01 resolves through lookup.
- [ ] Corpus tests find the corpus from any checkout, in the order the spec gives: an environment variable naming the release folder, then `.ingestion/<release>/` in the current checkout, then the same in the repository's main checkout. Run from a git worktree with no `.ingestion/`, they still find and use the corpus.
- [ ] A configured corpus location that is missing fails the run. Finding no corpus at all fails too, unless the explicit skip opt-out is set. Every run reports which corpus it used, or that the corpus tier was skipped and why.
- [ ] Test Knowledge Bases are built in temporary directories, never inside the checkout.
