# 07: Benchmark runner

**What to build:** The benchmark draft becomes a machine-readable benchmark: questions, categories, Area filters, expected sources with their anchors or PDF pages, and API Entries. A runner scores it against a built Knowledge Base. Expected source paths are mapped to Locators mechanically (ADR 0011).

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] The machine-readable benchmark holds all 39 draft questions, keeps their ids, and stores no vendor text.
- [ ] Expected sources are mapped from source paths to Locators mechanically, and PDF pages to page anchors.
- [ ] The runner reports hit-at-5 and mean reciprocal rank per category and overall, with and without the Area filter. API questions additionally check lookup.
- [ ] Questions that are scored by hand (the "not in the documentation" category) are listed, not scored.
- [ ] The runner belongs to the corpus tier and runs against whichever Areas are built. Questions whose Areas aren't built yet are reported as skipped.
