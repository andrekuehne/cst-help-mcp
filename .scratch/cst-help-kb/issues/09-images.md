# 09: Images

**What to build:** Images become Assets: deduplicated by content hash, with BMP and SVG converted to PNG at build time and derived copies scaled for clients. `cst_help_images` returns actual image content: one Asset, all figures of a Section, or a figure with its neighbours in document order.

**Blocked by:** 08

**Status:** ready-for-agent

- [x] Every Asset records its caption or alt text, dimensions, kind (figure, icon or equation image) and the Documents that reference it.
- [x] Inline icons stay as small images whose alt text comes from the file name. Logos and WebHelp chrome are dropped.
- [x] Equation images are marked as not transcribed (ADR 0006).
- [x] A call returns at most 4 PNG or JPEG images, scaled to at most 1,568 px on the long edge, with their captions. Icons are left out unless asked for.
- [x] The figures of FIG-01 and FIG-02 can be retrieved. Manual check: Claude Code displays them.

## Comments

**2026-10-25, from ticket 08:** `cst_help_read` lists each page's outgoing links, but not its image references, because there are no Assets yet. Add them here: each page should list the Asset ids and captions of the images its text shows (`reading.Page`, next to `links`).

**2026-10-25, implementation:** The reader turns each `<img>` into an image span in the block's text, and an image-only paragraph into a `figure` block. The per-page logos and WebHelp skin images are dropped. Alt text that only names a file (`image\brick.gif`) counts as none. At build time `assets.write_assets` reads every image a Document shows, finding it in the release folder without regard to case. Images are deduplicated by the SHA-256 of their bytes, and the Asset id is its first 12 hex digits. Assets are written to `<tree>/assets/<id>.png|jpg`:

- PNG and JPEG are kept byte for byte.
- BMP, GIF, SVG (rendered with resvg) and anything else become PNG. An animated GIF keeps its first frame.
- An image longer than 1,568 px also gets a `<id>.1568.<ext>` copy, which the server returns.

`assets/assets.json` lists each Asset's kind, caption, size, sources and Documents, so the files show what the server shows (ADR 0003). The assembled database gets an `assets` table.

- **Kinds:** an image under `icon_images/` is an icon. One whose file name says formula, formel, equation or corrformular is an equation image, whatever its size. Otherwise an image of 32 px or less is an icon.
- **Captions:** an Asset's caption is the first alt text a Document gives it. An icon without one is named after its file (`solver transient icon`).
- **Markdown:** images render as `![label](assets/<id>.png)`. An equation's label says "equation image, not transcribed", and a missing image shows its alt text or file name.
- **Report:** it counts Assets and lists missing ones. Image files no longer count as unsupported.
- **Retrieval:** `KnowledgeBase.images` and `cst_help_images` return:
  - the figures of a Section, or of a whole Document without an anchor;
  - Assets by id;
  - one Asset with up to 3 neighbours either side, in document order.

  Each call returns at most 4 images and lists the rest by id.
- **Reading:** `cst_help_read` pages now list the Asset ids, kinds and captions of the images they show, within the page budget. This finishes ticket 08's fourth criterion.

Pillow and resvg-py are in the `build` extra. The server only reads the files the build wrote.

Not done here:
- **Captions** come from alt text only, and CST rarely writes any. The captions in figure-grid cells (such as the polarization page) are not attached to their figures. FIG-01 and FIG-02 have no caption, so agents should read the surrounding Section.
- **SVG:** no Area built so far references an SVG. The Filter Designer theory SVGs arrive with ticket 21, and SVG conversion is covered by a synthetic test only. Ticket 21 should also add the Filter Designer SVGs to the equation rule, and Innovasys and Sphinx chrome to the dropped images.
- **Uncounted images:** image files no Document shows are neither Assets nor counted in the report.

**2026-10-25, manual check:** Passed. In Claude Code, `cst_help_images` returned images that Claude Code displayed, among them figures of farfield patterns.
