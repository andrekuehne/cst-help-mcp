# 07: Benchmark runner

**What to build:** The benchmark draft becomes a machine-readable benchmark: questions, categories, Area filters, expected sources with their anchors or PDF pages, and API Entries. A runner scores it against a built Knowledge Base. Expected source paths are mapped to Locators mechanically (ADR 0011).

The runner is also the tool for tuning search. Ticket 06 tuned its field weights on 8 questions and checked them on the same 8, so the weights are fitted to them. The benchmark therefore grows sets of questions the corpus labels itself, short queries as agents write them, and a held-out split. The runner takes weight overrides and searches a grid of them.

**Blocked by:** 01, 06

**Status:** done

- [x] The machine-readable benchmark holds all 39 draft questions, keeps their ids, and stores no vendor text.
- [x] Expected sources are mapped from source paths to Locators mechanically, and PDF pages to page anchors.
- [x] The runner reports hit-at-5 and mean reciprocal rank per category and overall, with and without the Area filter. API questions additionally check lookup.
- [x] Questions that are scored by hand (the "not in the documentation" category) are listed, not scored.
- [x] The runner belongs to the corpus tier and runs against whichever Areas are built. Questions whose Areas aren't built yet are reported as skipped.
- [x] The eight solver and how-to questions in `tests/test_search_ranking.py` come from the machine-readable benchmark instead of the test. Their ranks before ticket 06 and now stay as the first recorded baseline.
- [x] Each draft question also gets one or more short queries, as an agent would type them ("AR filter VBA", "discrete port impedance"). They're scored next to the full question text, since short and long queries rank differently.
- [x] Derived question sets are generated from the built Knowledge Base, not written by hand, and store no vendor text, only names and Locators:
  - each author keyword → its target topics;
  - each table-of-contents entry name → its page;
  - a sample of API Entry names → their Sections.

  They're scored per set. A keyword query naturally favours the keyword field, so the derived sets guard against regressions and calibrate the scales of the weights. They aren't used to choose between fields.
- [x] Every question set is split once, by a fixed seed, into a tuning half and a held-out half. The report gives both. A weight change counts as better only if the held-out half improves too.
- [x] The runner takes weight overrides (Section title, headings and body; Document keywords and table-of-contents paths) without editing code. It searches a small grid, then reports the best settings and how flat the area around them is. A broad plateau is preferred to a single best point.
- [x] If scores swing with small weight changes, the runner can also try putting the Section and Document scores on one scale, by normalising them or fusing by rank, before more weights are tuned. Embeddings stay out until this lexical search still misses (ADR 0008).
- [x] An opt-in query log records each `cst_help_search` and `cst_help_lookup` call: query, filters, the Locators returned and their order. It goes to a file named by the server's configuration or command line, never by default and never to stdout. The runner can turn logged queries into draft benchmark entries for a human to give expected sources.

## Comments

**Implemented (2026-10-24).** `docs/benchmark.toml` is the machine-readable benchmark; `cst_help_mcp.benchmark` scores it, and `cst-help benchmark --kb .kb` prints the report. Tests: `tests/test_benchmark.py` (loading, mapping, scoring, derived sets, grid), `test_search_ranking.py` (the tracked questions, overrides, fusions), `test_mcp_server.py` (query log), `test_cli.py` (both commands).

Decisions for later tickets:

- **Benchmark file.** One `[[questions]]` table per draft question: id, `half`, question, `areas`, `short`, `api_entries`, `sources` (path, anchor, headings, page), `baseline`, `scored = "by hand"`. The draft Markdown keeps the "why" and "risk" lines. Ids and categories come from the draft; `LOG` is new, for entries from the query log.
- **Locators.** `ExpectedSource.locator`: `locator_for(path)`, then the first heading's generated anchor, else the source id if it is usable as a fragment (the reader's rule, now `locator.is_usable_source_id`), else `page-<n>`. Scoring is by Document, as the draft says; the stricter Section hit is left for when PDFs (ticket 13) give pages to check against.
- **Aliases.** The index has a new `document_locators` table, each source path's Locator (a Document's own or an Alias's) to the Document served. `KnowledgeBase.document_of` reads it; a hit counts for an expected Alias. A Knowledge Base assembled before this table existed gives a clear error asking for a rebuild.
- **Skipped and missing.** A question is skipped when one of its Areas isn't built. A scored question whose expected Documents aren't in the Knowledge Base lists them, which catches mapping mistakes. Lookup is checked for API questions: lookup of the first `api_entries` name, unfiltered, must return the first source; the report gives its rank among lookup's hits. So the first entry is the one the first source documents (API-10 lists the VBA `AddToHistory` first). A question keeps only its first Area filter from the draft's "(then ...)"; LIB-04 and LIB-05 filter on both of theirs, as an agent would.
- **Split.** The questions were split once by a one-off script, and each half is recorded in the file: within each category, ids sorted by SHA-256 of `cst-help-benchmark-1:<id>` alternate between the halves, and each category with an odd count starts the next one on the other half. Short queries follow their question. Derived items and questions without a recorded half fall into a half by a hash of their name, so adding items never moves others. Entries from the query log are drafted as held out.
- **Derived sets** are generated from the Knowledge Base at each run and never stored: keyword → its leaf topics (Document hit), table-of-contents name → its pages (Document hit), API Entry qualified name → its own Section (exact hit). `--derived N` samples N of each by a hash, salted apart from the split; 200 by default. 600 probes take about 2 seconds.
- **Ranking.** `retrieval.Ranking` holds the five field weights and `fusion`: `sum` (raw BM25, as before), `normalised` (each index's scores divided by its best for the query) or `rank` (reciprocal rank fusion, k = 60). `search(ranking=...)` takes it; the MCP server and CLI search always use the default.
- **Grid.** `--grid NAME=V1,V2` per dimension, over `--weight` overrides and `--fusion`. The objective is the mean of the questions' and short queries' MRR on the tuning half, both filters. The best point is the one with the best plateau: its tuning score averaged with its neighbours' (the next weight either way, any other fusion). It counts as better only if it beats the base on both halves; derived sets are shown next to it as a guard.
- **Query log.** `cst-help serve --query-log FILE` appends one JSON line per search or lookup: time, Release, tool, arguments, Locators in order. `cst-help benchmark-drafts FILE` prints TOML entries for queries the benchmark doesn't ask yet, with the returned Locators as a comment and `sources = []` for a human to fill in. The loader refuses an entry without sources.

**First run on the development `.kb`** (Areas `3d`, `general`, `vba-3d`; 18 questions scored, 21 skipped). Ticket 06's ranks reproduce exactly. A 27-point grid (title 5/10/20, keywords 0.25/0.5/1, all three fusions) takes about 2 minutes:

| Settings | Tuning | Held-out |
|---|---|---|
| Ticket 06 (title 10, keywords 0.5, sum) | 0.631 | 0.497 |
| Best plateau (title 10, keywords 0.25, sum) | 0.654 | 0.507 |
| Same with rank fusion | 0.622 | 0.574 |

Title barely matters between 5 and 20. Lower keyword weights help a little on both halves. Rank fusion loses on tuning but gains most on held-out, so ticket 16 should look at it first. Normalising is worst everywhere. The defaults stay as ticket 06 left them; ticket 16 makes the tuning pass on the grown benchmark.
