# 30: Skeleton AGENTS.md with user-invoked skills

**What to build:** `AGENTS.md` shrinks to a skeleton that every session reads: the rules, the folder table, the entry files, and the grep patterns that find an identifier, a concept or a Library file. The detailed instructions for a kind of task move into skills that the user invokes, such as writing a macro, building a Result Template, or answering a how-to question with its UI location. Each skill holds the recipes and page anatomy that its task needs, so it can say more than a shared budget allows. Assembly copies the skills into each Release folder beside the Guide-writing skills (ticket 24).

**Blocked by:** 24

**Status:** needs-triage

- [ ] `AGENTS.md` keeps the rules (grep finds pages and never answers, cite path and Release, "not documented", Undocumented Member, look at figures), the folder table, the entry files and the short grep patterns. It names the skills, so that an agent can suggest one to the user.
- [ ] Each skill is invoked by the user only: in Claude Code its frontmatter sets `disable-model-invocation: true`. The skills hold no vendor text. Assembly copies them into `.claude/skills/` and `.agents/skills/` the way ticket 24 copies the Guide skills.
- [ ] The agent run scores each scorable question twice from a fresh full build: once with the matching skill invoked, once with the skeleton alone. With the skill, no question is worse than the run recorded before this change. With the skeleton alone, every question still reaches an expected Document.
- [ ] Ticket 25's client checks record how each client invokes a user skill. Claude Code uses `/name`; check Codex's and Cursor's equivalents, and whether `.agents/skills/` reaches them.

## Comments

**2026-10-26.** From the user, after tickets 17 and 22 each had to cut recipe lines to keep the full Release's `AGENTS.md` under 8 KB: raise the budget now, then move to a skeleton `AGENTS.md` with the detailed instructions in user-invoked skills. The budget is now about 12 KB (ADR 0013 as amended), and the cut lines are restored.

ADR 0013 chose an index in `AGENTS.md` over skills because agents often fail to invoke skills on their own (Vercel, 2026; `docs/research/existing-tools.md`). User-invoked skills avoid that: the user starts the skill, and the agent never has to decide to load it. The risk that remains is a plain question with no skill invoked, which is why the skeleton keeps the grep patterns and the agent run scores the skeleton alone.

Open for triage: the set of skills and their names (by task, as above, or by Area), and how much of today's recipes the skeleton keeps.
