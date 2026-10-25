# 15: Knowledge Base workspace

**What to build:** Every assembly makes the Knowledge Base folder a ready-to-open agent workspace (ADR 0013, ADR 0014). Opening Claude Code, Codex or Cursor there is all the setup there is. The generated `AGENTS.md` carries the navigation recipes that the experiment's hand-written one proved, with real counts and the Areas actually built.

**Blocked by:** 29

**Status:** ready-for-agent

- [ ] `AGENTS.md` stays under about 8 KB and is generated from the hand-written one in `../files-only-experiment.md`: the rules (first and in bold, that grep finds pages and never answers: open every cited page with the read tool before answering, even when the grep lines seem to hold the answer, and grep bodies without context lines; cite the path and the Release; "not documented" means not in `vba_3d/` and not in the Library; an Undocumented Member is one the Library uses but no page documents; look at figures), the table of folders with page counts, the page anatomy, the recipes (identifier, concept, UI location, dialog to VBA object, theory, terminology), and the list of index files and Guides.
- [ ] `api.md` lists every API Entry one per line: qualified name, Area, signature, path with anchor. It is the exact table, meant for grep.
- [ ] `CLAUDE.md` imports `AGENTS.md`. A `.cursor/rules/` file does the same for Cursor if ticket 25 finds that Cursor does not read `AGENTS.md` by itself.
- [ ] A `work/` folder for what agents write and a `guides/` folder for Guides (ticket 24) exist, and builds and assemblies never touch them.
- [ ] Manual check: Claude Code opened in the folder answers API-01 and HOW-04 from the generated `AGENTS.md` without being told where anything is.
- [ ] `scripts/agent-run.py` passes from a fresh build with the generated `AGENTS.md` (Claude Code, `--model sonnet`): 17 of 17, median at most 4, and per question no worse than the 2026-10-25 run with the strengthened hand-written one (ticket 29's comments). That closes ticket 29's criterion 7.

## Comments

**2026-10-25.** Rewritten for ADR 0014: no MCP configuration is written. The hand-written `AGENTS.md` that this ticket generalises is appended to `../files-only-experiment.md`.

**2026-10-25.** From ticket 29's agent run: with the experiment's wording ("Read the page before answering from a grep snippet", last in the rules), Sonnet answered THEO-02 from `grep -C` snippets without opening the page in two of three runs. Moved to the top of the rules and put as "**Grep finds pages; it never answers.** Before you answer, open every page you cite with your Read tool, even when the grep lines already seem to hold the answer. A snippet leaves out the conditions, figures and exceptions around it.", with the body-grep recipe saying "no context lines; then read the best match", THEO-02 hit in three of three runs and the full run scored 17 of 17, median 4. `cst-help instructions` already carries this wording (`instructions.RULES`); generate `AGENTS.md` from the same constants.

