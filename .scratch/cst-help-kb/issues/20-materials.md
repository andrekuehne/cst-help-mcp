# 20: Materials

**What to build:** The Library's Material Definitions become Documents in Area `materials`. Each Document shows:
- the exact name, with a "use as" line;
- a table per Material Set, with units;
- CST's own attribute summary and description, verbatim;
- its Variants and any "same definition as" links;
- the verbatim definition;
- the history block that loads the material, labelled as inferred.

Lookup finds materials by exact name, base name, name without vendor, or normalised form.

**Blocked by:** 17

**Status:** ready-for-agent

- [ ] Every `.mtd` section and Material Set is parsed, including both file formats.
- [ ] Permittivity for fitted materials is computed from their tables and labelled as computed, instead of the placeholder `ε = 1`.
- [ ] Material members that the help doesn't document are marked as undocumented.
- [ ] `FR4` finds `FR-4`, and `Rogers RO4350B` returns both the lossy and loss-free files, with `(lossy)` first under the MWS preference. CHT fluids rank last.
- [ ] Large families (Panasonic, ECCOSORB) are grouped by product in lookup results.
- [ ] Byte-identical files with different names keep separate Documents, linked as "same definition as".
- [ ] Fitting-table rows are not indexed for search.
- [ ] Materials questions (exact name for Rogers RO4350B, which copper for a lossy metal) are added to the benchmark and scored.
