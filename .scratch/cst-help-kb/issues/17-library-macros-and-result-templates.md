# 17: Library: Macros and Result Templates

**What to build:** The `cst-release` Source reads the Library's Macros and Result Templates into Areas `macros` and `result-templates`. A user can say "build it like the Farfield Result template", and lookup by Display Name returns a ranked shortlist headed by the right file.

**Blocked by:** 16

**Status:** ready-for-agent

- [ ] Files are classified by content (control macro, structure macro, Result Template, helper script, class module, preset, data, scrambled, binary), with cp1252 and CRLF handled.
- [ ] Display Names come from the folder path plus the file stem before `^`. The Application Filter is parsed into an attribute, and Variants are linked. MWS Variants rank first.
- [ ] Each file has a header Section plus one Section per `Sub` or `Function`, anchored by procedure name. Files under about 150 lines stay whole, and the change history becomes metadata.
- [ ] Each Document's metadata lists its menu path, kind, Application Filter, includes, help page and Aliases. Exact copies become Aliases.
- [ ] Scrambled Macros appear with metadata only. Legacy templates are flagged and ranked lower. Executables, Office files and wheels are excluded.
- [ ] `StartHelp` targets resolve to help Locators without regard to case.
- [ ] Dialog bitmaps become PNG Assets of the Documents that load them.
- [ ] Code Sections get their own search weights, and search's kind filter separates code from prose.
- [ ] LIB-01 to LIB-03 find their templates by Display Name and by search.
