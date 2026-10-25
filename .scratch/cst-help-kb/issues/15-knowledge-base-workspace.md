# 15: Knowledge Base workspace

**What to build:** Every assembly makes the Knowledge Base folder a ready-to-open agent workspace (ADR 0013, ADR 0014). Opening Claude Code, Codex or Cursor there is all the setup there is. The generated `AGENTS.md` carries the navigation recipes that the experiment's hand-written one proved, with real counts and the Areas actually built.

**Blocked by:** 29

**Status:** done

- [x] `AGENTS.md` stays under about 8 KB and is generated from the hand-written one in `../files-only-experiment.md`: the rules (first and in bold, that grep finds pages and never answers: open every cited page with the read tool before answering, even when the grep lines seem to hold the answer, and grep bodies without context lines; cite the path and the Release; "not documented" means not in `vba_3d/` and not in the Library; an Undocumented Member is one the Library uses but no page documents; look at figures), the table of folders with page counts, the page anatomy, the recipes (identifier, concept, UI location, dialog to VBA object, theory, terminology), and the list of index files and Guides.
- [x] `api.md` lists every API Entry one per line: qualified name, Area, signature, path with anchor. It is the exact table, meant for grep.
- [x] `CLAUDE.md` imports `AGENTS.md`. A `.cursor/rules/` file does the same for Cursor if ticket 25 finds that Cursor does not read `AGENTS.md` by itself.
- [x] A `work/` folder for what agents write and a `guides/` folder for Guides (ticket 24) exist, and builds and assemblies never touch them.
- [ ] Manual check: Claude Code opened in the folder answers API-01 and HOW-04 from the generated `AGENTS.md` without being told where anything is.
- [x] `scripts/agent-run.py` passes from a fresh build with the generated `AGENTS.md` (Claude Code, `--model sonnet`): 17 of 17, median at most 4, and per question no worse than the 2026-10-25 run with the strengthened hand-written one (ticket 29's comments). That closes ticket 29's criterion 7.

## Comments

**2026-10-25.** Rewritten for ADR 0014: no MCP configuration is written. The hand-written `AGENTS.md` that this ticket generalises is appended to `../files-only-experiment.md`.

**2026-10-25.** From ticket 29's agent run: with the experiment's wording ("Read the page before answering from a grep snippet", last in the rules), Sonnet answered THEO-02 from `grep -C` snippets without opening the page in two of three runs. Moved to the top of the rules and put as "**Grep finds pages; it never answers.** Before you answer, open every page you cite with your Read tool, even when the grep lines already seem to hold the answer. A snippet leaves out the conditions, figures and exceptions around it.", with the body-grep recipe saying "no context lines; then read the best match", THEO-02 hit in three of three runs and the full run scored 17 of 17, median 4. `cst-help instructions` already carries this wording (`instructions.RULES`); generate `AGENTS.md` from the same constants.

**2026-10-25.** Implemented. Assembly writes `api.md`, `AGENTS.md` and `CLAUDE.md` into each Release folder and creates `work/` and `guides/`. Every new view takes those two folders over from the old one, including from a view an interrupted assembly left behind, and never writes into them. The build keeps its API Entries in `api.json` beside the tree, as it does the navigation data. `AGENTS.md` (5.4 KB on the development `.kb`) and the `cst-help instructions` section are generated from the same rules, anatomy and recipes in `instructions.py`. The identifier recipe now starts with `api.md`. The "not documented" and Undocumented Member rules name `library/` only once that folder exists. `validate` skips links in `work/`, but not in `guides/` (ticket 24). In `api.md` the path is code, not a link, which keeps grep lines short. The file is 0.9 MB for 5,539 API Entries, and `AGENTS.md` says to grep it, not read it. The Cursor rule waits for ticket 25.

Criterion 6, from a fresh build of the development `.kb` (1,514 Documents, `validate` clean) with the generated `AGENTS.md`: Claude Code 2.1.310, `--model sonnet`, Read/Grep/Glob only, scored by `scripts/agent-run.py`. 17 of 17, median 3, maximum 5, PASS. `CLAUDE.md` now puts `AGENTS.md` into context, so most runs skip reading it, which saves a call against the earlier runs.

| Id | First expected read / total calls | Ticket 29 rerun |
|---|---:|---:|
| API-01 | 3 / 3 | 3 |
| API-02 | 3 / 3 | 4 |
| API-03 | 3 / 3 | 4 |
| SOL-01 | 4 / 6 | 5 |
| SOL-02 | 3 / 6 | 4 |
| SOL-03 | 3 / 6 | 4 |
| SOL-04 | 5 / 6 | 6 |
| HOW-01 | 2 / 2 | 4 |
| HOW-02 | 3 / 5 | 4 |
| HOW-03 | 2 / 2 | 3 |
| HOW-04 | 3 / 4 | 4 |
| TERM-01 | 5 / 5 | 4 |
| TERM-02 | 5 / 5 | 6 |
| THEO-01 | 4 / 4 | 4 |
| THEO-02 | 2 / 4 | 5 |
| FIG-01 | 5 / 6 | 4 |
| FIG-02 | 3 / 12 | 4 |

Two questions are one call over the ticket 29 rerun, so "per question no worse" is not met to the letter:
- TERM-01: two greps of `api.md` for guessed names (`ActiveSolver`, `SolverType`) came before a grep of `vba_3d/` for `ChangeSolverType`.
- FIG-01: the agent grepped inside the right page before reading it.

An earlier run with an intermediate wording also passed: 17 of 17, median 3, with API-01 and SOL-04 one call over. Criterion 5 (manual check) is open. In both runs, API-01 and HOW-04 reached the expected page from a session opened in the folder, with no hint where to look.

**2026-10-25, closed.** The user accepted the one-call differences on TERM-01 and FIG-01 as run-to-run noise, which ticks criterion 6, and closed the ticket. Criterion 5, the manual check in Claude Code, is the user's to do and stays unticked until it is recorded.
