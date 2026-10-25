# 10: MathJax TeX

**What to build:** On the help pages that load MathJax, the TeX is kept exactly as written and rendered as Markdown math. TeX is recognised only on those pages, honouring each page's delimiter configuration, so a literal `$` in VBA text elsewhere is never taken for math.

**Blocked by:** 04

**Status:** done

- [x] `$...$`, `$$...$$`, `\(...\)`, `\[...\]` and `\begin{...}` environments are recognised on MathJax pages only.
- [x] HTML entities inside TeX are decoded.
- [x] Mis-paired `$` delimiters are reported in the build report rather than corrupting the surrounding text.
- [x] The formulas on the THEO-01 and THEO-02 pages render, and their TeX is in the Markdown as written.

## Comments

**2026-10-25.** Implemented in `67ad743`. `tex.py` finds TeX the way MathJax 3 does: only in topics whose `<script>` loads MathJax, per run of text between tags (so a formula never spans a tag), with each topic's own `inlineMath`, `displayMath`, `ignoreHtmlClass` and `processHtmlClass`, and `\$` as text. Inline formulas render as `$...$`. Displayed ones (`$$`, `\[`, and `\begin{...}` environments, which keep their `\begin` and `\end`) become `equation` blocks inside `$$` fences, splitting the paragraph, note or field description they sat in. Covered by `tests/test_tex.py`; 113 tests pass in all.

The full development build reports `unpaired_math: 0`. The two mis-pairs in the corpus research were artefacts of a regex scan across tags: the impedance calculator's formulas pair within each paragraph, and the plane wave overview's `$` signs sit outside its `mathjax.*` class.

Decisions for later tickets:

- **Dollars.** On topics that load MathJax, a `$` that is text is written as `\$`, so that a Markdown renderer does not pair it with a formula. Topics without MathJax keep `Left$` raw; whether to escape there belongs to ticket 26.
- **Inline TeX** loses the spaces at its ends (`$ \vartheta$` → `$\vartheta$`), since Markdown reads `$` as math only without them. Otherwise TeX is as written, entities decoded.
- **Tables.** A `|` inside TeX in a GFM table cell is written `\|`, as the table syntax requires. GitHub removes the escape before rendering math, but the raw file shows `\|`. A displayed formula in a list item or a table cell stays on its line as `$$...$$`.
- **Link labels** are not read for math; no 3D topic has TeX in one.
- **Python.** The three Sphinx MathJax pages (`tex-chtml-full.js`) are left for ticket 12.
