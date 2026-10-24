# 03: Build lifecycle: immutable Builds, assembly, report

**What to build:** Each `cst-help build <collection>` writes a new, immutable Build. `cst-help assemble` combines the active Builds of all Collections into the Knowledge Base's database and entry files, then switches the active pointer atomically. A running server keeps the Build it opened until it restarts (ADR 0009). Every Build writes a report. Failures follow the agreed policy, and `cst-help validate` checks a Knowledge Base's integrity.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] Rebuilding a Collection never changes an existing Build, and a server started before the rebuild keeps answering from its Build.
- [x] The build report counts discovered, converted, skipped and failed Documents, unresolved links, missing Assets and unsupported items. The CLI prints a summary.
- [x] A Source whose expected structure isn't recognised fails the build. Failures in individual Documents mark the Knowledge Base incomplete, and the server reports it. `--strict` makes any failure fatal.
- [x] Sources accept include and exclude filters, so tests and experiments can build part of a Release.
- [x] `cst-help validate` detects a missing or inconsistent Build, database or Asset.
- [x] Minimal synthetic fixtures cover a Locator collision, an unrecognised structure, and immutability across the pointer switch. They may be hand-written or cut from real pages (ADR 0001).

## Comments

**Implemented (2026-10-24).** 20 new tests: 11 in `tests/test_build_lifecycle.py` (synthetic release folders, except the filter test, which uses the corpus) and 9 in `tests/test_validate.py` (a slice of the corpus). The full suite has 66. The development `.kb` builds 372 Documents in about 10 s and validates.

Decisions for later tickets:

- **Layout** (`layout.py`): `builds/<collection>/<build id>/` (`build.json`, `report.json`, `tree/`), `assemblies/<assembly id>/` (`assembly.json`, `index.sqlite`), and `active.json`, the pointer, replaced atomically. Ids sort by creation time. Builds and assemblies are written under `.<id>.partial` and renamed into place. A Build counts as finished once it has its `build.json`, which lists its Locators and the SHA-256 of every file.
- **Readable view.** `kb/<collection>/` is rebuilt at each assembly as hard links into the active Build's `tree/`, with copies where links fail. Build files are read-only, so an in-place edit through the view fails instead of changing the Build. The view switches just before the pointer.
- **Build and assemble.** `cst-help build` writes a Build and then assembles. `cst-help assemble --kb` re-assembles from the newest finished Build of every Collection, for example to restore a damaged view. Assembly holds `kb/.lock`, so a second process fails clearly instead of racing.
- **A running server keeps its Build.** Assembly writes a new database. A server's open `index.sqlite` is locked on Windows, so pruning keeps that assembly and every Build it references. Builds and assemblies that nothing holds are removed. On POSIX the open database survives, but its Build files may be pruned. **Ticket 08:** `read` should resolve Locators in the Build recorded in the server's own database (`collections.build`), not in the view, which follows the newest assembly.
- **Report.** The counts cover discovered `.htm` files, converted, skipped (non-topic pages) and failed Documents. Unsupported items are the other files in the selected part, counted by extension. Images count as unsupported until ticket 09. `unresolved_links` and `missing_assets` are `null` ("not checked yet") until tickets 04 and 09 fill them in.
- **Failures.** An exception while reading one Document is recorded, and the build goes on. The Build is then incomplete: its failure count lands in `collections.failed`, `KnowledgeBase.incomplete` exposes it, and the server instructions say so. `--strict` makes any failure fatal. Failures that are always fatal: a missing `Online Help` folder or VBA 3D project, a selection with no topics, a build where no Document converts, and a Locator collision. A failed build leaves the previous Build active.
- **Validate** checks the pointer, the assembly and Build manifests, every Build file's hash, the view, the database's integrity, and that its Builds and Locators match the manifests. Assets are covered by the file hashes once ticket 09 writes them.
- **Glossary gap:** "assembly" is now a command, a folder and a class, but GLOSSARY.md has no entry for it.
