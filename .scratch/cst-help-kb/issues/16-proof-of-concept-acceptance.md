# 16: Proof-of-concept acceptance

**What to build:** The proof-of-concept slice of `cst-2024` is built from the real corpus and accepted as a folder: Areas `vba-3d`, `winwrap-basic`, `3d`, `general` and `python`, plus the two Word manuals, with the entry files and the workspace.

**Blocked by:** 10, 11, 12, 13, 15, 29

**Status:** done

- [x] The full slice builds without errors, and the build report is reviewed.
- [x] The agent run (ticket 29) covers every question whose Areas are built, from the generated `AGENTS.md`. Every question reaches an expected Document. The per-question counts are recorded in this ticket, per half and per category, and the thresholds in `docs/benchmark-draft.md` are confirmed or adjusted from them.
- [x] Manual checks in Claude Code and in Cursor from a session opened in the folder: an identifier, a how-to, a figure (visible to the model from disk), and NODOC-01, where the agent says the item is not documented.
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

**2026-10-25, criterion 2.** The user ruled REL-01 an inappropriate test for this ticket: it needs the Release Notes, one of the PDFs left to ticket 21, and is not a question about the slice. With it out, every question the slice covers reached an expected Document (26 of 26, median 3, maximum 5), which ticks criterion 2. REL-01 is scored again once ticket 21 builds the Release Notes. The ticket stays open on criterion 3, the manual checks in Claude Code and Cursor.

**2026-10-25, manual checks, closed.** The user accepted all four manual checks in Claude Code and Cursor, from sessions opened in the folder: an identifier (API-01), a how-to (HOW-04), a figure (FIG-01) and NODOC-01. That ticks criterion 3. The verify-in-CST items of criterion 4 remain open as recorded above.

**2026-10-26, full agent run (ticket 21).** All of `cst-2024` is built: build `20261026T112357209944Z-73ae`, 4,246 Documents (168 Aliases), 7,388 API Entries, 4,663 Assets, 0 failed, `validate` clean, `AGENTS.md` 10.6 KB. The setup is the same as above. Every question in the benchmark can now be run, 40 of them; NODOC-01 is scored by hand. Result: 38 of 40, median 3, maximum 11, FAIL on two misses.

| Id | Half | First expected read / total calls | 2026-10-25 run |
|---|---|---:|---:|
| API-01 | tuning | 3 / 3 | 3 |
| API-02 | tuning | 3 / 3 | 3 |
| API-03 | tuning | 3 / 3 | 2 |
| API-04 | held-out | 3 / 5 | |
| API-05 | held-out | 3 / 10 | |
| API-06 | held-out | 3 / 9 | 3 |
| API-07 | tuning | 3 / 4 | 2 |
| API-08 | held-out | 2 / 4 | 3 |
| API-09 | held-out | 5 / 5 | 5 |
| API-10 | tuning | 3 / 4 | 3 |
| SOL-01 | held-out | 5 / 6 | 5 |
| SOL-02 | tuning | 3 / 12 | 3 |
| SOL-03 | held-out | 3 / 5 | 3 |
| SOL-04 | tuning | 3 / 5 | 5 |
| HOW-01 | tuning | 2 / 3 | 2 |
| HOW-02 | held-out | 4 / 5 | 3 |
| HOW-03 | held-out | 2 / 3 | 2 |
| HOW-04 | tuning | 3 / 3 | 3 |
| TERM-01 | held-out | 4 / 5 | 3 |
| TERM-02 | tuning | 4 / 4 | 4 |
| TERM-03 | tuning | 3 / 7 | |
| THEO-01 | held-out | 4 / 4 | 3 |
| THEO-02 | tuning | 4 / 4 | 4 |
| LINK-01 | held-out | 3 / 5 | 3 |
| LINK-02 | tuning | 3 / 6 | 2 |
| FIG-01 | held-out | 5 / 8 | 3 |
| FIG-02 | tuning | miss, 6 calls | 2 |
| FIG-03 | held-out | 3 / 17 | |
| PDF-01 | tuning | 5 / 7 | 3 |
| PDF-02 | held-out | 4 / 5 | 5 |
| EXP-01 | held-out | 3 / 4 | |
| EXP-02 | tuning | 2 / 4 | |
| REL-01 | tuning | 6 / 7 | miss |
| LIB-01 | held-out | 2 / 9 | |
| LIB-02 | held-out | miss, 14 calls | |
| LIB-03 | tuning | 6 / 7 | |
| LIB-04 | held-out | 11 / 18 | |
| LIB-05 | tuning | 5 / 13 | |
| LIB-06 | tuning | 2 / 2 | |
| LIB-07 | held-out | 2 / 3 | |

Per half: tuning 19 of 20, median 3; held-out 19 of 20, median 3. By category: exact API lookup 10 of 10 (median 3), solver-specific 4 of 4 (3), how-to and UI 4 of 4 (2.5), terminology mismatch 3 of 3 (4), theory and equations 2 of 2 (4), crosslink 2 of 2 (3), figure matters 2 of 3 (4), PDF manuals 2 of 2 (4.5), Example Projects 2 of 2 (2.5), release notes 1 of 1 (6), Library 6 of 7 (3.5).

The misses:
- FIG-02 took the manual route of the concept recipe (step 5). It answered from the High Frequency manual, pages 68–69, which has its own solver-choice diagrams. It never opened the expected help page, `special_overview_whichsolver.htm`. The manual was in the slice before, so this is the agent's choice of route, not a change from ticket 21.
- LIB-02, which asks for the farfield-source Result Template, grepped `keywords.md`, `api.md`, `3d/` and `vba_3d/`. It never opened `library.md` or `library/`. It answered from the help instead: the Field Monitor's "Export farfield source" option (`Monitor.ExportFarfieldSource`) for the automatic export, and `FarfieldPlot.ASCIIExportAsSource` for a manual one. That answer is sound, but it never names the Result Template. In ticket 17's run, LIB-02 hit at call 7. Nothing in ticket 21 touches the Library recipe, so this is the agent's choice of route.

The run also flagged "call 1 was not the AGENTS.md read" on every question. Claude Code loads `CLAUDE.md`, which includes `AGENTS.md`, so the agents no longer read it with a tool call.

**2026-10-26, LIB-02 ruled.** The user accepts the LIB-02 miss. A user who wants an export after every run is expected to know about post-processing templates and to ask for one, so the recipes need no cue that sends such questions to the Library. The answer the agent gave from the help, the Field Monitor's "Export farfield source" option, is sound.
