# 06: Search ranking

**What to build:** Search ranks Sections the way the spec describes. The exact API Entry table answers identifiers first. Behind it, an FTS5 index weights title above author keywords, keywords above table-of-contents path, then headings, then body, and a trigram index matches partial identifiers. Raw query text never reaches FTS5. Hits can be narrowed by Area and kind.

**Blocked by:** 05

**Status:** ready-for-agent

- [x] Dotted names, `$` and other punctuation in queries never cause errors.
- [x] A partial identifier such as `MeshProp` matches through the trigram index.
- [x] Hits can be filtered to one or more Areas, and by kind (prose, code or all).
- [x] Each hit shows its Locator, Release, Area, kind, title, heading path and snippet, plus generated and heuristic flags. A search returns at most 10 hits in about 3,000 tokens.
- [x] The benchmark's solver and how-to questions for the proof-of-concept Areas are scored. Rank changes are tracked against the baseline; thresholds are set in ticket 16.

## Comments

**Implemented (2026-10-24).** `tests/test_search_ranking.py` checks ranking through `KnowledgeBase.search` against the real corpus, and `test_mcp_server.py` and `test_cli.py` check the `kind` parameter and the hit headings. The benchmark questions run on a new `release_kb` fixture that builds every Area read so far, which adds about 40 seconds to the suite. The full suite has 132 tests.

Decisions for later tickets:

- **Tiers** (`retrieval.search`): first the Sections of API Entries named in the query, in lookup's order, each with the entry's own Locator and its signature and description as snippet. Then Sections that match both words and partial names, then partial names only, then words only.
  - The API tier takes only words written like identifiers: dotted, with an underscore, or camelCase. Bare common words such as `Start`, `Name` or `Solver` would otherwise put dozens of entries first, so a lower-case `frequencyrange` falls through to BM25.
  - `api_entries.section` records the Section that holds each entry's anchor. It isn't always the Section's first anchor.
- **Word indexes:**
  - `sections_fts` holds each Section's title, headings and body, weighted 10, 3 and 1.
  - `documents_fts` holds each Document's author keywords and table-of-contents paths, weighted 0.5 and 0.25. Its BM25 score is added to every one of the Document's Sections.
  - Keywords and paths sit in a table of their own because FTS5's BM25 normalises by the length of the whole row. In the Section rows they penalised every Section of a Document with long keyword lists: "frequency range for the simulation" lost `Solver.FrequencyRange`.
  - The two scores come from different tables, so the weights aren't comparable across them. They were tuned on the solver and how-to questions below; the spec's order title > keywords > paths > headings > body holds only in effect. One test shows a keyword's pull ("advancing front mesher"); no test isolates the paths.
- **Trigram index** (`sections_trigram`): each Section's title, heading path and API signatures. A query word goes there when neither word index holds it (`sections_vocab`, `documents_vocab`) and it has three or more characters. Trigram matching is a substring match, so a typo rarely matches a name, but a truncated name does.
- **Kind:** `search(kind="prose"|"code"|"all")` sorts Documents by `model.CODE_KINDS`, which is empty until the Library readers (ticket 17) add their kinds. Until then `code` finds nothing.
- **Flags:** `Document.generated` (Guides) and `Document.heuristic` (Usages) are new, False everywhere so far. Hits show them after the Area and kind, as in `[vba-3d, topic, Release 2024]`.
- **Speed:** ranking selects ids only; snippets are computed for the final hits. A long question takes about 30 ms on the development `.kb`.
- **Benchmark baseline:** until ticket 07, the eight SOL and HOW questions sit in the test with their ranks before this ticket and now. The test fails when a rank gets worse than now.

| Question | Before 06 (unfiltered, Area) | Now |
|---|---|---|
| SOL-01 | 2, miss | 2, miss |
| SOL-02 | 1, 1 | 1, 1 |
| SOL-03 | 4, 3 | 3, 2 |
| SOL-04 | 1, 1 | **3**, 1 |
| HOW-01 | 1, 1 | 1, 1 |
| HOW-02 | 5, 5 | 4, 4 |
| HOW-03 | 1, 1 | 1, 1 |
| HOW-04 | 3, 3 | 1, 1 |

The sum of reciprocal ranks went from 10.15 to 11.17. SOL-04 dropped unfiltered: the AR filter dialog pages for post-processing and solver settings now rank first and second, ahead of the expected AR filter overview (third). Neither is an expected source, though both are plausible answers.

- **Open points.**
  - SOL-01 still misses when filtered to `3d`: the dialog says "Accuracy", the question says "time domain solver". This is a candidate for Synonym Sets (ticket 14).
  - Ticket 07 should replace the questions in the test with the machine-readable benchmark. Ticket 16 sets the thresholds.
  - The server instructions don't mention partial names or the `kind` filter yet.
