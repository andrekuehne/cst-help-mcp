# 16: Proof-of-concept acceptance

**What to build:** The proof-of-concept slice of `cst-2024` is built from the real corpus and accepted as a folder: Areas `vba-3d`, `winwrap-basic`, `3d`, `general` and `python`, plus the two Word manuals, with the entry files and the workspace.

**Blocked by:** 10, 11, 12, 13, 15, 29

**Status:** ready-for-agent

- [x] The full slice builds without errors, and the build report is reviewed.
- [ ] The agent run (ticket 29) covers every question whose Areas are built, from the generated `AGENTS.md`. Every question reaches an expected Document. The per-question counts are recorded in this ticket, per half and per category, and the thresholds in `docs/benchmark-draft.md` are confirmed or adjusted from them.
- [ ] Manual checks in Claude Code and in Cursor from a session opened in the folder: an identifier, a how-to, a figure (visible to the model from disk), and NODOC-01, where the agent says the item is not documented.
- [x] The verify-in-CST items are checked or recorded as open: API-05, API-10, SOL-02, and whether `'#include` resolves for code sent through `add_to_history`.

## Comments

**2026-10-25.** Rewritten for ADR 0014. The earlier version set thresholds on ranker scores and planned a tuning pass; both went with the ranker. The experiment that replaced them is `../files-only-experiment.md`.

**2026-10-25.** Run against a fresh build of the development `.kb` (`uv run cst-help build cst-2024`).

Criterion 1. The build is `20261025T154517156215Z-7d8d`. It has 1,840 Documents (46 of them Aliases), 6,510 API Entries and 2,027 Assets. 2,492 files were discovered, 1,886 converted and 606 skipped; 0 failed and 0 had unpaired math. `validate` is clean, `AGENTS.md` is 7.8 KB, and there is no `*.json` in the Release folder. Reviewed report items:
- 7 unresolved links and 7 missing anchors. All of them are defects in the corpus: the targets are not in the installation. These are `general/printed_documentation.htm`, `cst_studio_suite_examples_overview.htm`, the getting-started `Videos/`, a `+Selected_Segments` link in the cable harness page, `#Mesh_Control_Regions` (the page defines `Mesh_Control_Items`), and `#ThermalConductionOnly` and `#TurbulenceModel` in the CHT solver page, which never defines them.
- 89 links point outside the slice, into Areas not built yet: DES, EXP_*, PCB, Filter Designer, SPARK3D, FEST3D, and downloadable files such as `.ffs`, `.zip` and `.txt`. 249 unsupported items are mostly `.js` (207), with `.xml`, `.css` and similar.
- Navigation: 691 table-of-contents entries and 2,003 keywords were kept; 571 entries and 1,071 keyword topics were dropped because they point outside the slice.
- `.kb/index.sqlite` is left over from before ticket 29. It sits outside the Release folder and nothing reads it.

`api.md`: every API Entry of the scorable API questions has a line pointing at its first expected source. Three of them are listed under other names: `Print #` is `Print`, and `AddToHistory` and `ChangeSolverType` are `Project.AddToHistory` and `Project.ChangeSolverType`.

Criterion 2. The setup matches ticket 15: the generated `AGENTS.md`, Claude Code 2.1.310 with `--model sonnet`, Read/Grep/Glob only, scored by `scripts/agent-run.py`. On Windows the command must name `claude.cmd` by its full path, because `subprocess` does not find the bare `claude` shim. The report now breaks the counts down by category, and it prints a line for a question that has no expected Document in the folder. Before, such a question was counted silently. Result: 26 of 27, median 3, maximum 5, FAIL on the one miss:

| Id | Half | First expected read / total calls | Ticket 15 run |
|---|---|---:|---:|
| API-01 | tuning | 3 / 3 | 3 |
| API-02 | tuning | 3 / 3 | 3 |
| API-03 | tuning | 2 / 2 | 3 |
| API-06 | held-out | 3 / 7 | |
| API-07 | tuning | 2 / 2 | |
| API-08 | held-out | 3 / 4 | |
| API-09 | held-out | 5 / 7 | |
| API-10 | tuning | 3 / 6 | |
| SOL-01 | held-out | 5 / 7 | 4 |
| SOL-02 | tuning | 3 / 10 | 3 |
| SOL-03 | held-out | 3 / 5 | 3 |
| SOL-04 | tuning | 5 / 5 | 5 |
| HOW-01 | tuning | 2 / 3 | 2 |
| HOW-02 | held-out | 3 / 4 | 3 |
| HOW-03 | held-out | 2 / 3 | 2 |
| HOW-04 | tuning | 3 / 3 | 3 |
| TERM-01 | held-out | 3 / 5 | 5 |
| TERM-02 | tuning | 4 / 4 | 5 |
| THEO-01 | held-out | 3 / 4 | 4 |
| THEO-02 | tuning | 4 / 4 | 2 |
| LINK-01 | held-out | 3 / 4 | |
| LINK-02 | tuning | 2 / 3 | |
| FIG-01 | held-out | 3 / 6 | 5 |
| FIG-02 | tuning | 2 / 12 | 3 |
| PDF-01 | tuning | 3 / 5 | |
| PDF-02 | held-out | 5 / 6 | |
| REL-01 | tuning | miss: no expected Document in the folder | |

Per half: tuning 14 of 15, median 3; held-out 12 of 12, median 3.

| Category | Hits | Median |
|---|---:|---:|
| Exact API lookup | 8 of 8 | 3 |
| Solver-specific | 4 of 4 | 4 |
| How-to and UI | 4 of 4 | 2.5 |
| Terminology mismatch | 2 of 2 | 3.5 |
| Theory and equations | 2 of 2 | 3.5 |
| Crosslink to follow | 2 of 2 | 2.5 |
| Figure matters | 2 of 2 | 2.5 |
| PDF manuals | 2 of 2 | 4 |
| Release notes | 0 of 1 | |

Calls to the first expected read: 2 in 6 questions, 3 in 14, 4 in 2, 5 in 4.

REL-01 asks about the Release Notes PDF. Its Area `manuals` is built, but the slice holds only the two Word manuals, so the agent never ran and the question could not be a hit. It becomes scorable with ticket 21. Every question the slice can answer was a hit. The thresholds in `docs/benchmark-draft.md` are kept unchanged: every scorable question a hit, median at most 4. The run fails them only through REL-01. Its median is 3, no category's median is above 4, and no question took more than 5 calls. Of the 17 questions that ticket 15 ran, SOL-01 took one call more and THEO-02 two more; seven took fewer. Open: whether REL-01 counts as out of the slice for this criterion, which would tick it.

Criterion 3. Not done. The interactive checks in Claude Code and Cursor are the user's to do. One headless pre-check was run: `claude -p --model sonnet` from the Release folder, with file tools only, answering NODOC-01. It passed. The agent said that Release 2024 documents no VBA call that selects TLM or the Hexahedral TLM mesh, and invented no value. It cited the `MeshType` values, the `ChangeSolverType` types and the dialog page. It noted that `ParameterSweep.SetSimulationType "TLM"` sets only a sweep's simulation type, and it pointed to the GUI route and the macro recorder.

Criterion 4. Recorded as open. They need CST, which this run did not have:
- API-05: `Block.SetDoubleProperty` on a schematic block. The `vba-schematic` Area is not in the slice either.
- API-10: whether two `add_to_history` calls with the same header keep both history blocks.
- SOL-02: whether the integral equation solver is started through `FDSolver` (`SetMethod`) or `IESolver`.
- Whether `'#include` resolves for code sent through `add_to_history`.
