# 08: Reading by Locator

**What to build:** `cst_help_read`, and a matching CLI command, returns a Section's or Document's Markdown by Locator. The text is byte-identical to the file in the tree (ADR 0003), paged at about 8,000 tokens with a cursor. Each page lists its outgoing links, with their status, and its image references.

**Blocked by:** 02, 04

**Status:** ready-for-agent

- [x] Reading a Locator with an anchor returns that Section, and reading one without an anchor returns the Document.
- [x] Long content is split into pages of about 8,000 tokens, and the cursor continues where the last page ended.
- [x] The text equals the Markdown file's content for that range.
- [x] Outgoing links come with their resolution status, and image references with their Asset ids and captions. (Image references done in ticket 09.)
- [x] An unknown Locator gives a clear error.

## Comments

**2026-10-25, implementation:** `KnowledgeBase.read`, the `cst_help_read` tool and `cst-help read` are done. Pages are cut where the rendered parts of a Document meet (`render.render_parts`), so a page's text is a slice of the file and lists the links it shows. A page's text plus its list of links stays within 24,000 characters (8,000 tokens at the server's pessimistic three characters per token). The cursor is the next page's number. Reads come from the Build the open assembly holds, so a running server keeps reading the Build it searches.

Outgoing links are listed with their status. Image references aren't yet: the build doesn't make Assets until ticket 09, so that half of the fourth criterion is left to 09.
