# 09: Images

**What to build:** Images become Assets: deduplicated by content hash, with BMP and SVG converted to PNG at build time and derived copies scaled for clients. `cst_help_images` returns actual image content: one Asset, all figures of a Section, or a figure with its neighbours in document order.

**Blocked by:** 08

**Status:** ready-for-agent

- [ ] Every Asset records its caption or alt text, dimensions, kind (figure, icon or equation image) and the Documents that reference it.
- [ ] Inline icons stay as small images whose alt text comes from the file name. Logos and WebHelp chrome are dropped.
- [ ] Equation images are marked as not transcribed (ADR 0006).
- [ ] A call returns at most 4 PNG or JPEG images, scaled to at most 1,568 px on the long edge, with their captions. Icons are left out unless asked for.
- [ ] The figures of FIG-01 and FIG-02 can be retrieved. Manual check: Claude Code displays them.

## Comments

**2026-10-25, from ticket 08:** `cst_help_read` lists each page's outgoing links, but not its image references, because there are no Assets yet. Add them here: each page should list the Asset ids and captions of the images its text shows (`reading.Page`, next to `links`).
