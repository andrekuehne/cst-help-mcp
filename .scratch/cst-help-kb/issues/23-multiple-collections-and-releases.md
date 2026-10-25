# 23: Multiple Collections and Releases

**What to build:** One Knowledge Base holds several Collections as sibling folders: `cst-2024/`, later `cst-2025/`, and a release-independent `pdfs/` built from a folder of PDFs the way ticket 13 builds manuals. Each Release folder has its own `AGENTS.md` naming its Release. The root `AGENTS.md` lists the Releases, says a session works in one, and points at `pdfs/`. Removing a Release is an explicit command.

**Blocked by:** 13, 29

**Status:** ready-for-agent

- [ ] A release-independent Collection builds from its folder into `pdfs/` with its own index file, and its Documents state the CST version they were written for where it is known.
- [ ] With two Releases assembled, each folder's `AGENTS.md` names its Release, and the root `AGENTS.md` tells an agent to stay in one.
- [ ] Adding PDFs to the folder rebuilds only that Collection.
- [ ] Removing a Release is an explicit command, and assembly afterwards leaves no trace of it.
- [ ] Synthetic fixtures cover the second Release and the PDF folder, because the corpus has neither.

## Comments

**2026-10-25.** Rewritten for ADR 0014: "served with every Release" becomes "a sibling folder every Release's `AGENTS.md` points at".
