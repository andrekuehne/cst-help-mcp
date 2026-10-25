# Files and the MCP server are two views of one build, sharing Locators

**Superseded by ADR 0014.** The Markdown tree is the only view; there is no MCP server.

Coding agents are strongest with their native file tools (grep, open by path), while an MCP server adds ranked search, exact API lookup, the editorial keyword index and image delivery. We publish both from the same build: the Markdown tree is the readable, greppable view, and the MCP server is the discovery and lookup view. They share one addressing scheme, so a Locator returned by search is also a file path plus anchor, and `read` returns exactly the file's text. Neither view may contain information the other cannot reach.

## Considered Options

- MCP-only, with Markdown as an internal artifact: hides the content from the agents' best tools.
- Files-only (Markdown plus grep): loses ranking, exact lookup and image delivery for clients that cannot open images from disk.
