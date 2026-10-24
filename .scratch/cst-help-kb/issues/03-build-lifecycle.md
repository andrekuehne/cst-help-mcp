# 03: Build lifecycle: immutable Builds, assembly, report

**What to build:** Each `cst-help build <collection>` writes a new, immutable Build. `cst-help assemble` combines the active Builds of all Collections into the Knowledge Base's database and entry files, then switches the active pointer atomically. A running server keeps the Build it opened until it restarts (ADR 0009). Every Build writes a report. Failures follow the agreed policy, and `cst-help validate` checks a Knowledge Base's integrity.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Rebuilding a Collection never changes an existing Build, and a server started before the rebuild keeps answering from its Build.
- [ ] The build report counts discovered, converted, skipped and failed Documents, unresolved links, missing Assets and unsupported items. The CLI prints a summary.
- [ ] A Source whose expected structure isn't recognised fails the build. Failures in individual Documents mark the Knowledge Base incomplete, and the server reports it. `--strict` makes any failure fatal.
- [ ] Sources accept include and exclude filters, so tests and experiments can build part of a Release.
- [ ] `cst-help validate` detects a missing or inconsistent Build, database or Asset.
- [ ] Minimal synthetic fixtures cover a Locator collision, an unrecognised structure, and immutability across the pointer switch. They may be hand-written or cut from real pages (ADR 0001).
