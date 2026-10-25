# Proposal: rank search by structure, not by fitted weights

Status: accepted 2026-10-25; carried out by tickets 27 and 28, with ticket 16 and ADR 0008 amended. Written after inspecting tickets 06, 07, 14 and 16, `retrieval.py`,
`benchmark.py` and the development `.kb` (Areas `3d`, `general`, `vba-3d`; 9,218 Sections, 1,514
Documents). The numbers below come from throwaway scripts run against that `.kb`; none of the code
in `src/` was changed.

## The concern, restated

Ticket 06 tuned five BM25 field weights on eight questions, ticket 07 built a grid search over
them with a tuning/held-out split, and ticket 16 plans "one tuning pass" on the grown benchmark.
That path fits a handful of magnitudes to 39 questions we wrote ourselves. It can only ever tell
us that *these* questions rank well, and the first run already shows how noisy it is: title
barely matters between 5 and 20, rank fusion loses on tuning and wins on held-out.

The spec's actual goal (stories 61 to 67) is that an agent, reading at most 10 hits, finds the
defining page for the words it typed, for any question. The way forward is to make ranking
insensitive to the weights, so there is nothing left to tune, and to evaluate with signals the
corpus and real sessions give us rather than with questions we invented.

## What the misses actually are

A diagnosis of all 102 scored probes (18 questions, each as full text and two short queries,
unfiltered and filtered) against the development `.kb`:

- **Almost no vocabulary gaps.** In nearly every probe, every content word of the query occurs in
  the expected Document's indexed text. The only genuine gap is TERM-02 ("radiation pattern" for
  farfield). Words such as "macro", "GHz", "temporarily" are missing from the expected page, but
  the page still ranks because the other words match.
- **The expected Document is in BM25's candidates, just low.** For every miss it sits at rank
  12 to 195 of the OR-matched candidates. So this is a ranking-shape problem, not recall, and
  not a reason for embeddings (ADR 0008 holds).
- **What outranks it has three shapes**, none of which a weight fixes:
  1. **Siblings flood the top 10.** "farfield monitor" returns six member Sections of the Monitor
     Object page. VBA pages have 18.7 Sections per Document; today's top 10 holds 5.3 distinct
     Documents on average.
  2. **Short pages beat long defining pages.** 60% of 3D Documents (649 of 1,087) are one empty
     title Section plus one huge content Section whose heading is the ribbon path ("Simulation:
     Solver > Setup Solver"). SOL-01's Time Domain Solver Parameters page is 12 KB in one
     Section, so BM25's length normalisation puts it at rank 28 behind "LF Time Domain Solver
     Parameters" and "Signals in Time Domain Simulations", which say the same words in less text.
     Its dialog fields exist as `field` blocks (935 of 1,042 3D Documents have them) but are
     indexed only in the body.
  3. **One heavy field match beats a full match.** Title weighs 10 and every Section of a
     Document carries the title, so a Section matching one word in its title ("solver") outranks
     a Section matching all four query words in headings and body. The spec asks for "title >
     keywords > paths > headings > body", which is a statement about ties, not about one title
     word being worth ten body words.

## Proposal

### 1. Rank by coverage first, BM25 second, and show one Document once

Two changes with no parameters:

- **Coverage first.** Order candidates by how many distinct query words they match (in the
  Section's title, headings and body, or in its Document's keywords and table-of-contents paths),
  then by today's BM25 sum within each coverage level. "A page about all your words beats a page
  about one of them." The existing tiers (API Entries, then partial names) stay above it.
- **At most two Sections per Document** in the 10 hits, the best ones. The rest of a Document is
  one `cst_help_read` away.

Prototyped on the 102 probes, weights untouched:

| Variant | hit@5 | hit@10 | MRR | distinct Documents in top 10 | held-out hit@10 | held-out MRR |
|---|---|---|---|---|---|---|
| today | 80% | 85% | 0.572 | 5.3 | 83% | 0.483 |
| coverage first | 82% | 87% | 0.675 | 6.8 | 83% | 0.546 |
| coverage first + 2 per Document | 82% | 90% | 0.678 | 8.3 | 88% | 0.552 |
| 2 per Document only | 80% | 87% | 0.573 | 7.0 | 83% | 0.458 |

The gain on the held-out half is as large as on the tuning half, which is what a structural fix
should look like and what a fitted weight never did. Once coverage leads, the field weights only
break ties among Sections that match the same words, so the spec's order can stay as a prior and
the grid search becomes unnecessary.

Cost: one FTS5 rowid query per query word (the inverted index answers these in milliseconds),
then set lookups over the 100 to 300 candidates. Well inside today's 30 ms.

### 2. Fix the Section model of dialog pages, which is a reader concern, not a ranking one

- **The ribbon path is metadata, not a heading.** "Simulation: Solver > Setup Solver" tells an
  agent where the dialog lives in the UI (valuable for how-to questions) and should be a
  Document field indexed like `toc_paths`, not the heading of the whole page. As a heading it
  makes "solver", "setup" and "simulation" heavy and useless. These pages also have empty
  `toc_paths` and `breadcrumbs` today, although story 32 wants the breadcrumb as the path.
- **Dialog frames and fields are the sub-structure.** Index `field` terms in the headings field,
  or start a Section per frame. Then "Accuracy" on the Solver Parameters page is a heading
  match, which is what it is in the dialog.
- **Navigation-only Sections** ("Contents", "See also", a lone breadcrumb line, 1,366 Sections
  have an empty body) should not be search hits. Dropping them alone slightly hurt in the
  prototype because they sometimes stand in for their Document; with "2 per Document" they are
  harmless, so this is a cleanliness fix rather than a ranking one.

### 3. Phrase and proximity before scattering

CST's vocabulary is made of two-word terms ("time domain", "waveguide port", "parameter sweep",
"steady state"). A Section where the query's adjacent words occur adjacently should rank above
one where they are scattered. FTS5 phrase queries and `NEAR` give this for free as a tier between
"all words" and "some words". No weight involved; worth prototyping after 1 and 2 land.

