# 22: Python apps subset

**What to build:** The Library's 5 Python apps are copied into `library/Python/`: their descriptors and the modules that contain VBA strings or `cst.*` calls. The rest of the GUI framework and the wheels stay out. `library.md` lists each app by its menu name with its modules.

**Blocked by:** 17

**Status:** ready-for-agent

- [ ] App descriptors give the menu names in `library.md`.
- [ ] Only modules with VBA strings or `cst.*` calls are copied, and the selection is reported.
- [ ] `AGENTS.md` says that VBA sent through `add_to_history` or `execute_vba_code` is found by grepping the string literals in these modules.

## Comments

**2026-10-25.** Shrunk for ADR 0014: no Sections and no usage index.
