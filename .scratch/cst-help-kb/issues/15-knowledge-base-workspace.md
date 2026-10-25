# 15: Knowledge Base workspace

**What to build:** Every assembly makes the Knowledge Base folder a ready-to-open agent workspace (ADR 0013, ADR 0014). Opening Claude Code, Codex or Cursor there is all the setup there is. The generated `AGENTS.md` carries the navigation recipes that the experiment's hand-written one proved, with real counts and the Areas actually built.

**Blocked by:** 29

**Status:** ready-for-agent

- [ ] `AGENTS.md` stays under about 8 KB and is generated from the hand-written one in `../files-only-experiment.md`: the rules (cite the path and the Release; "not documented" means not in `vba_3d/` and not in the Library; an Undocumented Member is one the Library uses but no page documents; look at figures), the table of folders with page counts, the page anatomy, the recipes (identifier, concept, UI location, dialog to VBA object, theory, terminology), and the list of index files and Guides.
- [ ] `api.md` lists every API Entry one per line: qualified name, Area, signature, path with anchor. It is the exact table, meant for grep.
- [ ] `CLAUDE.md` imports `AGENTS.md`. A `.cursor/rules/` file does the same for Cursor if ticket 25 finds that Cursor does not read `AGENTS.md` by itself.
- [ ] A `work/` folder for what agents write and a `guides/` folder for Guides (ticket 24) exist, and builds and assemblies never touch them.
- [ ] Manual check: Claude Code opened in the folder answers API-01 and HOW-04 from the generated `AGENTS.md` without being told where anything is.

## Comments

**2026-10-25.** Rewritten for ADR 0014: no MCP configuration is written. The hand-written `AGENTS.md` that this ticket generalises is appended to `../files-only-experiment.md`.
