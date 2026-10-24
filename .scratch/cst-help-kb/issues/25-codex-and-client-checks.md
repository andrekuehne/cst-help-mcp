# 25: Codex and client checks

**What to build:** Codex joins Claude Code and Cursor as a supported client, and image and instruction behaviour is verified in all three.

**Blocked by:** 16

**Status:** ready-for-agent

- [ ] Whether Codex accepts a project-level MCP configuration is settled. If it does, assembly writes one into the workspace; if not, `cst-help instructions` prints the global entry.
- [ ] In each client: images from `cst_help_images` reach the model, output stays within budget, and the server instructions take effect (recorded for Cursor).
- [ ] Findings are recorded in the spec's Further Notes, and any needed changes become new tickets.
