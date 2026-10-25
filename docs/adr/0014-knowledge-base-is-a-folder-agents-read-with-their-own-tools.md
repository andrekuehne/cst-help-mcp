# The Knowledge Base is a folder that agents read with their own tools; there is no search server

The first version built a read-only MCP server over a SQLite index: exact API lookup, BM25 search with weighted fields, trigram partial names, paged reading, image delivery and navigation browsing. Tuning its ranking on the benchmark showed that every miss was a ranking-shape problem (sibling Sections, short pages beating long ones, one heavy field) and that fixing those meant modelling pages for the ranker rather than for the reader. On 2026-10-25 the 17 scorable benchmark questions were answered from the Markdown tree alone, by agents given only a 4.6 KB `AGENTS.md` and their own file tools (grep, glob, read). Every question reached an expected Document, with a median of two greps before the page was open, under both a strong and a mid-sized model (`.scratch/cst-help-kb/files-only-experiment.md`). The vendor's own keyword index did most of the routing, the agents bridged the one vocabulary gap themselves, and both figure questions were answered by opening the image file.

So the Knowledge Base is a folder, and the folder is the whole interface. The build converts the help into Markdown, copies the Library code and the PDFs in beside it, writes index files (`toc.md`, `keywords.md`, `api.md`, `library.md`) and an `AGENTS.md` with navigation recipes, and nothing else. Agents consult it with the tools they already have, from a session opened in the folder or from a project that points at it. There is no server, no database, no ranking, no Synonym Sets and no usage index. Nothing is written into the tree that is not for reading: the persisted Document model that sat beside each page as a JSON sidecar is dropped, since re-parsing is cheap and the sidecars polluted greps.

The benchmark stays, as a question set. It is scored by running agents from the folder and counting tool calls to an expected Document, not by a ranker.

## Consequences

- ADR 0003 (files and MCP as two views), ADR 0004 (a separate read-only server) and ADR 0008 (exact lookup before lexical search) are superseded. ADR 0005 holds for sessions instead of servers: one folder per Release, and `AGENTS.md` names the Release. ADR 0007 keeps its reader-side decisions but no longer persists the model. ADR 0009 keeps immutable Builds; assembly produces entry files and `AGENTS.md`, not a database. ADR 0010 keeps Guides; the authoring session reads files. ADR 0012's usage index is superseded by grep over the copied Library; the rule to report an Undocumented Member instead of "not found" moves into `AGENTS.md`. ADR 0013 stands, and the workspace it describes is now the product.
- A client without file access is not supported. None of the three target clients (Claude Code, Codex, Cursor) is one.
- Should a ranked search ever be wanted again, it is a command-line tool over FTS5 that agents call from the shell, added by its own ticket with the agent-run benchmark as evidence. It is not a server.

## Considered Options

- Keeping a thin MCP server for search only: a second interface to maintain, for a need the experiment did not show.
- Keeping the SQLite index as a CLI search beside the folder: cheap, but untested against a need, and it would keep the ranking work alive.
