# 18: Includes and Helpers

**What to build:** The Library's Includes become Documents of kind Include in Area `macros`. Their public procedures become Helpers that lookup can find. A Helper is labelled as not a documented CST API Entry, and shows its signature, its comment block, its defining Include, the `'#include` lines to paste, and how many files use it.

**Blocked by:** 17

**Status:** ready-for-agent

- [ ] `'#include` directives resolve against the Includes folder without regard to case, and every Library Document lists its includes as Locator links.
- [ ] Dependencies between Includes are computed, because they aren't declared. Each Include records what it requires and what requires it.
- [ ] Helpers rank after API Entries and are never merged with them. Names that collide with entry points are stored only in qualified form.
- [ ] The obsolete and unused Includes are indexed but flagged and ranked lowest.
- [ ] `GetLastResult_LIB` and `NoForbiddenFilenameCharacters` resolve through lookup, with the include lines in dependency order.
