# 13: Two Word manuals

**What to build:** The two Word manuals, "High Frequency Simulation" and "Getting Started", join the tree as files in Area `manuals`: the PDF itself, copied as it is, and beside it a `<name>.pdf.md` with the text of every page under a `page-<n>` anchor, extracted with pypdf. Agents grep the text and open the PDF by page with their Read tool when layout or a figure matters.

**Blocked by:** 29

**Status:** ready-for-agent

- [ ] Each manual is copied unchanged and gets a text companion with frontmatter (title, source, page count) and one `## page-<n>` section per page.
- [ ] A PDF without a text layer is a reported failure.
- [ ] `AGENTS.md` names the `manuals/` folder and says to grep the companion and read the PDF page.
- [ ] PDF-01 and PDF-02 reach their pages in the agent run.

## Comments

**2026-10-25.** Shrunk for ADR 0014. Docling, the conversion cache, heading-tagged Sections and on-demand page rendering are gone: Claude Code and Codex read PDF pages from disk, and pypdf text is enough to find the page.
