# Experiment: answering the benchmark from files alone, 2026-10-25

Status: done. Input to the decision whether the Knowledge Base needs a search server at all.

## Setup

- Corpus: the development `.kb/cst-2024` (Areas `3d`, `general`, `vba-3d`; 1,516 Markdown pages),
  unchanged. A hand-written `AGENTS.md` of 4.6 KB was added to the folder (appendix below). It
  names the folders, the page anatomy, and grep recipes: identifier → heading grep in `vba_3d/`;
  concept → `keywords.md`, then `toc.md`, then title grep, then body grep.
- Agents: one fresh general-purpose subagent per question, same model as the author of this note
  (Claude Fable 5.1), given only the question text and told to read `AGENTS.md` first and to use
  file tools only (Read, Grep, Glob). No MCP server, no `cst-help` CLI, no Area hint, no short
  queries. Each agent reported its own numbered tool log; counts below are self-reported.
- Questions: the 17 benchmark questions the runner scores on this `.kb` (`docs/benchmark.toml`,
  those whose Areas are built). A hit means the agent read an expected Document of the question.
- Counted: tool calls up to and including the first Read of an expected Document. Call 1 is
  always the `AGENTS.md` read.

## Result

17 of 17 questions reached an expected Document. 7 held-out, 10 tuning; no difference.

| Calls to first expected read | Questions |
|---:|---|
| 3 (AGENTS.md, one grep, read) | API-01, API-02, HOW-01, HOW-02, HOW-03, HOW-04, TERM-01 |
| 4 | API-03, FIG-02, SOL-02, SOL-04, TERM-02, THEO-02 |
| 5 | FIG-01, SOL-01, SOL-03, THEO-01 |

Median 4 calls, maximum 5. Total calls per question ranged from 3 to 11; the long tails were
agents reading a second expected page, opening a figure, or (API-01) hunting for the `Units`
object to make "GHz" explicit, not failures to find the page.

Per question:

| Id | Half | Calls total | First expected read at | Route that found it |
|---|---|---:|---:|---|
| API-01 | tuning | 11 | 3 | heading grep `^### FrequencyRange` |
| API-02 | tuning | 3 | 3 | title grep "Port Object" |
| API-03 | tuning | 4 | 4 | heading grep for Renormalize |
| SOL-01 | held-out | 6 | 5 | heading grep SteadyStateLimit, title grep "Time Domain Solver Parameters" |
| SOL-02 | tuning | 6 | 4 | title grep IESolver, heading grep `^### Start` |
| SOL-03 | held-out | 6 | 5 | keywords.md, toc.md, title grep (batched) |
| SOL-04 | tuning | 8 | 4 | heading grep AR filter |
| HOW-01 | tuning | 3 | 3 | title grep "discrete port" |
| HOW-02 | held-out | 5 | 3 | keywords.md "add space" |
| HOW-03 | held-out | 3 | 3 | keywords.md "parameter sweep" |
| HOW-04 | tuning | 4 | 3 | keywords.md "history list" |
| TERM-01 | held-out | 3 | 3 | heading grep ChangeSolverType (from the AGENTS.md terminology note) |
| TERM-02 | tuning | 5 | 4 | keywords.md "farfield monitor" (agent bridged "radiation pattern" itself) |
| THEO-01 | held-out | 5 | 5 | keywords.md "Q-factor" (two dialog pages first, overview third) |
| THEO-02 | tuning | 6 | 4 | body grep "ludwig" after keywords.md had no entry |
| FIG-01 | held-out | 7 | 5 | keywords.md, toc.md, title grep; figure opened at call 7 |
| FIG-02 | tuning | 5 | 4 | keywords.md "which solver"; figure opened at call 5 |

## Observations

- SOL-01, which the ranker placed at rank 28 and which motivated ticket 28, was found by a title
  grep for "Time Domain Solver Parameters" and answered correctly (`SteadyStateLimit "-50"`). The
  dialog page's Ribbon Path heading did not confuse the agent.
- TERM-02, the one genuine vocabulary gap in the ranker's diagnosis ("radiation pattern" for
  farfield), was bridged by the agent itself at the first grep. No Synonym Set was needed.
