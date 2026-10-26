# 20: Materials

**What to build:** The Library's Material Definitions are copied into `library/Materials/` as they are, and a generated `materials.md` indexes them one line per file: exact material name, file path, Variants, and "same definition as" links for byte-identical files. An agent that needs the exact name for `.Material "…"` greps the index; one that needs the properties reads the file.

**Blocked by:** 17

**Status:** ready-for-agent

- [x] Every `.mtd` file is copied unchanged, both file formats included.
- [x] `materials.md` lists each file with its exact name and, where the name has a loss qualifier or a vendor prefix, the base name after it, so that a case-insensitive grep for `fr-?4` or `ro4350b` finds its lines.
- [x] Byte-identical files with different names are both listed and linked as the same definition.
- [x] `AGENTS.md` says that the material name CST expects is the file name, and that CHT fluids are not high-frequency materials.
- [x] The Materials questions (exact name for Rogers RO4350B, which copper for a lossy metal) are added to the benchmark and reach their files in the agent run.

## Comments

**2026-10-25.** Shrunk for ADR 0014. Parsing Material Sets into tables, computing permittivity for fitted materials and the inferred history block are dropped; the file is readable as it is.

**2026-10-26.** Built. What the build does beyond the letter of the criteria, and why:

- **"Unchanged" means the content**: line endings become LF, like every other file in the tree, so a grep's `$` anchors work. All 779 files are ASCII, so nothing else changes. "Same definition" compares the source bytes.
- **The base name** drops a vendor prefix (Panasonic, Rogers, Taconic, ECCOSORB, Preperm, Schott, the six families of the Library research) and a last qualifier that starts with `loss` (`(lossy)`, `(loss free)`, `(lossy - thermal anisotropic)`). Other qualifiers stay, since they name other materials: `ECCOSORB AN-72 (back)` has the base name `AN-72 (back)`, and `Air (CHT)` has none. The cell is empty when the base name is the name.
- **Variants** are the files whose names differ only in that loss qualifier, so `FR-4 (lossy)` has `FR-4 (loss free)` and `FR-4 (lossy - thermal anisotropic)`, a bare Panasonic CEM-3 name has its `(loss free)` twin, and `Rogers RO4350B LoPro` is not a Variant of `Rogers RO4350B`. `GLOSSARY.md` widens Variant accordingly.
- **A Description column** holds the file's `[Description]` on one line, the only section read. It shows "EM(HF) properties measured @ 10GHz", "100% IACS" or the CHT warning on the grep line itself.
- **"Same definition as" cells are Markdown links**, so `validate` checks them; 74 pairs, 148 rows.
- **`materials.md` is apart from `library.md`**, and a build with Material Definitions but no Library code writes no `library.md`. `validate` reports a missing `materials.md`. ADR 0014's list of index files names it.
- **`AGENTS.md` of the full Release is 9,300 bytes.** The Materials recipe is added only when `materials.md` exists.
- **The benchmark** gains LIB-06 (exact name for Rogers RO4350B, with its losses) and LIB-07 (which copper for a lossy metal). `scripts/agent-run.py` already names `library/Materials/` the Area `materials`.

Agent run on the full Release (Claude Code 2.1.310, `--model sonnet`, Read/Grep/Glob only), LIB-06 and LIB-07: 2 of 2 reached an expected file at call 2 (LIB-06 2 calls in all, LIB-07 4). LIB-06 answered `.Material "Rogers RO4350B (lossy)"`; LIB-07 named `Copper (annealed)` (5.8e7 S/m) and `Copper (pure)` (5.96e7 S/m). As in ticket 17, `CLAUDE.md` had put `AGENTS.md` in context, so call 1 was not its read.
