# 29: Markdown-only build

**What to build:** The tool builds a folder and nothing else (ADR 0014). The MCP server, the SQLite index, retrieval, the benchmark runner and the query log leave the package; the JSON sidecars leave the tree. What remains is the reader, the Markdown tree with its entry files, build, assemble, validate and instructions. The benchmark becomes an agent run from the folder, with a small script that reports the results.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `server.py`, `retrieval.py`, `index.py`, `benchmark.py`, `querylog.py` and `reading.py` are deleted, with their tests, and the `mcp` dependency is removed. The CLI keeps `build`, `assemble`, `validate` and `instructions`; `search`, `lookup`, `browse`, `read`, `serve`, `benchmark` and `benchmark-drafts` go.
- [ ] A Build writes no `*.json` next to the pages. The build manifest, report and navigation data stay in the Build directory root, outside the tree that agents read. `assets.json` moves there too.
- [ ] Assembly writes no database. It writes the entry files (`toc.md`, `keywords.md`) and the workspace files of ticket 15, and switches the active pointer as before. `validate` checks files and links, not an index.
- [ ] `cst-help instructions` prints the Knowledge Base path and an `AGENTS.md` section for a project repository that says to add the folder to the session and how to navigate it (the recipes of `AGENTS.md`), with no MCP entry.
- [ ] `docs/benchmark.toml` loses its `baseline` fields and the runner comments; it keeps questions, halves, Areas, short queries, API Entries and sources. `docs/benchmark-draft.md` describes the agent run as the scoring method.
- [ ] `scripts/agent-run.py`, or a documented procedure under `docs/agents/`, takes the question set and an agent command, runs each scorable question from the folder with file tools only, and reports per question the tool calls to the first expected Document, as `../files-only-experiment.md` did by hand. Thresholds are set from the recorded runs: every scorable question reaches an expected Document, median at most 4 calls.
- [ ] The 17 questions of the experiment pass from a fresh build of the development `.kb` with the hand-written `AGENTS.md` copied in, with counts no worse than the recorded runs.
- [ ] `README.md` says what the tool produces and how to open the folder in Claude Code, Codex and Cursor.

## Comments

**2026-10-25.** Written from the files-only experiment, which answered all 17 scorable questions from the tree with grep and read alone, under two models. The sidecars showed up in content greps and once sent an agent on a detour (SOL-04 under Sonnet), which is why they leave the tree rather than being told apart in `AGENTS.md`.
