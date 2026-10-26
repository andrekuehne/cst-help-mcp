# 21: Remaining Areas and manuals

**What to build:** The rest of `cst-2024` comes in:
- Areas `circuits`, `pcb`, `filter-designer`, `chip-interface`, `vba-schematic` and `example-projects`;
- the remaining Word manuals and the release notes in `manuals`.

VBA schematic objects become API Entries in their own Area.

**Blocked by:** 16

**Status:** done

- [x] Every remaining RoboHelp project builds with its navigation metadata, and its quirks are handled by the CSS class map.
- [x] VBA schematic API Entries stay distinct from VBA 3D ones with the same name.
- [x] The Example Projects are included, although no table of contents reaches them.
- [x] All Word manuals and the release notes build, and REL-01 finds its page.
- [x] Every benchmark question can be run, and the full agent run is recorded in ticket 16's table.

## Comments

**2026-10-26.** Implemented in `9fe3415`.

- **Areas.** `build._CST_RELEASE_PROJECTS` reads DES into `circuits` (`des/`), PCB into `pcb`, Filter_Designer_3D into `filter-designer`, CHI into `chip-interface` and VBA_DES into `vba-schematic` (`vba_des/`, with the VBA profile). The seven `EXP_*` projects go into `example-projects` (`exp_cbl/` … `exp_pd/`). The root table of contents already splices in the five registered projects, so they carry navigation metadata: 1,334 entries are kept and 3 dropped. No table of contents reaches the Example Projects. They are read as projects anyway, and their topics keep only the breadcrumbs embedded in them.
- **Quirks.** The new projects share 3D's and VBA 3D's style sheets. Classes the map doesn't know, such as `DokuText` and `Topic-Text-Bulleted`, already become paragraphs. The one quirk that needed handling is a heading tag styled as body text or a field name: `<h4 class="Tip-Note-Text">General Description</h4>` in Filter Designer, and PCB's Ribbon Paths as `<h2 class="Tip-Note-Text">`. The class map made those paragraphs or field terms. `robohelp._role` now lets the tag's heading role win over the class roles `text` and `term`. The rule is part of how the Profile is read, not one more class entry, because no class entry can say "unless the tag is a heading". It also changes about 90 3D topics; `tests/test_3d_general.py` checks two of them. h3 stays prose.
- **Manuals.** `manuals/` takes every PDF in `Documentation/` except `*FEST3D*`, `*SPARK3D*` and `*IdEM*`: the 8 Word manuals and the Release Notes. REL-01 finds page 10 of the Release Notes. Word's symbol-font characters are now mapped (ticket 13's open point): the Ribbon Path arrow U+F0F0 becomes `>`, as the help writes it, and the bullets U+F06F, U+F0A7 and U+F0B7 become `•`. Greek letters in equations stay private-use characters.
- **VBA schematic.** Its API Entries carry the Area `vba-schematic` in `api.md` and its own Locators, so `ParameterSweep`, `Units` and `ResultTree` each have one line per Area. The `AGENTS.md` rules and anatomy now name `vba_des/`.
- **Build report.** 4,246 Documents, 0 failed. The 11 unresolved links and 11 missing anchors are all corpus defects: missing files, a fragment written without its `#`, `common_VBAGeneral/common_general_blocks_supporting_layout_changes.htm`, which is not installed, and anchors the target pages never define. The outside links lead to IdEM, FEST3D, SPARK3D and sample-data files.
- **Agent run.** It is recorded in ticket 16: every question can be run, 38 of 40 hit, median 3. FIG-02 was answered correctly from the High Frequency manual instead of the expected help page. LIB-02, a Library question, never opened `library.md`. Neither miss comes from this ticket's changes.
- **Tests.** `tests/test_remaining_areas.py` is new. The `manuals_build` fixture now holds only the two slice manuals, so the REL-01 miss case still has a folder without the Release Notes. 167 tests pass.
