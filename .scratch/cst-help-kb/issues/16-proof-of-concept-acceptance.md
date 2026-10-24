# 16: Proof-of-concept acceptance

**What to build:** The proof-of-concept slice of `cst-2024` is built from the real corpus and accepted: Areas `vba-3d`, `winwrap-basic`, `3d`, `general` and `python`, plus the two Word manuals, with every tool, the entry files and the workspace.

**Blocked by:** 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15

**Status:** ready-for-agent

- [ ] The full slice builds without errors, and the build report is reviewed.
- [ ] A benchmark baseline is recorded for the built Areas, and pass thresholds are set from it. Thresholds come from the held-out half and from short queries, not from the questions the weights were tuned on.
- [ ] The manual checks run with the query log on. The queries the agents actually sent are turned into benchmark entries with expected sources, and become part of the held-out set.
- [ ] One tuning pass runs with the grown benchmark: weight grid, and if needed one score scale for Sections and Documents. The chosen weights, the plateau around them, and the per-category held-out scores are recorded in this ticket, replacing ticket 06's provisional weights.
- [ ] Manual checks in Claude Code and in Cursor: lookup, search, read, images (figures are visible to the model), browse, and NODOC-01, where the agent says the item is not documented.
- [ ] Whether Cursor uses the server instructions is recorded.
- [ ] The verify-in-CST items are checked or recorded as open: API-05, API-10, SOL-02, and whether `'#include` resolves for code sent through `add_to_history`.
