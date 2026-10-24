# 24: Guides

**What to build:** Guides become possible (ADR 0010):
- The package ships Guide-writing skills, one per topic family, and every assembly copies them into the workspace.
- An agent session in the workspace writes Guides into `work/guides/<release>/`.
- `cst-help build cst-2024-guides` ingests them as their own Collection in Area `guides`.

**Blocked by:** 15, 19

**Status:** ready-for-agent

- [ ] Skills exist for the first topic families: VBA history commands, Result Template anatomy, dialogs, settings storage, and `cst.interface` sessions. They contain no vendor text.
- [ ] The `guides-folder` Source reads Markdown with frontmatter and Locator citations.
- [ ] Ingestion flags every cited Locator that doesn't exist, and every identifier in a Guide's code that is neither an API Entry, a Helper nor an Undocumented Member.
- [ ] Guides are marked as generated in frontmatter and in every hit, and get no ranking boost.
- [ ] Lookup lists the Guides that cite an API Entry, and `AGENTS.md` lists every Guide.
- [ ] Synthetic fixtures cover the failure cases: a missing Locator and an invented method.
