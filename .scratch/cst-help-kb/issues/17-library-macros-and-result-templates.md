# 17: Library as files

**What to build:** The `cst-release` Source copies the Library's Macros, Result Templates and Includes into the tree under `library/`, with their original names and folder structure, so agents grep working code the way they grep any repository. A generated `library.md` indexes them one line per file. There are no Sections, no Display Name table and no Usage index: grep over `library/` is all of those.

**Blocked by:** 29

**Status:** ready-for-agent

- [ ] `library/Macros/`, `library/Result Templates/` and `library/Includes/` hold the text files (`.mcr`, `.mcs`, `.rtp`, `.bas`, `.cls`, `.txt`) as they are, re-encoded from cp1252 to UTF-8, with the original names kept. Executables, Office files, wheels and project files are left out. Scrambled Macros are listed in `library.md` but not copied.
- [ ] `library.md` has one line per file: kind (control macro, structure macro, Result Template, Include, helper script), menu path and Display Name (folder path plus file stem before `^`), Application Filter, Variants, and the first comment line. An Include's line also names its public procedures.
- [ ] Dialog bitmaps become PNG Assets next to the Macros that load them, since Read opens PNG and not BMP.
- [ ] `AGENTS.md` gains the Library recipes: find working code for an API Entry with a grep over `library/`; a `'#include "X"` line points at `library/Includes/X`; a public procedure in an Include is a Helper and not a documented CST API Entry; a member used in `library/` but absent from `vba_3d/` is an Undocumented Member and is reported as such.
- [ ] LIB-01 to LIB-05 reach their files in the agent run, and `GetLastResult_LIB` is found by grep in its Include.

## Comments

**2026-10-25.** Shrunk for ADR 0014, and absorbs ticket 18. The earlier version parsed each file into Sections with per-procedure anchors, built a Display Name lookup and computed Include dependencies. Copying the files and indexing them one line each gives agents the same reach with grep.
