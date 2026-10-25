# 29: Markdown-only build

**What to build:** The tool builds a folder and nothing else (ADR 0014). The MCP server, the SQLite index, retrieval, the benchmark runner and the query log leave the package; the JSON sidecars leave the tree. What remains is the reader, the Markdown tree with its entry files, build, assemble, validate and instructions. The benchmark becomes an agent run from the folder, with a small script that reports the results.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] `server.py`, `retrieval.py`, `index.py`, `benchmark.py`, `querylog.py` and `reading.py` are deleted, with their tests, and the `mcp` dependency is removed. The CLI keeps `build`, `assemble`, `validate` and `instructions`; `search`, `lookup`, `browse`, `read`, `serve`, `benchmark` and `benchmark-drafts` go.
- [x] A Build writes no `*.json` next to the pages. The build manifest, report and navigation data stay in the Build directory root, outside the tree that agents read. `assets.json` moves there too.
- [x] Assembly writes no database. It writes the entry files (`toc.md`, `keywords.md`) and the workspace files of ticket 15, and switches the active pointer as before. `validate` checks files and links, not an index.
- [x] `cst-help instructions` prints the Knowledge Base path and an `AGENTS.md` section for a project repository that says to add the folder to the session and how to navigate it (the recipes of `AGENTS.md`), with no MCP entry.
- [x] `docs/benchmark.toml` loses its `baseline` fields and the runner comments; it keeps questions, halves, Areas, short queries, API Entries and sources. `docs/benchmark-draft.md` describes the agent run as the scoring method.
- [x] `scripts/agent-run.py`, or a documented procedure under `docs/agents/`, takes the question set and an agent command, runs each scorable question from the folder with file tools only, and reports per question the tool calls to the first expected Document, as `../files-only-experiment.md` did by hand. Thresholds are set from the recorded runs: every scorable question reaches an expected Document, median at most 4 calls.
- [ ] The 17 questions of the experiment pass from a fresh build of the development `.kb` with the hand-written `AGENTS.md` copied in, with counts no worse than the recorded runs.
- [x] `README.md` says what the tool produces and how to open the folder in Claude Code, Codex and Cursor.

## Comments

**2026-10-25.** Written from the files-only experiment, which answered all 17 scorable questions from the tree with grep and read alone, under two models. The sidecars showed up in content greps and once sent an agent on a detour (SOL-04 under Sonnet), which is why they leave the tree rather than being told apart in `AGENTS.md`.

**2026-10-25.** Implemented. Criterion 3: assembly writes `toc.md` and `keywords.md` into the Release folder; the workspace files themselves are ticket 15, which is blocked by this one, so they are not written yet. `validate` resolves links against the Release folder root, as the renderer writes them; ticket 26 changes both to page-relative links. `scripts/agent-run.py` counts any read of a PDF companion as a hit until a PDF Area exists.

Criterion 7 is not met. Fresh build of the development `.kb` (1,514 Documents, no `*.json` in the folder, `validate` clean), the experiment's `AGENTS.md` copied in, Claude Code 2.1.310 with `--model sonnet`, Read/Grep/Glob only, scored by `scripts/agent-run.py`:

| Id | First expected read / total calls | Recorded Sonnet run |
|---|---:|---:|
| API-01 | 3 / 3 | 3 / 3 |
| API-02 | 3 / 3 | 4 / 4 |
| API-03 | 3 / 3 | 3 / 3 |
| SOL-01 | 4 / 9 | 4 / 8 |
| SOL-02 | 4 / 6 | 4 / 7 |
| SOL-03 | 4 / 6 | 3 / 3 |
| SOL-04 | 4 / 5 | 7 / 7 |
| HOW-01 | 3 / 4 | 3 / 3 |
| HOW-02 | 4 / 5 | 4 / 5 |
| HOW-03 | 3 / 4 | 3 / 3 |
| HOW-04 | 4 / 4 | 3 / 3 |
| TERM-01 | 4 / 4 | 4 / 5 |
| TERM-02 | 5 / 5 | 5 / 5 |
| THEO-01 | 4 / 5 | 4 / 4 |
| THEO-02 | miss / 4 | 4 / 6 |
| FIG-01 | 6 / 7 | 5 / 6 |
| FIG-02 | 3 / 9 | 5 / 6 |

16 of 17 hits, median 4, maximum 6. SOL-04, the sidecar detour of the recorded run, dropped from 7 to 4. THEO-02 hit in one of three runs (call 4). In the two misses the agent grepped `Ludwig` with context in `3d/special_postpr/`, got the expected page's text in the snippets, and answered correctly with that page cited, without reading it, against the `AGENTS.md` rule to read before answering. SOL-03, HOW-04, TERM-01 and FIG-01 also took one call more than the recorded run. Open: whether a snippet answer from an expected page counts, or ticket 15's `AGENTS.md` should press the read harder.

