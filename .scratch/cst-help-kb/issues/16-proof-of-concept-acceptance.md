# 16: Proof-of-concept acceptance

**What to build:** The proof-of-concept slice of `cst-2024` is built from the real corpus and accepted: Areas `vba-3d`, `winwrap-basic`, `3d`, `general` and `python`, plus the two Word manuals, with every tool, the entry files and the workspace.

**Blocked by:** 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15

**Status:** ready-for-agent

- [ ] The full slice builds without errors, and the build report is reviewed.
- [ ] A benchmark baseline is recorded for the built Areas, and pass thresholds are set from it.
- [ ] Manual checks in Claude Code and in Cursor: lookup, search, read, images (figures are visible to the model), browse, and NODOC-01, where the agent says the item is not documented.
- [ ] Whether Cursor uses the server instructions is recorded.
- [ ] The verify-in-CST items are checked or recorded as open: API-05, API-10, SOL-02, and whether `'#include` resolves for code sent through `add_to_history`.
