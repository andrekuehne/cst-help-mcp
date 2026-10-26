# 30: Skeleton AGENTS.md with the recipes in skills

**What to build:** `AGENTS.md` shrinks to a skeleton: the rules, the folder table, the entry files, and one line per recipe family that names the skill holding its detail. The detailed recipes and the page anatomy move into navigation skills that assembly copies into each Release folder beside the Guide-writing skills (ticket 24). The skeleton then stays small however many Areas a Release gains, and each skill can say more than the shared budget allowed.

**Blocked by:** 24

**Status:** needs-triage

- [ ] `AGENTS.md` keeps the rules (grep finds pages and never answers, cite path and Release, "not documented", Undocumented Member, look at figures), the folder table and the entry files. Each recipe family gets one line saying when to load its skill.
- [ ] Navigation skills hold the detailed recipes and page anatomy, one per family (for example: API lookup, concepts and dialogs, manuals, Library code), with no vendor text. Assembly copies them into `.claude/skills/` and `.agents/skills/` the way ticket 24 copies the Guide skills.
- [ ] The agent run over every scorable question, from a fresh full build, is no worse than with the current `AGENTS.md`: the same hits, and per question no more calls to the first expected read than the run recorded before this change.
- [ ] Ticket 25's client checks say whether Cursor and Codex load the skills. A client that does not load them still gets the rules and the folder table from `AGENTS.md`.

## Comments

**2026-10-26.** From the user, after tickets 17 and 22 each had to cut recipe lines to keep the full Release's `AGENTS.md` under 8 KB: raise the budget now, then move to a skeleton `AGENTS.md` with the detailed instructions in skills. The budget is now about 12 KB (ADR 0013 as amended), and the cut lines are restored.

Open question for triage: ADR 0013 chose an index in `AGENTS.md` over skills because published evaluations found agents often fail to invoke skills (Vercel, 2026; `docs/research/existing-tools.md`). So the agent run is what decides this ticket. Without a skill loaded, an agent has only the skeleton, so the agent run has to show that agents load the right skill before their first grep. If they don't, a middle way is a skeleton that keeps the recipes' one-line grep patterns and moves only the anatomy and the long explanations into skills.
