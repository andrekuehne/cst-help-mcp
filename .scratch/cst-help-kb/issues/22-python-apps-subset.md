# 22: Python apps subset

**What to build:** The Library's 5 Python apps are copied into `library/Python/`: their descriptors and the modules that contain VBA strings or `cst.*` calls. The rest of the GUI framework and the wheels stay out. `library.md` lists each app by its menu name with its modules.

**Blocked by:** 17

**Status:** ready-for-agent

- [x] App descriptors give the menu names in `library.md`.
- [x] Only modules with VBA strings or `cst.*` calls are copied, and the selection is reported.
- [x] `AGENTS.md` says that VBA sent through `add_to_history` or `execute_vba_code` is found by grepping the string literals in these modules.

## Comments

**2026-10-25.** Shrunk for ADR 0014: no Sections and no usage index.

**2026-10-25.** Built. What the build does beyond the letter of the criteria, and why:

- **The five entry modules are copied too**, though four of them neither import `cst` nor hold VBA. They are what each descriptor's `-m` runs, so an app's row in `library.md` starts with a file that is in the tree.
- **"Drives CST"** means one of three things. The module imports the `cst` package. Or it calls a VBA object's member on a CST object held in a variable, the way `circuits/drivers/design_studio/read.py` calls `cmds.Block.Reset()` for the Place Lumped Elements app. Or it holds a string literal with a line starting `With X`, `End With`, `End Sub` or `End Function`. All found by `ast`, nothing run. None of the 53 modules left out has `add_to_history`, `execute_vba_code`, `End With` or a `cst.` call in its code.
- **Modules that drive CST but belong to none of the five apps are copied as well**: the `_impl/eda/emag/` tree, whose app descriptor ships only in the wheel, and the DDR5 AMI modules. `emag/_impl/vba_snippets.py` holds 22 of the VBA literals, more than any other module, and is the research note's own example. Under a strict reading of "the 5 apps' modules" they would be left out.
- **An app's modules** are its entry module, then the copied modules it imports directly or through others, as paths below `library/Python/lib/`. Each module also has its own row, with its dotted name and the first line of its docstring.
- **The descriptor's `restrict_to`** (`PCBS` for the PCB STUDIO demo) is a column of its own, "Restricted to". It is not an Application Filter, which is a file-name suffix.
- **The selection is reported** in `report.json` as `library_left_out`, the source paths of the modules not copied, and `counts.library_left_out`. The build's summary line prints the count. Wheels, icons and the package index stay out and are counted as unsupported by extension.
- **`AGENTS.md` of the full Release is 8,172 bytes.** The Python recipe and the wider `library/` and `library.md` descriptions added 222 bytes. To stay under 8 KB, these were cut: "Pages are short; most are under 10 KB", the Solver Parameters example of a dialog and its object (Port stays), "when one is good enough", "the layout" in the manual recipe, and "first steps" in the manuals row. The `Solver` example in Page anatomy was shortened. No agent run checked these cuts.
- **`scripts/agent-run.py`** names `library/Python/` the Area `python-apps`, apart from the help's `python`.
- **`GLOSSARY.md`** gains Python app.
