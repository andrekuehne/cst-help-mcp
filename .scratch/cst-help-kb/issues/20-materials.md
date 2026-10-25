# 20: Materials

**What to build:** The Library's Material Definitions are copied into `library/Materials/` as they are, and a generated `materials.md` indexes them one line per file: exact material name, file path, Variants, and "same definition as" links for byte-identical files. An agent that needs the exact name for `.Material "…"` greps the index; one that needs the properties reads the file.

**Blocked by:** 17

**Status:** ready-for-agent

- [ ] Every `.mtd` file is copied unchanged, both file formats included.
- [ ] `materials.md` lists each file with its exact name and, where the name has a loss qualifier or a vendor prefix, the base name after it, so that a case-insensitive grep for `fr-?4` or `ro4350b` finds its lines.
- [ ] Byte-identical files with different names are both listed and linked as the same definition.
- [ ] `AGENTS.md` says that the material name CST expects is the file name, and that CHT fluids are not high-frequency materials.
- [ ] The Materials questions (exact name for Rogers RO4350B, which copper for a lossy metal) are added to the benchmark and reach their files in the agent run.

## Comments

**2026-10-25.** Shrunk for ADR 0014. Parsing Material Sets into tables, computing permittivity for fitted materials and the inferred history block are dropped; the file is readable as it is.
