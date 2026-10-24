# 06: Search ranking

**What to build:** Search ranks Sections the way the spec describes. The exact API Entry table answers identifiers first. Behind it, an FTS5 index weights title above author keywords, keywords above table-of-contents path, then headings, then body, and a trigram index matches partial identifiers. Raw query text never reaches FTS5. Hits can be narrowed by Area and kind.

**Blocked by:** 05

**Status:** ready-for-agent

- [ ] Dotted names, `$` and other punctuation in queries never cause errors.
- [ ] A partial identifier such as `MeshProp` matches through the trigram index.
- [ ] Hits can be filtered to one or more Areas, and by kind (prose, code or all).
- [ ] Each hit shows its Locator, Release, Area, kind, title, heading path and snippet, plus generated and heuristic flags. A search returns at most 10 hits in about 3,000 tokens.
- [ ] The benchmark's solver and how-to questions for the proof-of-concept Areas are scored. Rank changes are tracked against the baseline; thresholds are set in ticket 16.
