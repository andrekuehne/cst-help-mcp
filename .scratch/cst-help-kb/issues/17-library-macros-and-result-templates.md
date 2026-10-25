# 17: Library as files

**What to build:** The `cst-release` Source copies the Library's Macros, Result Templates and Includes into the tree under `library/`, with their original names and folder structure, so agents grep working code the way they grep any repository. A generated `library.md` indexes them one line per file. There are no Sections, no Display Name table and no Usage index: grep over `library/` is all of those.

**Blocked by:** 29

**Status:** done

- [x] `library/Macros/`, `library/Result Templates/` and `library/Includes/` hold the text files (`.mcr`, `.mcs`, `.rtp`, `.bas`, `.cls`, `.txt`) as they are, re-encoded from cp1252 to UTF-8, with the original names kept. Executables, Office files, wheels and project files are left out. Scrambled Macros are listed in `library.md` but not copied.
- [x] `library.md` has one line per file: kind (control macro, structure macro, Result Template, Include, helper script), menu path and Display Name (folder path plus file stem before `^`), Application Filter, Variants, and the first comment line. An Include's line also names its public procedures.
- [x] Dialog bitmaps become PNG Assets next to the Macros that load them, since Read opens PNG and not BMP.
- [x] `AGENTS.md` gains the Library recipes: find working code for an API Entry with a grep over `library/`; a `'#include "X"` line points at `library/Includes/X`; a public procedure in an Include is a Helper and not a documented CST API Entry; a member used in `library/` but absent from `vba_3d/` is an Undocumented Member and is reported as such.
- [x] LIB-01 to LIB-05 reach their files in the agent run, and `GetLastResult_LIB` is found by grep in its Include.

## Comments

**2026-10-25.** Shrunk for ADR 0014, and absorbs ticket 18. The earlier version parsed each file into Sections with per-procedure anchors, built a Display Name lookup and computed Include dependencies. Copying the files and indexing them one line each gives agents the same reach with grep.

**2026-10-25.** Built. What the build does beyond the letter of the criteria, and why:

- **Includes are `.lib` files**, so `.lib` is copied too; the list above names only the other extensions. The two small `.lib` overrides in `Macros/Results/Eye Diagram, TDR, etc/` are labelled Include as well.
- **Line endings become LF** along with the re-encoding, like every other file in the tree, so a grep's `$` anchors work.
- **A `.txt` without procedures** (the port-extension and 5G data tables) has the kind `text`, a sixth kind; a `.txt` with procedures is a helper script.
- **Every BMP becomes a PNG where it sits**, including the 8 whose names the Macros build at run time. They are files beside the Macros, not entries of `assets.json`.
- **Helpers** are an Include's procedures that are not `Private`, without the debug entry points named `Main…`.
- **The first comment line** is the first comment with a letter in it that is not a `'#` directive or the menu-title guard. For some files that is a heading such as "History of Changes".
- **A release folder without `Library/Macros`, `Library/Result Templates` or `Library/Includes` is not recognised**, like one without a help project.
- **`AGENTS.md` of the full Release is 8,175 bytes.** The Library adds a folder row, the `library.md` entry and a Working code recipe; the Undocumented Member rule was already there for a folder with a Library. To stay under 8 KB, the recipe "Where a setting lives in the UI" was dropped (Page anatomy says the same of the Ribbon Path line), along with "There is no search server", "(no context lines)" in the concept recipe (the rules say it) and the `**Group**` note on WinWrap pages. The manual recipe was tightened.
- **`scripts/agent-run.py`** maps a `Library/…` source to `library/…` and counts each Library folder as an Area (`result-templates`, `macros`, `includes`).

Agent run on the full Release (Claude Code 2.1.310, `--model sonnet`, Read/Grep/Glob only), LIB-01 to LIB-05: 5 of 5 reached an expected Document, median 5 calls, maximum 9 (LIB-01 2, LIB-03 4, LIB-04 5, LIB-02 7, LIB-05 9). The script's FAIL line is about the median of 4, which the criterion here does not ask for of these five alone. No agent read `AGENTS.md` as call 1: `CLAUDE.md` imports it, so it was already in context. These counts don't compare call for call with runs where call 1 was that read (the script prints a note for each). `GetLastResult_LIB` is defined in `library/Includes/template_conversions.lib` and is listed among that Include's Helpers in `library.md` (tested).
