# 10: MathJax TeX

**What to build:** On the help pages that load MathJax, the TeX is kept exactly as written and rendered as Markdown math. TeX is recognised only on those pages, honouring each page's delimiter configuration, so a literal `$` in VBA text elsewhere is never taken for math.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] `$...$`, `$$...$$`, `\(...\)`, `\[...\]` and `\begin{...}` environments are recognised on MathJax pages only.
- [ ] HTML entities inside TeX are decoded.
- [ ] Mis-paired `$` delimiters are reported in the build report rather than corrupting the surrounding text.
- [ ] The formulas on the THEO-01 and THEO-02 pages render, and their TeX is in the Markdown as written.
