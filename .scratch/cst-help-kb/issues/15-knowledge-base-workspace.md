# 15: Knowledge Base workspace

**What to build:** Every assembly makes the Knowledge Base folder a ready-to-open agent workspace (ADR 0013). Opening Claude Code or Cursor there connects to `cst-help` with no further setup.

**Blocked by:** 02, 03

**Status:** ready-for-agent

- [ ] `AGENTS.md` stays under about 8 KB. It holds the routing rules, the citation and "not documented" rules, and an index of each Area's entry files (with a slot for Guides).
- [ ] `CLAUDE.md` imports `AGENTS.md`.
- [ ] `.mcp.json`, plus `.cursor/mcp.json` and a Cursor rule, register the server using relative paths, so they survive copying the folder.
- [ ] A `work/` folder exists, and builds and assemblies never touch it.
- [ ] Manual check: Claude Code opened in the Knowledge Base folder lists the `cst_help_*` tools and uses them.
