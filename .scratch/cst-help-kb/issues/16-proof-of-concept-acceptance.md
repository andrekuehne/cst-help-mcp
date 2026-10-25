# 16: Proof-of-concept acceptance

**What to build:** The proof-of-concept slice of `cst-2024` is built from the real corpus and accepted: Areas `vba-3d`, `winwrap-basic`, `3d`, `general` and `python`, plus the two Word manuals, with every tool, the entry files and the workspace.

**Blocked by:** 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 27, 28

**Status:** ready-for-agent

- [ ] The full slice builds without errors, and the build report is reviewed.
- [ ] A benchmark baseline is recorded for the built Areas, and pass thresholds are set from it. Thresholds are on hit@10 by Document (ticket 27), from the held-out half and from short queries.
- [ ] The manual checks run with the query log on. The queries the agents actually sent are turned into benchmark entries with expected sources, and become part of the held-out set.
- [ ] No tuning pass. The field weights stay the spec's order as ticket 06 left them; ranking is by structure (ticket 27) and the dialog pages are modelled as written (ticket 28). The per-category held-out scores and the runner's diagnosis of every miss are recorded in this ticket. Each miss the runner classes as a vocabulary gap gets a Synonym Set (ticket 14) or a note saying why not; the share of such misses is the evidence ADR 0008 asks for before embeddings are considered.
- [ ] Manual checks in Claude Code and in Cursor: lookup, search, read, images (figures are visible to the model), browse, and NODOC-01, where the agent says the item is not documented.
- [ ] Whether Cursor uses the server instructions is recorded.
- [ ] The verify-in-CST items are checked or recorded as open: API-05, API-10, SOL-02, and whether `'#include` resolves for code sent through `add_to_history`.

## Comments

**2026-10-25.** The tuning pass was dropped in favour of tickets 27 and 28; see `../search-ranking-proposal.md`. Ticket 07's first grid run had already shown that the weights are a poor lever: title barely matters between 5 and 20, and rank fusion lost on the tuning half while winning on the held-out half.

