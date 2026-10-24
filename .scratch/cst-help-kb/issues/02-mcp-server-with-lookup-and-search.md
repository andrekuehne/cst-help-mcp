# 02: MCP server with lookup and search

**What to build:** `cst-help serve --kb <path>` starts the read-only `cst-help` MCP server over stdio, built on the official `mcp` 2.x SDK. It exposes `cst_help_lookup` and `cst_help_search`, which wrap the retrieval core one to one. `cst-help instructions` prints the MCP entry and AGENTS.md section to paste into a project, so Claude Code can be pointed at the Knowledge Base and look up VBA methods.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] The server serves exactly one Release, fixed at start with `--release`, defaulting to the newest. Every result names its Release (ADR 0005).
- [ ] The first 512 characters of the server instructions stand on their own: identifiers and Display Names go to `cst_help_lookup`, concepts to `cst_help_search`, and answers cite the Locator and Release. The instructions also give the "not documented" rule and the Knowledge Base path.
- [ ] Reads stay inside the Knowledge Base root, the server makes no network calls, and it logs to stderr only.
- [ ] Every response stays under 10,000 tokens. Search returns at most 10 hits in about 3,000 tokens.
- [ ] Contract tests use the SDK's in-memory client to cover tool names and parameter schemas, the start of the instructions, the budgets, and clear errors for unknown names.
- [ ] Manual check: Claude Code, configured with the printed entry, looks up `Solver.FrequencyRange` through the server.
