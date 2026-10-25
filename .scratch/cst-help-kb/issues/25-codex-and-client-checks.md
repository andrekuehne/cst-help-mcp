# 25: Codex and client checks

**What to build:** Codex joins Claude Code and Cursor as a supported client. Each client is opened in the Knowledge Base folder and run through five questions with file tools only, including a figure question, and what each client needs in order to read the workspace is recorded.

**Blocked by:** 15

**Status:** ready-for-agent

- [ ] In each client: API-01, HOW-04, SOL-01, FIG-02 and NODOC-01 from a session opened in the folder. The agent reaches the expected page, opens the figure from disk, and says NODOC-01 is not documented.
- [ ] Whether each client reads `AGENTS.md` on its own is recorded. If Cursor needs a `.cursor/rules/` file, ticket 15's assembly writes it.
- [ ] Whether `cst-help instructions` is enough for a project session (a repository that points at the folder, next to the Control Server) is checked in Claude Code with the folder added to the session.
- [ ] Findings are recorded in the spec's Further Notes, and any needed changes become new tickets.

## Comments

**2026-10-25.** Rewritten for ADR 0014: no MCP configuration, no image tool, no server instructions to verify.