- `keywords.md` was the first move in 9 of 17 questions and led to an expected page in 7 of them.
  It is the vendor's own synonym list, and it works as one.
- Both figure questions were answered from the image: the agents opened the PNG with Read and read
  the axes and the k·h dimensions off it. No image tool was involved.
- The `*.json` sidecars showed up in grep results and were ignored because AGENTS.md said so. A
  files-only build should not write them next to the pages.
- The answers themselves looked correct on reading (the author knows CST), but this experiment
  measured retrieval, not answer accuracy; nobody checked each claim against the page.

## Limits

- Self-reported tool logs. The first run used one strong model for all 17 questions; the second
  run below repeats it with Sonnet.
- Full natural-language questions only; the benchmark's short queries and Area-filtered variants
  were not run, because an agent with grep does not issue those.
- 17 questions in three Areas. The Library, Python and PDF Areas are not built, so code Sections,
  Display Names and PDF pages were not tested.

## Second run: Sonnet as the agent model

The same 17 questions, same prompts, same folder and AGENTS.md, with Claude Sonnet as the agent.
Again 17 of 17 reached an expected Document. Median 4 calls to the first expected read in both
runs; Sonnet's worst case was 7 (SOL-04) against Fable's 5.

| Id | Half | Fable: first expected read / total calls | Sonnet: first expected read / total calls |
|---|---|---:|---:|
| API-01 | tuning | 3 / 11 | 3 / 3 |
| API-02 | tuning | 3 / 3 | 4 / 4 |
| API-03 | tuning | 4 / 4 | 3 / 3 |
| SOL-01 | held-out | 5 / 6 | 4 / 8 |
| SOL-02 | tuning | 4 / 6 | 4 / 7 |
| SOL-03 | held-out | 5 / 6 | 3 / 3 |
| SOL-04 | tuning | 4 / 8 | 7 / 7 |
| HOW-01 | tuning | 3 / 3 | 3 / 3 |
| HOW-02 | held-out | 3 / 5 | 4 / 5 |
| HOW-03 | held-out | 3 / 3 | 3 / 3 |
| HOW-04 | tuning | 3 / 4 | 3 / 3 |
| TERM-01 | held-out | 3 / 3 | 4 / 5 |
| TERM-02 | tuning | 4 / 5 | 5 / 5 |
| THEO-01 | held-out | 5 / 5 | 4 / 4 |
| THEO-02 | tuning | 4 / 6 | 4 / 6 |
| FIG-01 | held-out | 5 / 7 | 5 / 6 |
| FIG-02 | tuning | 4 / 5 | 5 / 6 |

Distribution of the call at which the first expected page was read:

| Call | Fable | Sonnet |
|---:|---:|---:|
| 3 | 7 | 6 |
| 4 | 6 | 7 |
| 5 | 4 | 3 |
| 7 | 0 | 1 |

What differed:

- Sonnet's `keywords.md` greps missed more often ("free space", "ludwig", "accuracy",
  "electrically large" have no index entry) and it recovered each time with a title or body grep,
  as AGENTS.md says to. The recovery cost one call.
- SOL-04 is the one detour: a content grep for "AR filter" across `vba_3d/` returned a truncated
  list polluted by `*.json` sidecars, and Sonnet read the post-processing `Arfilter` object and
  `PostProcess1D` before the `Solver` object. An `api.md` index (one line per API Entry) would
  have answered "which object has an AR-filter switch" in one grep. Dropping the sidecars from a
  files-only build removes the pollution.
- Sonnet was more literal and more cautious in its answers (it flagged the `"Surface"` versus
  `"Surface Mesh"` inconsistency on the FDSolver page, and that the Solver page does not name a
  frequency unit). All 17 answers named the right call or setting; none invented a method.
- Sonnet runs took 15 to 33 seconds each; Fable runs 35 to 88 seconds.

Conclusion: on these questions the result does not depend on the model. The folder, the vendor's
own indexes and a 4.6 KB AGENTS.md carry it.

## Appendix: the AGENTS.md used

