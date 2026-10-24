# 13: Two Word manuals

**What to build:** A PDF reader (Docling, from the `build` extra, with OCR switched off) turns two Word manuals, "High Frequency Simulation" and "Getting Started", into Documents in Area `manuals`. Each is one Document with section anchors from the PDF's heading tags and page anchors. Conversion is cached. `cst_help_images` can render a page or a region of a page on demand.

**Blocked by:** 03, 09

**Status:** ready-for-agent

- [ ] A PDF without a text layer is a reported failure.
- [ ] Sections follow the tagged H1-H3 headings, every page has a `page-<n>` anchor, and running headers and footers are removed.
- [ ] The conversion cache is keyed by file content plus converter version and settings, and a rebuild with no changes skips conversion.
- [ ] PDF-01 and PDF-02 find their pages.
- [ ] Rendering a page or region at serve time needs no OCR or conversion dependencies.
- [ ] The build report notes whether formulas in these manuals come out as text glyphs. That decides whether Docling's formula model gets switched on.
