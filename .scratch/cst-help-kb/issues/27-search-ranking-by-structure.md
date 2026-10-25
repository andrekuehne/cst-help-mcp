# 27: Search ranking by structure

**What to build:** Search ranks by structure instead of by fitted field weights, as the search ranking proposal laid out (deleted with ADR 0014; in git history). After the API Entry tier, candidates are ordered by how many distinct query words they match, then by today's BM25 sum within each level; a Document appears at most twice among the hits, with its best Sections. Each hit says which query words it matched, and the hits are followed by a one-line list of further matching Documents within the search budget. The benchmark runner scores hit@10 by Document, diagnoses every miss, gains a derived set of link labels, and the query log records reads. The field weights stay the spec's order (title, keywords, paths, headings, body) and are not tuned.

**Blocked by:** 06, 07

**Status:** wontfix

- [ ] Candidates from the word indexes are ordered by the number of distinct query words they match (in the Section's title, headings and body, or in its Document's keywords and table-of-contents paths), then by the BM25 sum. The API Entry tier and the partial-name tier keep their places. Coverage comes from FTS5 postings per query word, not from reading candidate text; a long question still ranks in about 30 ms on the development `.kb`.
- [ ] At most two Sections of one Document appear among the hits, the best-ranked ones. The CLI and the server instructions say that the rest of a Document is one `cst_help_read` away.
- [ ] Each hit lists the query words it matched, after its heading path.
- [ ] When more Documents matched than the hits show, the search result ends with one line per further Document (title, Locator), as many as fit the 3,000-token budget, headed "Also matched". The hits themselves stay at most 10.
- [ ] The runner reports hit@10 by Document next to hit@5 and MRR, per set, filter, half and category. Thresholds in ticket 16 are set on hit@10 by Document.
- [ ] The runner diagnoses every miss: whether the expected Document was among the word indexes' candidates at all, its rank there if it was, and which content words of the query occur nowhere in its indexed text. Misses are summarised by class, so the trigger of ADR 0008 (vocabulary gaps) can be read off the report.
- [ ] A derived set `links` is generated at run time from the built Knowledge Base: each resolved link's label text, as a query, finds the Document it points to. Labels that equal the target's title, labels of a single word, and labels that are bare identifiers (those belong to the `api` set) are left out. Like the other derived sets it stores only labels and Locators, is sampled by hash and split by `half_of`.
- [ ] The query log also records `cst_help_read` (Locator and cursor), so a logged session yields query-to-Document pairs. `cst-help benchmark-drafts` fills a draft's `sources` from the Documents read within the next three calls of the same session, marked as drafted for a human to confirm.
- [ ] The eight tracked questions keep or improve their recorded ranks. Hit@10 by Document improves on the held-out half of the questions and of the short queries against the baseline recorded below, with the default `Ranking`. The derived sets do not get worse. The ranks before and after are recorded in this ticket.
- [ ] No weight in `Ranking` changes in this ticket. `--grid` and `--weight` stay as tools for experiments.

## Baseline before this ticket (development `.kb`, Areas `3d`, `general`, `vba-3d`, 2026-10-25)

All 102 scored probes of 18 questions (full text and short queries, unfiltered and filtered), with the default `Ranking`. The prototype column is from a throwaway script that read candidate text in Python and used its own stop-word list, so the implementation's numbers will differ a little.

| | hit@5 | hit@10 | MRR | distinct Documents in top 10 | held-out hit@10 | held-out MRR |
|---|---|---|---|---|---|---|
| today | 80% | 85% | 0.572 | 5.3 | 83% | 0.483 |
| prototype: coverage first, two Sections per Document | 82% | 90% | 0.678 | 8.3 | 88% | 0.552 |

## Comments

**2026-10-25, from the proposal.** The misses the benchmark shows today are not vocabulary gaps: in nearly every probe every content word of the query occurs in the expected Document, and the Document sits among BM25's candidates at rank 12 to 195. What outranks it is sibling Sections of one Document, shorter pages that say the same words in less text, and Sections that match one heavy field (the title, copied into every Section) rather than all the words. Coverage first and two Sections per Document address the first and third; ticket 28 addresses the second. A phrase or `NEAR` tier for CST's two-word terms ("time domain", "waveguide port") is a candidate follow-up, untested; if it is tried, it goes between the all-words level and the rest, with no weight.

**2026-10-25, retired.** The ranker it would have improved is removed. Agents reading file paths do not have its miss shapes: the SOL-01 page the ranker put at rank 28 was found with one title grep in both runs. See ADR 0014 and `../files-only-experiment.md`.
