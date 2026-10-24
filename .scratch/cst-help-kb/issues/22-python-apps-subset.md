# 22: Python apps subset

**What to build:** The Library's Python apps become Area `python-apps`, covering the 5 apps, their descriptors, and the modules that contain VBA strings or `cst.*` calls. The rest of the GUI framework and the wheels stay out.

**Blocked by:** 17

**Status:** ready-for-agent

- [ ] App descriptors give the menu names.
- [ ] Python Sections are split at `def` and `class`.
- [ ] VBA held in strings and sent through `add_to_history` or `execute_vba_code` counts toward the usage index.
- [ ] Search and lookup reach these modules by app name and by API Entry Usage.
