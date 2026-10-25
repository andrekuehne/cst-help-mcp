# 19: Usage index and Undocumented Members

**What to build:** The build scans Library code and records which Sections use which API Entry (ADR 0012). It reads VBA inside string literals, maps calls without an object to the Application object, and counts method names passed to `CallByName`. Lookup shows the best few Usages next to each API Entry. A member that only Library code uses becomes an Undocumented Member with its Usages, instead of a "not found".

**Blocked by:** 17, 18

**Status:** wontfix

- [ ] Every Usage is labelled as found heuristically, and Usages are ranked to prefer current layout, non-legacy code and short Sections.
- [ ] Each API Entry's Markdown lists its top Usages, keeping the two views in step (ADR 0003).
- [ ] `Units.GetFrequencyUnit` returns as an Undocumented Member with its Usages.
- [ ] A member that is neither documented nor used returns "not documented".
- [ ] Library questions (LIB-04, LIB-05, and new ones about Usages) are added to the benchmark and scored.

## Comments

**2026-10-25, retired.** No usage index is built. The Library is copied into the tree and `grep` over it is the usage index. The Undocumented Member rule moves into `AGENTS.md` (ticket 15). See ADR 0014 and `../files-only-experiment.md`.
