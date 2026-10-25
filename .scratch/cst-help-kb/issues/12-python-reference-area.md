# 12: Python reference Area

**What to build:** A Sphinx reader turns the Python reference into Area `python`. Its classes, methods, properties and functions become API Entries under their dotted names, taken from the Sphinx inventory and anchored to their entries.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Content comes from the Sphinx main region, without sidebars or navigation bars, and keeps headings, code blocks, admonitions and math.
- [ ] Every inventory object becomes an API Entry with its signature and parameters, taken from its entry on the page.
- [ ] Links from Sphinx pages into the RoboHelp help resolve to Locators.
- [ ] The RoboHelp topics about Python (`mergedProjects/Python/python_overview.htm`, and the root `menu.htm` and `user_scipts.htm`, which ticket 04 reads into `general`) move to Area `python`. Their links into the Sphinx pages resolve.
- [ ] API-08 and API-09 reach their pages in the agent run, and their entries are in `api.md`.
