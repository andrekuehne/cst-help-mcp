# Collections build independently into immutable Builds, assembled into the Knowledge Base

**Amended by ADR 0014.** Assembly produces the entry files and `AGENTS.md`, not a search index; there is no server holding files open, but Builds stay immutable and the pointer switch stays.

Adding a few PDFs should not mean rebuilding a whole CST Release, a running server must never see a half-written Knowledge Base, and Windows cannot replace SQLite files that a server holds open. So each Collection is built on its own into a new, immutable Build directory. Only PDF conversion is cached (keyed by file hash plus converter version and settings); everything else is derived again on every build, which keeps the cache logic small now that there is no OCR (ADR 0006). A separate, cheap assembly step combines the active Builds of all Collections into the Knowledge Base's search index and entry files, then switches a pointer. A running server keeps the Builds it opened until it restarts.

## Considered Options

- One build for the whole Knowledge Base: simpler, but every added PDF rebuilds every Release.
- Fine-grained incremental caching of every stage, as the brainstorm proposed: unnecessary once OCR is gone, and a common source of stale output.
