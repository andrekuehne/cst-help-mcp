# 23: Multiple Collections and Releases

**What to build:** One Knowledge Base holds several Collections as sibling folders: `cst-2024/`, later `cst-2025/`, and a release-independent `pdfs/` built from a folder of PDFs the way ticket 13 builds manuals. Each Release folder has its own `AGENTS.md` naming its Release. The root `AGENTS.md` lists the Releases, says a session works in one, and points at `pdfs/`. Removing a Release is an explicit command.

**Blocked by:** 13, 29

**Status:** done

- [x] A release-independent Collection builds from its folder into `pdfs/` with its own index file, and its Documents state the CST version they were written for where it is known.
- [x] With two Releases assembled, each folder's `AGENTS.md` names its Release, and the root `AGENTS.md` tells an agent to stay in one.
- [x] Adding PDFs to the folder rebuilds only that Collection.
- [x] Removing a Release is an explicit command, and assembly afterwards leaves no trace of it.
- [x] Synthetic fixtures cover the second Release and the PDF folder, because the corpus has neither.

## Comments

**2026-10-25.** Rewritten for ADR 0014: "served with every Release" becomes "a sibling folder every Release's `AGENTS.md` points at".

**2026-10-26.** Implemented. A `pdf-folder` Source makes a Collection release-independent: it takes no `release` and no other Source type (config rejects a mix). Its PDFs, at any depth, are copied as they are with Text Companions at `<path>.pdf.md`, Area `pdfs`. Their frontmatter has `cst_version` instead of `release` when the file name, the PDF title or the first five lines of page 1 name one ("CST Studio Suite 2023"). Body text further on is not read, so a passing mention of another version can't be mistaken for it. The index file is `documents.md`, rendered at assembly from `documents.json` beside the Build, one line per PDF with its pages and "written for CST <v>" or "CST version unknown". `validate` checks it is there.

Assembly writes:
- a Release's `AGENTS.md`, with a "Beside this Release" section listing `../pdfs/` and how to `--add-dir` it;
- the release-independent folder's own short `AGENTS.md` and `CLAUDE.md`, with no `work/` or `guides/` (a session works in a Release);
- a root `AGENTS.md` and `CLAUDE.md` listing the Releases and the release-independent Collections, which say to stay in one Release. ADR 0013 is amended for this.

`cst-help instructions` now also prints the release-independent folders and points the project section at them.

`cst-help remove <collection> --kb <kb>` assembles the remaining Collections first. It then deletes the Collection's Builds (manifests first, so a locked file can't bring it back) and its view, including that view's `work/` and `guides/`. It refuses an unknown Collection and the last one. Covered by `tests/test_collections.py` (synthetic second Release and PDF folder). The full suite passes.

Left open:
- `build pdfs` builds only that Collection, but its assembly still re-links every Release's view. That is cheap on the synthetic fixtures and is ADR 0009's design; it has not been timed on a full Release.
- `remove` deletes what agents wrote into the removed Release's `work/` and `guides/`, as "leaves no trace" asks. The README says so.
