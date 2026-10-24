# 23: Multiple Collections and Releases

**What to build:** One Knowledge Base holds several Collections:
- a release-independent `pdf-folder` Collection, served with every Release, whose Documents state the CST version they were written for where it is known;
- more than one Release side by side, with the server choosing one at start;
- removing a Release, as an explicit command.

**Blocked by:** 03, 16

**Status:** ready-for-agent

- [ ] A release-independent Collection builds from its folder and appears in results for any served Release.
- [ ] With two Releases assembled, a server started for one never returns Documents from the other.
- [ ] Adding PDFs to the folder rebuilds only that Collection, and unchanged PDFs come from the cache.
- [ ] Removing a Release is an explicit command. Assembly afterwards leaves no trace of it.
- [ ] Synthetic fixtures cover the second Release and the PDF folder, because the corpus has neither.
