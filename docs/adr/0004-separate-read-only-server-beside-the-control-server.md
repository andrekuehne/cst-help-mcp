# A separate, read-only documentation server runs beside the Control Server

**Superseded by ADR 0014.** There is no documentation server; the Knowledge Base is a folder read beside the Control Server.

The main consumers are agents generating VBA and Python for a Control Server (mcp-cst-studio, which runs VBA through `cst.interface`). Rather than adding documentation tools to that server, this project ships its own read-only MCP server that agents use alongside it. Both keep independent release cycles and licenses, the Knowledge Base stays useful without a running CST, and the documentation server can never execute anything.

## Considered Options

- Extending the Control Server's own small, hand-written VBA reference (33 objects): couples us to a third-party fork and keeps a second, unofficial source of truth.
- Exposing our retrieval only as a library for the Control Server to import: possible later, but not a committed public interface.
