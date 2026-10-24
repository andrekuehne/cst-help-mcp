# 08: Reading by Locator

**What to build:** `cst_help_read`, and a matching CLI command, returns a Section's or Document's Markdown by Locator. The text is byte-identical to the file in the tree (ADR 0003), paged at about 8,000 tokens with a cursor. Each page lists its outgoing links, with their status, and its image references.

**Blocked by:** 02, 04

**Status:** ready-for-agent

- [ ] Reading a Locator with an anchor returns that Section, and reading one without an anchor returns the Document.
- [ ] Long content is split into pages of about 8,000 tokens, and the cursor continues where the last page ended.
- [ ] The text equals the Markdown file's content for that range.
- [ ] Outgoing links come with their resolution status, and image references with their Asset ids and captions.
- [ ] An unknown Locator gives a clear error.
