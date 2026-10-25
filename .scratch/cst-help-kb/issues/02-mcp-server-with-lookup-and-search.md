# 02: MCP server with lookup and search

**What to build:** `cst-help serve --kb <path>` starts the read-only `cst-help` MCP server over stdio, built on the official `mcp` 2.x SDK. It exposes `cst_help_lookup` and `cst_help_search`, which wrap the retrieval core one to one. `cst-help instructions` prints the MCP entry and AGENTS.md section to paste into a project, so Claude Code can be pointed at the Knowledge Base and look up VBA methods.

**Blocked by:** 01

**Status:** done

- [x] The server serves exactly one Release, fixed at start with `--release`, defaulting to the newest. Every result names its Release (ADR 0005).
- [x] The first 512 characters of the server instructions stand on their own: identifiers and Display Names go to `cst_help_lookup`, concepts to `cst_help_search`, and answers cite the Locator and Release. The instructions also give the "not documented" rule and the Knowledge Base path.
- [x] Reads stay inside the Knowledge Base root, the server makes no network calls, and it logs to stderr only.
- [x] Every response stays under 10,000 tokens. Search returns at most 10 hits in about 3,000 tokens.
- [x] Contract tests use the SDK's in-memory client to cover tool names and parameter schemas, the start of the instructions, the budgets, and clear errors for unknown names.
- [x] Manual check: Claude Code, configured with the printed entry, looks up `Solver.FrequencyRange` through the server.

## Comments

**Implemented (2026-10-24).** 18 new tests: 15 MCP contract tests through the SDK's in-memory client (including one real stdio round trip through `cst-help serve`) and 3 CLI tests; the full suite has 46. The manual check passed: Claude Code, in another project configured with the entry printed for the development `.kb`, looked up `Solver.FrequencyRange` through the server.

Decisions for later tickets:

- **Server.** `cst_help_mcp.server.create_server(kb)` takes an opened `KnowledgeBase`, so the Release is fixed by whoever opens it. Tools return plain text (`structured_output=False`). Each hit carries its Area, Release and Locator.
- **Budgets.** Responses are counted in characters at a pessimistic 3 characters per token: 27,000 characters for any response (under 10,000 tokens) and 9,000 for a search page (about 3,000 tokens). Whole hits are left out once a budget is reached, and the response ends with "... N more not shown" and how to narrow. A bare `Reset` has 249 API Entries, so it gets cut.
- **Errors.** A `CstHelpError` from the retrieval core becomes a tool error with the same message. An unknown Area is now an error in the core (`KnowledgeBase.areas`), so the CLI reports it too. An unknown name is not an error; it answers "not documented in Release …".
- **Instructions.** `server_instructions(kb)` serves as both the server instructions and the AGENTS.md section that `cst-help instructions` prints. The "not documented" rule tells agents to try search before concluding, because Display Names route to lookup before lookup supports them (ticket 17).
- **Printed entry.** The command is the absolute path of `cst-help` when it is on PATH, because MCP clients may not see the venv's scripts.
- **Not covered yet.** Containing reads to the Knowledge Base root has nothing to test until `cst_help_read` lands (ticket 08). Logging goes to stderr via `logging.basicConfig(stream=sys.stderr)` and the SDK's own stderr handler; the stdio test would fail if stdout were polluted during a call.