### 4. Evaluate with signals that are not ours

- **The benchmark becomes a regression guard, not a tuning target.** Score hit@10 by distinct
  Document (what an agent can act on), keep MRR as information, and set thresholds on the
  held-out half as ticket 16 says. Drop the "one tuning pass" and the grid from ticket 16's plan;
  keep `--grid` as a tool for experiments.
- **The runner diagnoses each miss.** For every miss, report whether the expected Document was
  (a) outside the candidates, (b) in the candidates but outranked, and (c) which query words it
  lacks. This is the trigger ADR 0008 asks for: embeddings are considered when class (a) with
  missing words grows, not when MRR disappoints. Today that class is one question.
- **More self-labelled probes, from how the authors refer to pages.** Beyond keywords, TOC
  names and API names (ticket 07), the corpus has thousands of **link labels**: the words an
  author used, on another page, to point at a Document. They are paraphrases written by the
  vendor, not by us, and they are diverse ("see the AR filter overview" → the AR filter page).
  "See also" lists and the "Related topics" blocks are the same kind of signal. These sets are
  generated at run time and hold only labels and Locators, like the existing derived sets.
- **Real sessions as the ground truth.** The query log (ticket 07) already records searches and
  lookups. Record `cst_help_read` too, and the runner can then extract (query → Document read
  next) pairs from the manual checks of ticket 16 as weak labels, and measure task success as
  "the agent read an expected Document within N tool calls", not "rank 1 matched our pick".
  This is the only measure that is not artificial, and it also records the reformulations agents
  make, which tell us which vocabulary gaps are real.

### 5. Let the agent be the reranker

The consumer reads all 10 hits and can refine. Two cheap changes make that work better than any
weight:

- Show, per hit, which query words it matched ("matches: time, domain, accuracy"). The agent
  sees coverage and can judge a hit without reading it.
- Within the 3,000-token budget, after the 10 hits, list further matching Documents as one line
  each (title and Locator) when they exist. Ten such lines cost about 200 tokens and turn a miss
  at rank 14 into a hit the agent can read.

### 6. Vocabulary gaps stay a separate, small mechanism

Synonym Sets (ticket 14) remain the tool for the few genuine gaps (TERM-02). Grow them from
evidence the runner now labels (class (a) misses) and from mined sources before hand-writing:
the author keyword index is already a synonym list (it has "Transient Solver Parameters" for the
time domain solver page), and link labels are another. The ticket's rule, "every set must be
justified by a question that failed without it", stays.

## Effect on the tickets

- **New ticket 27, "Search ranking by structure"**, blocked by 06 and 07, before 16: coverage
  first, two Sections per Document, matched words per hit, the runner's miss diagnosis, link-label
  derived set, `cst_help_read` in the query log. Acceptance: the four tracked tables keep their
  ranks or improve, hit@10 by Document improves on the held-out half, no weight changes.
- **New ticket 28, "Dialog pages: ribbon path as metadata, fields as headings"**, a reader
  change under ticket 04's rules, blocked by 04 and 05. Acceptance: SOL-01 filtered to `3d`
  finds the Solver Parameters page; `toc_paths`/ribbon path populated for dialog pages; the
  Markdown shows the ribbon path as a field, not a heading.
- **Ticket 16**: replace "One tuning pass runs with the grown benchmark" by "the benchmark
  thresholds (hit@10 by Document, held-out) are set from the baseline after tickets 27 and 28; the
  weights stay the spec's prior; the miss diagnosis is reviewed and each vocabulary-gap miss gets
  a Synonym Set or a note".
- **Ticket 14**: unchanged in substance; its first sets are justified by diagnosed gaps, and it
  mines the keyword index and link labels before adding hand-written sets.
- **ADR 0008**: add one sentence. The trigger for embeddings is the share of misses the runner
  classifies as vocabulary gaps, not an overall score.

## What this does not claim

- The prototype used my own stop-word list and read candidate text in Python; a real
  implementation computes coverage from FTS5 postings. Numbers will move a little.
- 18 of 39 questions are scored today; the Library and Python Areas may add miss shapes of their
  own (code Sections, Display Names). Coverage-first and per-Document grouping are generic, but
  code Sections will need their own fields as the spec already says.
- Phrase tiers (section 3) are untested here.
