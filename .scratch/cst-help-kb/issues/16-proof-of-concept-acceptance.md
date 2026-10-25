# 16: Proof-of-concept acceptance

**What to build:** The proof-of-concept slice of `cst-2024` is built from the real corpus and accepted as a folder: Areas `vba-3d`, `winwrap-basic`, `3d`, `general` and `python`, plus the two Word manuals, with the entry files and the workspace.

**Blocked by:** 10, 11, 12, 13, 15, 29

**Status:** ready-for-agent

- [ ] The full slice builds without errors, and the build report is reviewed.
- [ ] The agent run (ticket 29) covers every question whose Areas are built, from the generated `AGENTS.md`. Every question reaches an expected Document. The per-question counts are recorded in this ticket, per half and per category, and the thresholds in `docs/benchmark-draft.md` are confirmed or adjusted from them.
- [ ] Manual checks in Claude Code and in Cursor from a session opened in the folder: an identifier, a how-to, a figure (visible to the model from disk), and NODOC-01, where the agent says the item is not documented.
- [ ] The verify-in-CST items are checked or recorded as open: API-05, API-10, SOL-02, and whether `'#include` resolves for code sent through `add_to_history`.

## Comments

**2026-10-25.** Rewritten for ADR 0014. The earlier version set thresholds on ranker scores and planned a tuning pass; both went with the ranker. The experiment that replaced them is `../files-only-experiment.md`.