```markdown
# CST Studio Suite 2024 help, as files

This folder is the CST Studio Suite help of Release 2024, converted to Markdown. Nothing here is
generated by a model; every page is the vendor's text. Use your own file tools: grep, glob, read.
There is no search server. Ignore every `*.json` file (build sidecars) and the `assets/` folder
except when you want to look at an image.

## Rules

- Cite the file path (the Locator) and "Release 2024" of every page you rely on.
- If an identifier is in no page under `vba_3d/`, say it is not documented in Release 2024. Never
  invent a method, its arguments or its behaviour.
- Some answers are only in a figure. Open the image file with your Read tool; equation images are
  not transcribed, so look rather than guess.
- Read the page before answering from a grep snippet. Pages are short; most are under 10 KB.

## What is where

| Folder | Pages | Content |
|---|---:|---|
| `3d/` | 1,087 | 3D simulation help: solver dialogs, overviews, theory, post-processing, modelling |
| `vba_3d/` | 345 | VBA object reference: one page per object, one `###` heading per method or property |
| `general/`, `userinterface/`, `ribbons/`, `advanced/`, `license/`, `simulation_acceleration/` | 79 | Product overview, dialogs of the main window, ribbon pages, command line, environment variables |
| `toc.md` | | CST's table of contents, as a nested list of links |
| `keywords.md` | | CST's author keyword index: the authors' own terms, each linking to the pages it means |
| `assets/` | | Images, named by hash; pages link to them |

Folder names inside `3d/` say what a page is: `special_solvopt_*` solver and setup dialogs,
`special_overview_*` overviews and theory, `special_postpr_*` post-processing, `special_process_*`
parameter sweeps and optimisation, `common_*` shared across products, `special_theory_*` theory.
Inside `vba_3d/`, `special_vba<topic>/..._object.htm.md` is one VBA object (for example
`special_vbasolver/special_vbasolver_solver_object.htm.md` is the `Solver` object) and
`common_vbaapp/` holds the application-level objects.

## Page anatomy

- Frontmatter: `title`, `area`, `source`, and when CST gave them, `keywords` (author index terms)
  and `toc_paths` (where the page sits in the table of contents).
- Dialog pages: the `## ` line right under the title is the Ribbon Path, where the dialog is
  reached in the CST ribbon, such as `Simulation: Solver > Setup Solver`. Dialog frames are bold
  lines and their fields are definition items under them.
- VBA pages: `## General Methods`, `## Queries` and similar groups, then `### MethodName` with a
  ```vba signature block and the description. Links between pages are relative to this folder.

## Recipes

**An identifier** (`Solver.FrequencyRange`, a bare `FrequencyRange`, an object name):
grep the method as a heading, case-insensitively, in `vba_3d/`: `^### FrequencyRange`. For an
object, grep its title: `^title: "Solver Object`. Then read the page or the heading's section.

**A concept or how-to question** ("time domain solver accuracy", "how do I define a discrete
port"): work from the vendor's own vocabulary outward.
1. Grep `keywords.md` for your main noun, case-insensitively. The index terms are the authors'
   synonyms; "Transient Solver Parameters" points at the time domain solver dialog.
2. Grep `toc.md` the same way to see the neighbourhood of pages.
3. Grep titles: `^title:.*discrete port` across `3d/`.
4. Only then grep bodies, with the two or three most specific words, listing files only, and
   narrow by a second word. Prefer pages whose title or Ribbon Path matches over pages that
   merely mention the words.
Read the one or two most likely pages. The defining page is usually the dialog
(`special_solvopt_*`) for settings, and the overview (`special_overview_*`) for concepts.

**Where a setting lives in the UI**: it is the Ribbon Path line of the dialog page.

**Which VBA call does what a dialog does**: find the dialog page in `3d/`, then grep the dialog's
title words in `vba_3d/` titles; dialog and object usually share a name (Solver Parameters ↔
`Solver Object`, Port ↔ `Port Object`).

**Theory and equations**: `special_overview_*` and `special_theory_*` pages in `3d/`. TeX is
inline as `$…$` or `\begin{equation}`; where an equation is an image, open it.

**Terminology**: CST says "transient" and "time domain" for the same solver, "farfield" for
radiation patterns, "monitor" for a field recording, "port" for excitation; the VBA `Solver`
object is the time domain solver, `FDSolver` the frequency domain solver.
```
