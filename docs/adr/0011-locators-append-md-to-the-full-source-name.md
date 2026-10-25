# Locators append `.md` to the full source file name

**Amended by ADR 0014.** The rule applies to rendered Documents. Files copied into the tree as they are (Library code, Material Definitions, PDFs) keep their original names, and their Locator is their path.

A Locator mirrors the source path: lowercased, with `Online Help/` and `mergedProjects/` dropped, and every run of characters outside `a-z 0-9 . _ - + ^` collapsed to `-`. It then appends `.md` to the complete file name, so `special_vbaports_planewave_object.htm` becomes `….htm.md` and `Farfield Result^+MWS+DS.rtp` becomes `farfield-result^+mws+ds.rtp.md`. Replacing the extension instead collides 11 times in the Library alone (`Evaluate Field Statistics.rtp` and `.txt`, `.json`/`.py` pairs), and collapsing `+` and `^` would merge Variants such as `PowerPoint Slide^+DS` and `^-DS`. A build that would still produce two equal Locators stops with an error. One rule for every Source means an agent can derive the file from any source path.

## Considered Options

- Replacing the extension (`….md`): prettier, but collision-prone.
- Collapsing `+` and `^` like other punctuation: merges Variants that CST treats as different files.
