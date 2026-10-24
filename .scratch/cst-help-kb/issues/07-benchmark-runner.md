# 07: Benchmark runner

**What to build:** The benchmark draft becomes a machine-readable benchmark: questions, categories, Area filters, expected sources with their anchors or PDF pages, and API Entries. A runner scores it against a built Knowledge Base. Expected source paths are mapped to Locators mechanically (ADR 0011).

The runner is also the tool for tuning search. Ticket 06 tuned its field weights on 8 questions and checked them on the same 8, so the weights are fitted to them. The benchmark therefore grows sets of questions the corpus labels itself, short queries as agents write them, and a held-out split. The runner takes weight overrides and searches a grid of them.

**Blocked by:** 01, 06

**Status:** ready-for-agent

- [ ] The machine-readable benchmark holds all 39 draft questions, keeps their ids, and stores no vendor text.
- [ ] Expected sources are mapped from source paths to Locators mechanically, and PDF pages to page anchors.
- [ ] The runner reports hit-at-5 and mean reciprocal rank per category and overall, with and without the Area filter. API questions additionally check lookup.
- [ ] Questions that are scored by hand (the "not in the documentation" category) are listed, not scored.
- [ ] The runner belongs to the corpus tier and runs against whichever Areas are built. Questions whose Areas aren't built yet are reported as skipped.
- [ ] The eight solver and how-to questions in `tests/test_search_ranking.py` come from the machine-readable benchmark instead of the test. Their ranks before ticket 06 and now stay as the first recorded baseline.
- [ ] Each draft question also gets one or more short queries, as an agent would type them ("AR filter VBA", "discrete port impedance"). They're scored next to the full question text, since short and long queries rank differently.
- [ ] Derived question sets are generated from the built Knowledge Base, not written by hand, and store no vendor text, only names and Locators:
  - each author keyword → its target topics;
  - each table-of-contents entry name → its page;
  - a sample of API Entry names → their Sections.

  They're scored per set. A keyword query naturally favours the keyword field, so the derived sets guard against regressions and calibrate the scales of the weights. They aren't used to choose between fields.
- [ ] Every question set is split once, by a fixed seed, into a tuning half and a held-out half. The report gives both. A weight change counts as better only if the held-out half improves too.
- [ ] The runner takes weight overrides (Section title, headings and body; Document keywords and table-of-contents paths) without editing code. It searches a small grid, then reports the best settings and how flat the area around them is. A broad plateau is preferred to a single best point.
- [ ] If scores swing with small weight changes, the runner can also try putting the Section and Document scores on one scale, by normalising them or fusing by rank, before more weights are tuned. Embeddings stay out until this lexical search still misses (ADR 0008).
- [ ] An opt-in query log records each `cst_help_search` and `cst_help_lookup` call: query, filters, the Locators returned and their order. It goes to a file named by the server's configuration or command line, never by default and never to stdout. The runner can turn logged queries into draft benchmark entries for a human to give expected sources.
