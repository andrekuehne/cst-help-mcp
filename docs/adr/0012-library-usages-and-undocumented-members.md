# The build indexes Library Usages, including Undocumented Members

**Superseded by ADR 0014.** No usage index is built; agents grep the copied Library. The rule that a member Library code uses but no help page documents is reported as an Undocumented Member, not as "not found", lives in `AGENTS.md`.

About three quarters of the Library has no help page, and Library code uses members the 2024 help never documents (for example `Units.GetFrequencyUnit`, in 80 files). Agents learn CST's idioms best from working code, so the build scans Library code and records which Sections use which API Entry. It reads VBA inside string literals (a third of all uses are history commands built as strings for `AddToHistory`) and maps unqualified calls to the Application object. `cst_help_lookup` shows the best few Usages next to each API Entry. When a lookup finds no API Entry but the code uses the member, it reports an Undocumented Member with its Usages rather than "not found".

The scan is regex-based and misses objects held in variables, so every Usage is labelled as found heuristically, and Undocumented Members are labelled as not authoritative. Readers never execute or import anything from the Library, and scrambled macros are never descrambled.

## Considered Options

- Documentation only, with the Library as plain searchable text: no link from an API Entry to working code.
- A type-inferring VBA parser: more precise, but far more work for a dialect with no available grammar.
