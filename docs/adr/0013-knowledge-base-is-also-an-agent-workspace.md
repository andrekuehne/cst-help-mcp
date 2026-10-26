# The Knowledge Base is also a ready-to-open agent workspace

**Confirmed by ADR 0014.** The workspace is the product. There is no MCP configuration to write. The workspace files are written into each Release folder, not the Knowledge Base root, since a session works in one Release (ADR 0005 as amended), and a `guides/` folder sits beside `work/` (ADR 0010).

**Amended 2026-10-26 (ticket 23).** The Knowledge Base root also gets a short `AGENTS.md`, with `CLAUDE.md` importing it. It is not a workspace: it lists the Release folders and the release-independent Collections beside them, and tells a session to open one Release and stay in it.

**Amended 2026-10-26.** The `AGENTS.md` budget is about 12 KB, up from 8 KB. With the Library's recipes, the full Release reached the old limit, and staying under it meant cutting recipe lines the benchmark runs had relied on. Ticket 30 plans a short skeleton `AGENTS.md` with the detailed instructions in skills that the user invokes. That leaves the finding below untouched, since no agent has to decide to load a skill. A plain question with no skill invoked must still be answerable from the skeleton, and the agent run checks both cases before the skeleton replaces this layout.

Users should be able to start a "help session" by opening Claude Code, Cursor or Codex directly in the Knowledge Base folder. Every assembly therefore writes, at the Knowledge Base root:

- a generated `AGENTS.md` of about 12 KB at most, holding the routing rules, the citation and "not documented" rules, and a compact index of each Area's entry files and every Guide;
- `CLAUDE.md`, which imports it;
- MCP configuration for Claude Code (`.mcp.json`) and Cursor (`.cursor/mcp.json` plus a rule), pointing at the Knowledge Base by relative path so it survives copying;
- a `work/` folder that builds never touch, for anything agents write.

In the user's own project repositories, `cst-help instructions` prints the equivalent MCP entry and AGENTS.md section instead. An index in AGENTS.md was the most reliable way to make agents consult documentation in published evaluations (Vercel, 2026), more reliable than skills that agents must choose to invoke.

## Considered Options

- Shipping the Guides as installable Agent Skills: agents often fail to invoke skills, and installation is a separate step per client.
- Only printing instructions for the user to paste: works for project sessions, but leaves the Knowledge Base itself without an entry point.
