# CST Studio Suite 2024 `Library` folder: profile

Facts gathered from the `Library` folder of a CST Studio Suite 2024 installation (macros, Result Templates and Python packages), to decide how the Knowledge Base covers example code. Nothing under `.ingestion/` was modified.

- **Root:** `.ingestion/2024/Library/` (local, licensed copy; not committed, see ADR 0001). It has five subfolders: `Includes/`, `Macros/`, `Materials/`, `Python/` and `Result Templates/`. `Includes/` and `Materials/` were copied after sections 1 to 7 were written. Sections 8 and 9 profile them and supersede the earlier statements that the include libraries are absent (sections 4.1, 5 and 7, hazard 6).
- **Path convention:** unless prefixed with `Online Help/`, every path below is relative to `.ingestion/2024/Library/`. `mP/` abbreviates `Online Help/mergedProjects/`.
- **Method:** Python 3.12 standard-library scans (`os.walk`, `hashlib`, `re`, `ast`, `zipfile`, `zlib`, `html.parser`). Wheels were listed with `zipfile`, never extracted or imported, and no Library code was run. `pypdf` is not installed, so PDF text layers were checked by inflating content streams. Counts are exact for what was scanned. Where a count depends on a heuristic (API usage, near-duplicates, title matching), the text says so.
- **Excerpts** show structure only, mostly with placeholders. Vendor code and comments are left out on purpose.
- **Terms** follow `GLOSSARY.md`. "The Library" means CST's folder of that name (CST calls its location the *Global Library Path*). It is not a synonym for Collection; see the glossary note under Design implications.

---

## 1. Inventory

**727 files, 252.5 MB.** About 79% of the bytes are Python wheels. The code itself is small: 562 text files hold 9.5 MB and 247,509 lines.

By extension:

| Extension | Files | MB | What it is |
|---|---:|---:|---|
| .whl | 14 | 199.57 | Python wheels in a local package index (`Python/repo/simple/`) |
| .bmp | 71 | 37.36 | Pictures shown in macro dialogs |
| .rtp | 163 | 4.21 | Result Templates (VBA) |
| .mcr | 211 | 4.13 | Control macros (VBA) |
| .ppt / .pptx / .doc | 7 / 1 / 2 | 1.85 / 0.09 / 0.51 | Companion slides and manuals next to some macros |
| .xlsm | 1 | 1.72 | `Macros/Wizard/CST-Via-Wizard.xlsm`, which contains a VBA project |
| .mcs | 62 | 0.81 | Structure macros (VBA) |
| .py | 83 | 0.69 | Python sources (82 in `Python/lib/cstapps/`, 1 in `Macros/`) |
| .pdf | 5 | 0.60 | Companion manuals and slides |
| .bas | 20 | 0.39 | VBA helper scripts |
| .txt | 19 | 0.29 | VBA include bodies, data tables, readme files |
| .cls | 6 | 0.12 | VBA class modules |
| other: .cst 3, .ffconfig 19, .json 5, .html 7, .png 10, .svg 7, .cfg 3, .reg 2, .lib 2, .exe 1, .bat 1, .pfc 1, no extension 1 | 62 | 0.19 | Projects, presets, app descriptors, package index, icons, registry files, a helper executable |

### Per top-level subtree

| Subtree | Files | MB | Dominant content |
|---|---:|---:|---|
| `Macros/` | 402 | 47.73 | 211 .mcr, 62 .mcs, 10 .bas, 6 .cls; 71 .bmp (37.4 MB); 16 companion documents |
| `Result Templates/` | 200 | 4.47 | 163 .rtp, 10 .bas, 8 .txt, 19 .ffconfig, `Readme.txt` |
| `Python/lib/` | 104 | 0.74 | the `cstapps` package: 82 .py, 5 .json app descriptors, 17 icons |
| `Python/repo/` | 21 | 199.58 | a PEP 503 "simple" index (`index.html`, generator `simple503 version 0.4.0`) with 14 wheels |

### The folders form a category tree

- **`Macros/`**: 11 categories with 35 subcategories, at most two levels deep. 143 files sit directly in a category and 259 in a subcategory.

  | Category | Subcategories | Code files (.mcr/.mcs/.bas) | MB |
  |---|---:|---:|---:|
  | Construct | 11 (Coils, Demo Examples, Electronics Cooling, Vias, …) | 88 | 10.35 |
  | Solver | 13 (A-Solver, Mesh, Ports, Sources, High Performance Computing, …) | 68 | 1.79 |
  | Results | 10 (`- Import and Export`, EMC, Farfield, Tables, …) | 48 | 1.67 |
  | Calculate | 1 (Heat Transfer Coefficient) | 20 | 25.16 (bitmaps) |
  | Materials | 0 | 16 | 3.24 |
  | File | 0 | 13 | 0.19 |
  | Report and Graphics | 0 | 9 (+1 .cls) | 0.18 |
  | Wizard | 0 | 8 | 2.47 |
  | Converter | 0 | 6 | 0.23 |
  | Matching Circuits | 0 | 4 | 2.43 |
  | Parameters | 0 | 3 | 0.02 |

- **`Result Templates/`**: 16 categories, one level deep: `0D`, `1D`, `2D and 3D Field Results` (32 .rtp), `AntennaPlacement`, `EMC`, `Farfield and Antenna Properties` (17), `Filter Analysis`, `General 1D` (11), `MRI Toolbox`, `Misc` (29), `Optical`, `Particles` (13), `S-Parameters` (12), `Statics and Low Frequency` (13), `Thermal`, `Time Signals`. The one level-2 folder, `Farfield and Antenna Properties/FarfieldResult_QuickSettings/`, holds data, not templates (19 presets, section 2.4).
  - **`0D` and `1D` are legacy.** `Result Templates/Readme.txt` says templates in those two folders "cannot be accessed from within the GUI anymore" (backward compatibility with 2010 and older).
- **The tree is the GUI menu.** The help says macros are started "from the hierarchical structure in the Macros menu" (`Online Help/vba/vba_macro_language_overview.htm`). It writes them as menu paths, for example "Results / Farfield / Total Radiated Power (TRP)" for `Macros/Results/Farfield/Show Total Radiated Power (TRP)^+MWS.mcr` (`mP/3D/common_preloadedmacro/common_preloadedmacro_preloaded_macros_overview.htm`).
- **`Python/`** is a package layout, not a category tree. It goes up to six levels deep (`Python/lib/cstapps/_impl/eda/emag/_impl/…`). Its user-facing categories come from the app descriptors instead (`"name": "EDA/Multilayer PCB Setup"`, section 2.6).

---

## 2. File kinds and formats

### 2.1 Encoding and line endings

| Kind | Files | Encoding | Line endings |
|---|---:|---|---|
| .mcr | 211 | 204 ASCII; **7 contain cp1252 bytes** (degree signs and similar in strings and comments, for example `Macros/Results/Eye Diagram, TDR, etc/PDA (Peak Distortion Analysis)^+DS.mcr`); no BOM | CRLF |
| .mcs, .rtp, .bas, .cls, .lib, .pfc, .txt, .ffconfig, .cfg, .reg, .bat, .json, README | all | ASCII, no BOM | CRLF |
| .py | 83 | ASCII, no BOM | CRLF (78); 5 are empty (0 bytes) |
| .svg | 7 | ASCII | CRLF; one also has bare CR (`Python/lib/cstapps/_impl/eda/emag/assets/pcb_button.svg`) |
| .html (package index) | 7 | ASCII, `<meta charset="UTF-8" />` | CRLF |

- No file has a BOM, a NUL byte or a control character. UTF-8 never appears, so **cp1252 decoding reads every text file correctly**, and ASCII files decode the same either way.
- **Tabs indent the VBA**: 148,137 of 247,509 text lines contain a tab. There are 4,072 ` _` line continuations, 561 lines longer than 200 characters (the longest is 1,285, in `Macros/Solver/Sources/Analytical Farfield Source^+MWS.mcr`) and 4,485 lines with trailing whitespace. **No line contains three backticks**, so Markdown fences are safe.

### 2.2 Macros: `.mcr` (control) and `.mcs` (structure)

The help defines the two kinds. "Structure macros (identified by their .mcs file extension)" are stored in the history list when run; the other kind are control macros, and "A control macro always has a * sign in front of its name" (`Online Help/vba/vba_macro_language_overview.htm`). `.mcr` as the control-macro extension is an inference: no `.mcr` uses `*`-less structure syntax, and 27 `.mcr` carry the `*`.

| Feature | .mcr (211) | .mcs (62) | How detected |
|---|---:|---:|---|
| `Sub Main` | 206 (the other 5 are scrambled) | 62 | regex on `Sub Main` |
| `Option Explicit` | 157 | 36 | |
| `'#Language "WWB-COM"` (WinWrap Basic language pragma) | 75 | 4 | |
| `'#include "<file>"` | 96 | 3 | |
| `'#Uses "<file>.cls"` | 2 | 0 | |
| `Begin Dialog` … `End Dialog` (files / dialogs) | 168 / 202 | 34 / 40 | |
| `BeginHide` … `EndHide` (removed before writing to the history list) | 5 | 58 | |
| `'@ <caption>` history-list block markers | 2 | 32 | 972 marker lines in total, across all kinds |
| `AddToHistory` / `AddToHistoryNoModelChange` | 79 | 23 | 774 call lines in 109 files, all kinds |
| `StartHelp` with a literal or `HelpFileName` argument (files / resolving to a help page) | 44 / 40 | 24 / 19 | section 2.8 (.rtp: 55 / 48) |
| Menu-title guard line | 29 | 33 | see below |
| Legacy `' macro.NNN` id | 21 | 8 | |
| Dated change-history lines | 160 | 34 | `DD-Mon-YYYY initials: text` |
| Copyright line | 50 | 0 | |
| Size: lines, median / max | 195 / 5,509 (scrambled) | 341 / 1,679 | |

**Header comments are informal; there are no metadata fields.**

- **Title:** 62 files start with a menu-title guard, which is a comment followed by a fixed warning line:
  ```vb
  ' *<Category> / <Name>
  ' !!! Do not change the line above !!!
  ```
  The `*` marks a control macro (27 files). These titles are **legacy and often disagree with the current file location**. For example, `Macros/Construct/Demo Examples/Dipole Antenna^+MWS.mcs` is titled "Construct / Online / Dipole Antenna", and `Macros/File/Open directory Global Library Path.mcr` is titled "File / Open directory Global Macro Path". Elsewhere the first line is a comment (131 .mcr and 27 .mcs, counting `'#Language` pragmas), `Option Explicit` (19), blank (16), `Dim` or `Sub` (13), or `Scrambled` (5). Only about 65 of the 220 macros whose first line is a comment repeat the display name there.
- **Description:** free-form comment lines when present.
- **Author:** initials only, inside history lines (`ube`, `fsr`, `set2`).
- **Version:** none. The `' macro.NNN` ids are a leftover of the older naming scheme `macro.000` (preloaded macros "start at 500", `vba_macro_language_overview.htm`). They are not unique: 546 is used by both `Calculate Wavelength.mcr` and `Create Drude Material for Optical Applications^+MWS+PS.mcr`, and 561 by both `PowerPoint Slide` variants.
- **History:** 3,120 dated lines in 358 files, dated 2001 to February 2024.

**Structure macros are recorded history.** A typical `.mcs` (`Macros/Construct/Demo Examples/Dipole Antenna^+MWS.mcs`) has this shape, with no code shown:

```vb
' <Category> / <Name>
' !!! Do not change the line above !!!
Sub Main ()
BeginHide
    StoreDoubleParameter "<p>", <value> ...
EndHide
'@ <history caption>
With <Object>
     .Reset
     .<Member> "<value>"
     .Create
End With
...
```

**Control macros often build history commands as strings.** 796 string literals start with `With <Object>`, and 7,384 start with `.<Member>`, in 86 files. They are passed to `AddToHistory`, which is the same mechanism the Control Server uses. Section 4 counts these.

### 2.3 Result Templates: `.rtp` and how they differ from Macros

A Result Template has no `Sub Main` (0 of 163). The template-based post-processing framework calls named functions instead. `mP/3D/common_macro/post_processing_template_layout.htm` documents the contract:

- `Function Define(sName As String, bCreate As Boolean, bNameChanged As Boolean) As Boolean` must exist. It must call `StoreTemplateSetting("TemplateType", …)` and, in the current layout, `StoreTemplateSetting("EvaluationType", "single_run" | "all_runs")`.
- **Current layout:** `Evaluate0DResult`, `Evaluate1DResult` and `Evaluate1DCResult`, each `(resultID As String, indexMultiple As Long, templateName As String, returnMultipleName as String) As Object`.
- **Legacy layout** (used when `EvaluationType` is not set): `Evaluate0D() As Double`, `Evaluate1D()`, `Evaluate1DComplex()`, `EvaluateMultiple0D/1D/1DComplex(nCount, sName, sTableName)`.
- Settings are stored with `StoreScriptSetting` and read with `GetScriptSetting`. `ActivateScriptSettings` and `ClearScriptSettings` are for testing outside the framework.

What the files actually use:

| Feature | .rtp (163) |
|---|---:|
| `Function Define` | 152 |
| Legacy layout (`Evaluate0D`, `Evaluate1D`, `EvaluateMultiple*` and similar) | **130** |
| Current layout (`Evaluate0DResult`, `Evaluate1DResult`, `Evaluate1DCResult`) | **22** |
| Pointer files: no procedures, only `'#include` of another template | 11 |
| `TemplateType` literal values (all .rtp and include bodies) | 0D 84, 1D 61, M1D 21, M0D 19, 1DC 17, M1DC 14, expression 15 |
| `EvaluationType` values | single_run 17, all_runs 9 |
| Debug entry points `Sub Main2` / `Sub Main_RTP` / `Main1D` | 74 / 45 / 6 |
| `'#include` | 153 |
| `'#Language "WWB-COM"` | 18 |
| `Begin Dialog` (files / dialogs) | 142 / 218 |
| `' Post Processing Template: <title>` header line | 73 (some titles empty or wrong, section 3) |
| Copyright line (`' Copyright <years> Dassault Systemes Deutschland GmbH`) | 94 |
| Size: lines, median / max | 361 / **12,608** (`Result Templates/Time Signals/Eye Diagram Tool^+DS+MWS.rtp`) |

- `GetResultTemplateDialogType` occurs nowhere in the Library or the help. Framework calls that do occur include `GetTemplateAborted` (22 files), `ActivateScriptSettings` (156), `ClearScriptSettings` (154), `StoreTemplateSetting` (155), and the include helper `GetLastResult_LIB` (14).
- **Pointer files** delegate to other templates. For example, `Result Templates/Filter Analysis/Group Delay Time^+MWS.rtp` contains only includes, ending in `'#include "..\Result Templates\Time Signals\Group Delay Time^+MWS.rtp"`. 11 such relative includes exist, and all 11 resolve (section 5).
- **Include bodies** are code in `.txt` files that the GUI does not list. Examples are `Result Templates/2D and 3D Field Results/Evaluate Field Statistics-v2.txt`, `CombinePowerLoss-Template.txt` and `Loss from E-v1.txt`. 6 of the 8 `.txt` files there are code with `Define` / `Evaluate*`, `Run VBA Code-Examples.txt` is a 24-line snippet without procedures, and `Readme.txt` is prose.
- **Helper `.bas` scripts** are code-generation templates. For example, `Result Templates/1D/+ Mix 1D Results^-DS.rtp` reads `…\Result Templates\1D\mix1d_template.bas` and runs a modified copy written to the project's result folder with `RunScript`.

### 2.4 Presets: `.ffconfig`

There are 19 files in `Result Templates/Farfield and Antenna Properties/FarfieldResult_QuickSettings/`. The Farfield Result template loads them from `sConfigFilePath` (`Farfield Result^+MWS+DS.rtp`). Each one is `key=value` lines after a first line `CSTPRELOADEDCANNOTBECHANGED`, for example `TemplateType=1D`. The file names are user-facing preset names such as "Max Gain over Frequency" and "Total radiated power (TRP, full sphere) over frequency".

### 2.5 Other VBA kinds

- **`.bas` (20).** `Macros/Converter/*.bas` and `Macros/File/ADS Converter *.bas` form an ADS import tool chain that calls itself through `RunScript` (section 5). The largest is 4,308 lines. `Result Templates/{0D,1D,General 1D}/*.bas` are the helper scripts above. All 20 have `Sub Main`; 3 carry a guard title.
- **`.cls` (6)** are class modules with a `VERSION 1.0 CLASS` / `Attribute VB_Name` header, used through `'#Uses "<name>.cls"`. Examples are `Macros/Report and Graphics/WordReport.cls` and five HPC scheduler classes in `Macros/Solver/High Performance Computing/`. All 11 `'#Uses` resolve inside the same folder. The WinWrap reference documents `'#Uses` (`Online Help/sax_basic/ww_00030.htm`, "Class Module").
- **`.lib` (2)**: `Macros/Results/Eye Diagram, TDR, etc/CST_Compatibilty_Settings_{DS,MWS}.lib`. These are 11-line files, and one redefines `SelectTreeItem` as an empty Sub for an application where it is unavailable.
- **`.pfc` (1)**: `Macros/Solver/E-Solver/Model.pfc`, a user-defined parameter-sweep watch (`Sub ParameterSweepWatch`).
- **`.txt` in `Macros/` (11):** one is VBA (`Macros/Results/Statespace/ExtractStatespace.txt`, 471 lines). The others are data tables (`Macros/Solver/Ports/Calculate port extension coefficient_*.txt`, `Macros/Wizard/5G-Code*.txt`).
- `Macros/Solver/High Performance Computing/README` is plain text and points to an external PDF.

### 2.6 Python

- **`Python/lib/cstapps/`** is a 19,613-line application framework: 82 modules, PySide2 GUI code, EDA and LF apps. 79 of its 82 modules are byte-identical, modulo CRLF, to the `cstapps/` content of `Python/repo/simple/cst_apps-0.0.693-py3-none-any.whl`. The wheel adds `cstapps/apps/extraction.py` and `cli_extraction.py`.
  - All 83 `.py` files parse with `ast`. 13 have a module docstring, and 17 start with a `#` comment. There is no common header and no title field.
  - **App descriptors**: five `Python/lib/cstapps/apps/*.json` files hold `name`, `program` (`${python_interpreter}`), `args` (`-m cstapps.apps.<module>`, `--cst_pid ${CST_STUDIO_PID}`, `--prj ${CST_ACTIVE_PROJECT}`), `show_console_window` and `keep_open`. `name` is a menu path such as `"EDA/Multilayer PCB Setup"` or `"MATERIALS/Fit Generalized Debye"`. One descriptor is named differently from its module: `pleos.json` runs `place_lumped_elements_on_schematic`.
  - **Python that writes VBA**: 45 string constants contain VBA (`With …`, `.Reset`, `End With`). They are sent through `.model3d.add_to_history(…)` (21 calls) and `.schematic.execute_vba_code(…)` (8), for example in `Python/lib/cstapps/_impl/eda/emag/_impl/vba_snippets.py` and `…/_impl/mws.py`. This is the path the Control Server uses.
- **`Macros/Results/- Import and Export/WriteModelicaFile.py`** imports only `os` and `sys`. A macro starts it through `Shell` with `GetInstallPath + "\AMD64\python\python.exe"`.
- **`Python/repo/simple/`** holds the following wheels, all binary or packaging:

  | Wheel | Contents |
  |---|---|
  | `cst_results_2024_linux_x86_64-0.0.16-cp{37…311}` (5 × 37 MB) | `cst/results/__init__.py`, `.so` binaries (61 MB unpacked) |
  | `cst_results_2024_win_amd64-0.0.15-cp{37…311}` (5 × 2.9 MB) | a `.pyd`, DLLs and **two `.pyi` type stubs** |
  | `cst_results_2024-0.0.86-py3-none-any` | a meta-package that selects the platform wheel |
  | `cst_studio_suite_link-2024.2.1201136.551` | 3 small `.py` files and a `.pth`, `Requires-Python: >=3.7, < 3.11` |
  | `activate_opera_python-1.0.0.7` | a DLL-path helper |
  | `cst_apps-0.0.693` | as above |

  No wheel declares a license or ships a LICENSE file. Two give the author as `PVN2@3ds.com`.

### 2.7 Images, companion documents and other binaries

- **BMP (71, 37.4 MB)**: 24-bit (55), 8-bit (14) or 4-bit (2), from 62×69 to 794×1123 px, median about 824×100. Dialogs load them by path (`GetInstallPath + "\Library\Macros\…\<name>.bmp"`) or by quoted file name. 63 are referenced from code. The 8 that are not are `Macros/Calculate/OptWG-*.bmp` (7 × 2.2 MB) and `RLCG.bmp`; their names are probably built at run time. The images were not viewed. Their names (`Calculate analytical Line Impedance_coax.bmp`, `TabSI_TwoSidedCoating.BMP`, `*_pict.bmp`) suggest geometry and parameter sketches. Any text in them stays untranscribed under ADR 0006.
- **Companion documents next to code**, matched by file stem:

  | Files | Kind |
  |---|---|
  | `Macros/Construct/Convert Single Ended to Mixed Mode.{pdf,ppt}` | PDF (Adobe PDF Library 9.0, text layer, about 5 pages) and OLE2 PPT |
  | `Macros/Construct/Miscellaneous/Bend Selected Objects at UV Plane.{pdf,ppt,cst}` | PDF (PowerPoint 2010, text) + **a `.ppt` that is really a ZIP/PPTX** + demo project |
  | `Macros/Construct/Miscellaneous/Cut Selected Objects into Checkerboard Pieces.{pdf,ppt,cst}` | PDF (text) + OLE2 PPT + demo project |
  | `Macros/Construct/FastHenry/{CST2FastHenry_UserManual,FastHenry2CST}.{doc,pdf}` | PDF (Acrobat Distiller 9.5.5, text) + OLE2 DOC |
  | `Macros/Construct/Parts/Reflector_ Dish-HELP.pptx` | PPTX, 2 slides |
  | `Macros/Materials/Create Drude Material for Optical Applications - Help.ppt`, `Macros/Results/Eye Diagram, TDR, etc/{TDR Cross Probing,Time gating for output signal_Example}.ppt`, `Macros/Wizard/Thermal Power Rating Sweep.ppt` | OLE2 PPT with no PDF counterpart |

  - All 5 PDFs are born-digital, with `BT`/`Tf` text operators in their inflated streams.
  - No code file references any companion document. The link exists only through the shared file stem.
  - There are no `.htm` files in the Library.
- **`.cst` projects (3)** start with the bytes `DE 03 04`, which look like a ZIP local header with altered magic. They are `Bend Selected Objects at UV Plane.cst`, `Cut Selected Objects into Checkerboard Pieces.cst` and `Macros/Wizard/empty.cst`.
- **Executables and system files** that must never be run or served:
  - `Macros/Matching Circuits/GetOptenniLabDirectory.exe` (a PE executable);
  - `Macros/File/CSTdebug-{add,remove}.reg` (registry edits);
  - `Macros/Wizard/via.bat`;
  - `Macros/Wizard/CST-Via-Wizard.xlsm`, which has a `vbaProject` and 42 worksheets.

### 2.8 Documentation of the Library in the Online Help

- **`mP/3D/common_preloadedmacro/`** has 109 help pages (`common_preloadedmacro_*.htm` plus `5g_code_book.htm`). Two of them are overviews, `…_preloaded_macros_overview.htm` and `…_preloaded_result_templates.htm`. The 3D TOC lists only those two overviews; the 3D index references 68 distinct pages in the folder (`mP/3D/whxdata/whidata0_xml.js`).
- **Framework and concept pages:**
  - `mP/3D/common_macro/post_processing_template_layout.htm` (the Result Template contract);
  - `mP/3D/common_overview/common_overview_template_based_pp_overview.htm` and `mP/DES/analysis/postprocessing/templatebasedpostprocessingoverview.htm` (naming rules, section 3);
  - `Online Help/vba/vba_macro_language_overview.htm` (control and structure macros, `BeginHide`/`Assign`, Global Library Path).
- **Code links to help by page name.**
  - 126 code files call `StartHelp "<page>"` or `StartHelp HelpFileName` with a `Const HelpFileName = "<page>"`. 110 of them resolve to at least one help page, 83 distinct pages in all, 79 of them in `common_preloadedmacro/`.
  - **Resolution must be case-insensitive.** 25 of the 38 resolved `HelpFileName` constants differ in case from the file, for example `common_preloadedmacro_farfield_TRP` → `common_preloadedmacro_farfield_trp.htm`.
  - 16 targets do not resolve: 13 name pages that do not exist, for example `common_preloadedmacro_farfield_TIS` and `common_preloadedmacro_Construct_Fan`, and 3 are empty strings.
- **Help links back to code only by name.**
  - 68 of the 109 pages have a title (`Category / Name`) whose last part equals a Library display name after normalisation. 20 more are reached only through a `StartHelp` link.
  - 21 match nothing. Some are overviews. Others describe items absent from this Library, which suggests stale or renamed pages: `…_0d___dq_model.htm` ("0D / dq Model"), `…_farfield_slant_polarization.htm`, `…_file_multi_column_to_2_column.htm`, `…_wizard_parameter_+_mesh_study.htm`.
  - Of 338 longer display names (at least 3 words and 14 characters), 84 appear verbatim in help text: 148 page hits in `common_preloadedmacro/`, plus `mP/EXP_HF/examplesoverview` 14, `mP/3D/special_solvopt` 7 and a few elsewhere.
- **About three quarters of the Library has no help page.** Only 110 of 476 readable VBA files link to one. For the rest, the code, its comments and its dialog labels are the only documentation.
- **`cstapps` is not documented.** `cstapps`, `cst-apps` and "python apps" appear nowhere in the help. The include libraries (`vba_globals_all.lib` and others) are not documented either; `'#include` is mentioned only on `common_preloadedmacro_wizard_compare_multiple_runs.htm` and `vba_macro_language_overview.htm`.

---

## 3. Naming and display names

### 3.1 File name convention

```
<Display Name>[^<application filter>].<ext>
```

- The CST GUI shows the folder path plus the file stem before `^`. Vendor code confirms the rule: `Macros/Results/Tables/Apply Result Template to Parametric Data^-DS.mcr` lists templates by splitting the file name at `^` and `.rtp`. The same code applies the filter, keeping a file when its name has no `-<App>`, and either no `^` or a `+<App>` for the running application (`GetApplicationName()`, where every `DS…` counts as `DS`). The help itself does not document the `^` suffix anywhere.
- **Filter values** on the 456 macro, template and `.bas` files:

  | Suffix | Files |
  |---|---:|
  | `^+MWS` | 128 |
  | `^-DS` | 87 |
  | none | 62 |
  | `^+DS` | 42 |
  | `^+MWS+DS` | 31 |
  | `^+EMS` | 29 |
  | `^+PS` | 27 |
  | `^+MWS+PS` | 18 |
  | `^+MPS` | 13 |
  | rarer combinations, plus `^DS` (4 legacy `.bas`), `^WIN` (1) and `^-EMS-DS` (1) | 19 |

  The tokens are application short names: MWS (high frequency), DS (Design Studio and schematic), EMS (low frequency), PS (particles), MPS (multiphysics). `+` means shown only there, `-` means hidden there.
- **Leading `- ` (23 names)**: "Templates with a "-" sign in front of their name do not add useful results to the Navigation Tree Tables folder, but store their results at other locations" (`mP/3D/common_overview/common_overview_template_based_pp_overview.htm`, and the DES equivalent). It is also used for the macro subcategory `Macros/Results/- Import and Export/`. A leading `+ ` occurs on 3 legacy files in `Result Templates/1D/`.

### 3.2 Display names used by CST and its help

- The help writes **menu paths with abbreviations**, for example "Farfield&Antenna / Farfield Result" for `Result Templates/Farfield and Antenna Properties/Farfield Result^+MWS+DS.rtp` (`common_preloadedmacro_0d_farfield.htm`), and "General / Load 1D Data File (project and external)" for `Result Templates/General 1D/Load 1D Data File (project and external)^-DS.rtp`.
- **Other names inside files are unreliable:**
  - The guard titles are stale (section 2.2).
  - The `' Post Processing Template:` header titles (73 .rtp) often differ from the display name, and some are copy-paste leftovers:
    - `Farfield Result` → "Farfield Computation";
    - `3D Eigenmode Result` → "3D Eigenvalue result";
    - `Export Phase Center^+MWS+DS.rtp` → "Evaluate Field Statistics (Histogram, etc)";
    - `HAC (…)^+MWS.rtp` → "0D Value from 3D Result";
    - `Farfield Radiation from Selected Solids` → "Farfield probes".
- **"Farfield Postprocessing Template" does not match one file.** 18 `.rtp` mention "farfield" in their folder, display name or header title, and 9 have it in the display name. The intended file, `Farfield Result^+MWS+DS.rtp`, matches only through several weak signals: its folder, the help title "Farfield&Antenna / Farfield Result", its header "Farfield Computation", and its being the template the preset folder belongs to. A file title such as "Show Total Radiated Power (TRP)" or "Farfield Result" does match exactly, but may have variants (3.3).

### 3.3 Collisions and variants

- **Same folder, same display name, different filter: 16 pairs.** Examples are `Result Templates/S-Parameters/Y Parameter^+DS.rtp` and `^+MWS.rtp`, `Macros/Report and Graphics/PowerPoint Slide^+DS.mcr` and `^-DS.mcr`, and `Result Templates/1D/mix1d_template.bas` and `mix1d_template^DS.bas`. The contents differ: the `HAC (…)` pair has a Jaccard similarity of distinct non-comment lines of 0.65, but the `Y Parameter` and `Z Parameter` pairs only 0.24 and 0.23, so they are separate implementations.
- **Same display name in different folders: 15.** Some are exact copies (section 6). Others differ, for example `Macros/Solver/A-Solver/Calculate scattered fields^+MWS.mcr` and `…/I-Solver/…`. `Peak Field Values from Probes` exists as a macro (`Macros/Results/EMC/…^+MWS.mcr`) and as two templates (`Result Templates/2D and 3D Field Results/…^+MWS+DS.rtp`, `Result Templates/EMC/…^+MWS+DS.rtp`).
- **Odd characters.** Among all 727 file names, the characters outside `[A-Za-z0-9._-]` are space (528 names), `^` (394), `+` (303), `(` and `)` (30), `,` (10) and `=` (6). No name contains `#`. One folder has a comma (`Eye Diagram, TDR, etc`).
  - One file has a space before its extension: `Macros/Solver/Mesh/Hex Mesh - Refinement between Snapped Meshlines^-DS .mcr`.
  - One has a double space: `Macros/Construct/Parts/NASA  Almond^-DS.mcs`.
  - The longest path is 154 characters.
- **Case:** lowercasing every path produces **no collisions**.
- **Replacing the extension with `.md` produces 11 collisions.** The groups are:
  - `Result Templates/2D and 3D Field Results/Evaluate Field Statistics.rtp` and `.txt`, both code;
  - four `Python/lib/cstapps/apps/<name>.json` and `.py` pairs;
  - `Macros/Solver/Ports/Calculate port extension coefficient_SL.bmp` and `.txt`;
  - five groups of companion documents (`.pdf`/`.ppt`/`.doc`/`.cst`).

---

## 4. API usage

Heuristic, regex-based scans over the 476 readable VBA files and the 83 Python files. The API Entry lists came from the help:

- **VBA:** 316 object pages in `mP/VBA_3D` and `mP/VBA_DES` (`p.VBA-Heading-Object`, `p.VBA-Heading-Method`), with 5,835 object and member pairs, about 5,500 after merging objects documented in both projects.
- **Python:** 764 entries in `Online Help/Python/objects.inv`.

### 4.1 VBA

| Measure | Value |
|---|---:|
| `With <X>` blocks in code | 1,175 (181 distinct heads) |
| `With <X>` blocks inside string literals (history commands built as strings) | 796 in 86 files |
| Distinct `Object.Member` pairs with a known object, outside strings | 1,441 (1,172 with a documented member) |
| … including pairs inside string literals | **2,153 (1,674 documented, about 30% of the documented members)** |
| Objects referenced at least once | 122 of about 300 |
| Distinct unqualified Application/Project methods used (`SelectTreeItem`, `GetProjectPath`, …) | 106 |
| Distinct API references per file (median / p90 / max), outside strings | 10 / 41 / 275; 32 files have none |

Files referencing selected identifiers, by plain token match outside strings and comments:

| Identifier | Files | Identifier | Files |
|---|---:|---|---:|
| ResultTree | 172 | Solver | 60 |
| StoreTemplateSetting | 155 | Result1DComplex | 58 |
| Units | 153 | Mesh | 53 |
| GetScriptSetting | 151 | Material | 37 |
| StoreScriptSetting | 147 | Port | 36 |
| SelectTreeItem | 135 | DSResultTree | 34 |
| AddToHistory | 104 | Brick | 30 |
| Result1D | 101 | Monitor | 22 |
| DS (Design Studio object prefix) | 87 | Result3D | 18 |
| BeginHide | 66 | **FarfieldPlot** | **17** |
| Result0D | 16 | Plot1D | 14 |
| RunScript | 14 | ParameterSweep | 12 |

Notes:

- **Many calls are unqualified.** `SelectTreeItem`, `GetProjectPath`, `StoreScriptSetting`, `AddToHistory`, `ReportInformationToWindow` and `Result1D(…)` are documented as methods of the Application object, whose heading is "Project Object" (`mP/VBA_3D/common_vbaapp/common_vbaappapplication_object.htm`). Code calls them without an object, so a usage scan has to map bare names to that object.
- **Members used in code are not always documented.** About 480 pairs (22%) have no matching documented member. Some are gaps in the heuristic, but some are real. `Units.GetFrequencyUnit` appears in 80 files and is not on the 2024 Units Object page (`mP/VBA_3D/common_vbaunitso/common_vbaunitso_units_object.htm`, which documents `GetUnit` and `GetFrequencyUnitToSI`).
- **Objects held in variables are missed.** `Set o = Result1DComplex("…")` followed by `o.Magnitude` cannot be attributed without type inference, so the counts are lower bounds.
- **Library code depends on undocumented helpers.** It calls 64 distinct `*_LIB` helpers in 95 files, all from include files that are absent (section 5). Examples are `FillResultList_LIB` (20 files), `GetLastResult_LIB` (13) and `GetExportPathMaster_LIB` (13).
- **`FarfieldCalculator`** occurs in 1 file and has no help page.

### 4.2 Python

- Imports from the `cst` family: `cst.interface` 18, `cst.eda.pcb_api` 13, `cst.results` 5, `cst.units` 2, `cst.eda` and `cst.eda.geometry2d` 1 each. There are also private calls (`cst._get_install_bin64`) and an internal module (`cst_dev.data_access.xml`).
- There are only **37 distinct `cst.*` dotted paths**, 18 of them in `objects.inv`. The most used are `cst.eda.pcb_api.PCB` (8 files), `cst.interface.ProjectType` (7), `cst.interface.DesignEnvironment` (6), `cst.results.ProjectFile` (5) and `DesignEnvironment.connect_to_any_or_new` (3). Instance calls such as `prj.model3d.add_to_history` (21) are not attributed by the `ast` scan.
- **Feasibility.**
  - For VBA, scanning code for usage of a given API Entry is feasible. Common objects (`ResultTree`, `Units`, `Solver`, `Mesh`, `Brick`, `Transform`, `Material`) have tens to hundreds of usages, and `FarfieldPlot` has 17 files. Most of the documented members still have no usage at all.
  - For Python, usage examples would be thin. The cases worth showing are VBA sent through `add_to_history` and `execute_vba_code`.

---

## 5. Release coupling and cross-file references

- **Version markers:**
  - The code reads the version at run time through `GetApplicationVersion` (14 files), for example `Mid(GetApplicationVersion, 9, 4)` to build registry keys. No hard-coded release governs behaviour.
  - "2024" appears in 4 VBA files, only in history lines and copyright notices (latest history entry 01-Feb-2024, `Macros/Solver/Sources/Analytical Farfield Source^+MWS.mcr`).
  - Other strings name older versions: "CST STUDIO SUITE version 2011" (`Result Templates/Readme.txt`), "CST Studio Suite 2018".
  - Copyright year ranges end in 2019 to 2024.
  - The Python packages are tied to the release: `cst_results_2024*`, `cst_studio_suite_link-2024.2.1201136.551`.
- **Legacy material:** `Result Templates/0D/` and `1D/` are hidden in the GUI, 130 of 163 templates use the legacy layout, and some names say so (`Macros/Wizard/Legacy 5G PP Wizard^+MWS.mcr`, `Macros/File/Import ADS (Legacy)^-DS.mcs`).
- **`'#include` (260 files) points outside this folder.** There are 25 bare `.lib` names, none present in `.ingestion/2024`: `vba_globals_all.lib` (included 256 times), `vba_globals_3d.lib` (79), `template_conversions.lib` (36), `template_results.lib` (28), `complex.lib` (25), `mws_ports.lib` (17), `vba_globals_ds.lib` (14), `farfield.lib` (7) and others. The other 8 targets are relative paths of the form `..\Result Templates\<folder>\<file>`, which all resolve. They would resolve from a folder that is a sibling of `Result Templates/` under `Library/`, presumably where the `.lib` files live.
- **Install-relative paths:** 109 literals of the form `GetInstallPath + "\Library\…"`.
  - Most point to `Library\Macros` (86) or `Library\Result Templates` (13): bitmaps, `.bas` helpers, `.mcr` and `.py`.
  - Some point to folders **not present in this copy**: `\Library\Misc\templates\` (8, PowerPoint and Word templates) and `\Library\Bio Models\` (2).
  - Others point outside `Library`: `\AMD64\python\python.exe`, `\AMD64\EyeAnalyzer_AMD64.exe`, `pscp` and `plink.exe`.
- **`RunScript`** occurs in 17 call lines. Six have literal targets, for example `Macros/Wizard/Data Import Wizard.mcr` → `Macros/Results/- Import and Export/Import Touchstone File^+MWS+DS.mcr` and the ADS converter chain. The rest run computed paths, such as generated copies of `.bas` helpers or a user-chosen file.
- **`'#Uses`**: 11, all to `.cls` files in the same folder.
- **Python**: descriptors start modules with `-m cstapps.apps.<module>`. Modules import `cstapps._impl.common.connect` and `cstapps._impl.gui_tkinter.tkinter_gui_support`, which exist in neither `lib/` nor the wheel's file list, so they are probably dead imports.

---

## 6. Duplicates, generated, binary and scrambled content

- **Exact duplicates (MD5): 12 groups, 15 redundant copies, 143 KB.**
  - The four `Macros/Converter/ADS Converter {1,2,3,5}.bas` files equal `Macros/File/ADS Converter {1,2,3,5}.bas`, and `Macros/Converter/ADS Converter 4.bas` equals `Macros/File/Import ADS (Legacy)^-DS.mcs`.
  - `Result Templates/1D/rescale1d_template{,^DS}.bas` equals `Result Templates/General 1D/rescale1d_template{,^DS}.bas`.
  - `Macros/Solver/Mesh/Hex Mesh - Prepare Postprocessing Loss from E field^+MWS.mcr` equals the copy in `Macros/Solver/Monitors and Probes/`.
  - `Macros/Construct/Vias/Via Wizard^-DS.mcr` equals `Macros/Wizard/Via Wizard.mcr`.
  - Two pointer templates are identical across folders: `Evaluate Field Statistics.rtp` (in `2D and 3D Field Results` and `MRI Toolbox`), and `- Combine Power Loss^+MWS+DS.rtp` equals `MRI Toolbox/Combine Power Loss and Worst Case SAR^+MWS+DS.rtp`.
  - Five empty `.py` files are identical.
- **Near-duplicates:** 39 pairs with a Jaccard similarity of distinct non-comment lines of at least 0.6. At 0.8 or more, 9 clusters with 21 files. Examples:
  - the three `CST_Microsoft_HPC_Scheduler_{2012,2016,2019}.cls` (0.97);
  - `PowerPoint Slide^+DS` and `^-DS` (0.91);
  - `LF - Export Admittance/Impedance Matrix …^+EMS.rtp` (0.90);
  - `Waveguide T-Splitter` and `(ready for DC)` (0.89);
  - `Set Monitor Sampling A-Solver` and `I-Solver` (0.86);
  - `Macros/Calculate/Calculate Moment of Inertia^+EMS.mcr` and `Result Templates/Statics and Low Frequency/Calculate Moment of Inertia^+EMS.rtp` (0.75).
- **Scrambled macros: 5 `.mcr`, 1.15 MB.** Every line has the form `Scrambled "05<hex>"`, so the source is unreadable:
  - `Macros/Materials/Extract complex permittivity from measured S-Parameters (broadband)^+MWS.mcr` (406 KB);
  - `Macros/Materials/Import Biological Tissue Properties^-DS.mcr`;
  - `Macros/Solver/Set up 2.5D vEIM Simulation^+MWS+DS.mcr`;
  - `Macros/Wizard/5G Post-Processing Wizard^+MWS.mcr`;
  - `Macros/Wizard/Legacy 5G PP Wizard^+MWS.mcr`.

  Scrambling is a property of the file content, not of the extension: the other 206 `.mcr` are plain text, and `.mcs` versus `.mcr` means structure versus control macro.
- **Very large files:**
  - `Result Templates/Time Signals/Eye Diagram Tool^+DS+MWS.rtp` (12,608 lines);
  - `Result Templates/2D and 3D Field Results/0D or 1D Result from 2D Colormap.rtp` (7,191);
  - `ADS Converter 1.bas` (4,308, in two copies);
  - `Farfield Result^+MWS+DS.rtp` (3,974).

  Across all files there are 2,774 procedures: median 35 lines, p90 175, p99 633, maximum 2,186. Files have a median of 3 procedures and at most 124.
- **Binaries:**
  - wheels (199.6 MB, 79% of bytes);
  - BMP (37.4 MB);
  - `.xlsm` with a VBA project, `.exe`, `.cst` projects, OLE2 `.ppt` and `.doc`;
  - PNG and SVG icons in `cstapps`.
- **Generated content:** the package index HTML (`simple503`) and `__git_sha__.py`. No code was found to be machine-generated, apart from the recorded history blocks in `.mcs` files (`'@` markers).

---

## 7. Other things that would break or mislead a naive ingestion

- **Strict UTF-8 decoding fails** on 7 `.mcr` files (cp1252).
- **The extension does not tell what a file is:**
  - `.txt` mixes VBA include bodies, data tables and readme files;
  - one `.ppt` is a PPTX;
  - `.cst` uses a ZIP-like header with altered magic;
  - `.lib` exists both as include files (absent) and as two small local overrides;
  - 5 `.mcr` are scrambled.
- **Pointer templates** have no body of their own. Indexing them as Documents duplicates their target or yields empty Sections.
- **Code that is not self-contained:** 260 files include libraries that are absent, and 95 call `*_LIB` helpers that are defined nowhere in the Knowledge Base.
- **Names are untrustworthy:** stale guard titles, wrong header titles, duplicate `macro.NNN` ids, and help titles abbreviated differently ("Farfield&Antenna", "General").
- **Display names are not unique**, because of application filter variants, the same name in several folders, and macro and template pairs.
- **Locators that replace the extension collide** (11 groups). Names contain `^`, `+`, spaces, parentheses, commas and `=`. One has a space before its extension and one has a double space, so normalising whitespace would break mirroring.
- **Help links** need case-insensitive resolution, and 16 targets are missing. A help page may document an item that no longer exists in the Library.
- **Size skew:** wheels and bitmaps are 94% of the bytes. One template has 12,608 lines.
- **Boilerplate inside code:**
  - long change-history blocks (3,120 lines, about 150 in `Farfield Result^+MWS+DS.rtp` alone);
  - copyright lines;
  - dialog layout code (9,830 lines, 6% of non-comment lines);
  - debug mains (`Main2`, `Main_RTP`).
- **Files that must not be run or served:** `.exe`, `.reg`, `.bat`, `.xlsm`.
- **A legacy layout dominates:** 130 of 163 templates use it, although the help documents the current layout first.

---

## Hazards for ingestion

1. **A new kind of input:** a file tree of code (WinWrap Basic macros and templates, class modules, include bodies, Python) plus presets, data, bitmaps and Office or PDF companions. None of it is HTML, so the existing readers do not apply.
2. **Kind detection by content.** Extension and content disagree for `.txt`, `.ppt`, `.cst` and scrambled `.mcr`. Pointer `.rtp` files contain nothing but an include.
3. **Encoding:** cp1252 in 7 files, CRLF everywhere, tabs in 60% of lines.
4. **Naming:** the display name comes from the file name (stem before `^`) and the folder path. The `^` application filter must be parsed. In-file titles are unreliable, and display names collide (16 variant pairs, 15 multi-folder names).
5. **Locator collisions** if the extension is replaced (11 groups, two of them between code files). Names carry `^`, `+`, spaces, parentheses, commas and `=`, plus one trailing space and one double space.
6. **Missing dependencies:** include libraries (25 `.lib` names, 64 `*_LIB` helpers) and the `Library/Misc` and `Library/Bio Models` folders are not in this copy.
7. **Scrambled code:** 5 macros (1.15 MB) whose content is unreadable by design.
8. **Duplicates:** 15 exact copies, 39 near-duplicate pairs, macro and template twins.
9. **Size:** 200 MB of wheels and 37 MB of BMP. Files up to 12,608 lines and procedures up to 2,186 lines are too large to be one Section each.
10. **Heuristic API attribution:** unqualified Application methods, `With` blocks, string-built history commands (796 `With` blocks in strings) and variable-held objects.
11. **Documentation gaps:** about three quarters of the code has no help page. Library code uses members the 2024 help does not document (`Units.GetFrequencyUnit`, 80 files) and helpers no Document defines.
12. **Stale help:** 21 `common_preloadedmacro` pages match no Library file by title or link, and 16 `StartHelp` targets do not resolve.
13. **Files that must never be executed or served:** `.exe`, `.reg`, `.bat`, `.xlsm` with macros, and wheels with native code.

---

## Design implications

### Forced by the facts

1. **A new Source format.** The Library folder needs its own reader that parses into the Document model of ADR 0007. ADR 0007 already allows readers per source format; this adds one for code.
   - The reader classifies files by content, not by extension alone: scrambled, pointer, include body, data, binary.
   - It decodes cp1252 and normalises CRLF in the rendered view, keeping originals verbatim (ADR 0002).
   - The new block kinds are verbatim code, comment prose, metadata fields, and optionally dialog definitions.
2. **The Library belongs to the `cst-2024` Collection.** It ships with the installation and contains 2024-specific package versions, history up to February 2024, and help links into the 2024 help. ADR 0005 and the Collection definition therefore make it a Source of a Release-bound Collection, rebuilt per Release. It is not release-independent.
3. **The glossary must widen "Document".** It currently reads "one help topic or one PDF". It must cover one code file, and the Document needs a kind: Macro (control or structure), Result Template, Python script or module, and supporting kinds (helper script, class module, include body, preset, app descriptor). The user's three kinds (Macro, Result Template, Python script) are the minimum.
4. **Library Locators cannot simply replace the extension.** That rule collides 11 times, including `Evaluate Field Statistics.rtp` and `.txt` and four `.json`/`.py` pairs.
   - The fix that keeps the Locator rule otherwise unchanged is to append the extension: `…/farfield result^+mws+ds.rtp.md`.
   - Lowercasing is collision-free, and `#` never occurs in names, so the `#anchor` separator stays unambiguous.
   - Names must be mirrored verbatim, including `^`, `+`, spaces, parentheses and the odd whitespace.
5. **Display names must come from the file name and folder path**, with the `^` filter parsed into a separate attribute. Header and guard titles may only serve as extra names. Lookups must be able to return several candidates, because display names collide.
6. **Exact copies are Aliases.** The glossary's definition, another source path under which the same Document was published identically, fits the 12 duplicate groups, for example `Macros/Converter/ADS Converter 1.bas` and `Macros/File/ADS Converter 1.bas`. Pointer templates are not Aliases (their content differs). They need an "includes" relation to their target.
7. **Procedure boundaries are trusted Section boundaries.** Whole-file Sections are unworkable for the largest files (12,608 lines; procedures up to 2,186). `Sub`/`Function`…`End` is syntactic, VBA does not nest procedures, and Python `def`/`class` come from `ast`. This fits the rule "split only at trusted boundaries".
8. **A usage scan must also read string literals.** Otherwise it misses the string-built history commands, which make up about a third of all attributed pairs (712 of 2,153). It must also map unqualified calls to the Application object. Its results are heuristic and must be labelled as such.
9. **Excluded from the Knowledge Base:** wheels (79% of bytes), `.exe`, `.reg`, `.bat`, `.xlsm`, `.cst`. Readers never execute or import anything from the Library. Scrambled macros get metadata only (name, category, filter, "source not readable"), and their content is never descrambled.
10. **Dependencies are recorded on each Document.** Its included libraries and the `*_LIB` helpers it calls are listed, because an agent copying such code gets a macro that does not run unless the include is available.
11. **Help links are resolved at build time.**
    - Code → help: `StartHelp` and `HelpFileName`, case-insensitive, 110 files.
    - Help → code: normalised title match, 68 pages.
    - Both directions are rendered as Locator links. ADR 0003 requires every link to appear in both views.
12. **ADR 0001 applies unchanged.** About 150 files carry Dassault Systèmes copyright notices and 2 carry a third-party notice ("MNW Scan Pte Ltd"). Nothing from the Library is committed, and tests use synthetic fixtures that imitate the structure (guard line, `^` suffix, `Define`/`Evaluate1D`, `'@` blocks).
13. **ADR 0006 applies to dialog bitmaps.** They become Assets of the Documents that load them (63 of 71 are referenced by path), and any text in them stays untranscribed.

### Judgment calls (recommendation first)

1. **Areas.**
   - *Recommended:* three new Areas for `cst-2024`, named `macros`, `result-templates` and `python-apps`. The Library is one document family per subfolder, and users name templates and macros specifically ("build it like the … template").
   - *Alternatives:* a single `library` Area, or folding everything into `examples`. Folding into `examples` would blur that Area, which today means the EXP_* tutorial projects.
   - The application filter (MWS, DS, EMS, PS, MPS) is better a filterable attribute than an Area.
2. **Sections.**
   - *Recommended:* one Section for the file header (title, description comments, module-level declarations, includes) and one Section per procedure. Files under about 150 lines stay whole. The change history becomes a metadata field, or a separate low-weight Section.
   - *Alternative:* a Section per file, plus a Section per procedure only for files over a size threshold.
3. **Rendering.**
   - *Recommended:* a metadata block (display name, menu path, kind, application filter, template type and layout, source path, includes, `*_LIB` helpers used, help page Locator, Alias paths, history date range), then per Section a heading such as `## Function Define` and a fenced block tagged `vb` or `python` with the code verbatim. The output is UTF-8 with LF, and tabs are kept.
   - Anchors derive from procedure names, which are unique per file.
   - `.ffconfig` presets go into a "Presets" Section of the Farfield Result Document.
   - The 5 PDF companions are ingested through the PDF reader and linked to their sibling macro by stem. PPT and DOC files without a PDF are reported as unsupported.
4. **Lookup by display name.**
   - *Recommended:* a name table next to the API Entry table, consulted first as in ADR 0008. It holds names normalised for case, punctuation and leading `- `/`+ `, from:
     - the file stem and the menu path;
     - the help page title and page file name;
     - guard and header titles, at low weight.
   - `cst_help_lookup` accepts a display name or menu path and returns ranked candidates with their filter variants, plus an optional application parameter.
   - "Farfield Postprocessing Template" should yield a short list headed by `Farfield Result`, not a single forced hit.
5. **Usage examples for API Entries.**
   - *Recommended:* a build-time usage index from API Entry to Library Sections. `cst_help_lookup` reports it ("used in N Library Sections", top few by a quality rank: current layout, not legacy, not scrambled, short Section). Each API Entry's Markdown gets a matching list (ADR 0003). This keeps the five planned tools.
   - *Alternative:* a sixth tool, `cst_help_examples`.
   - Undecided: should usages of undocumented members, such as `Units.GetFrequencyUnit`, be offered when the exact API lookup misses? They are valuable, but not authoritative.
6. **Search weighting.**
   - *Recommended:* code Sections in the same FTS5 index with their own field weights: names and menu path high, comment prose and dialog labels medium, referenced identifiers in a separate field, code body low, history lines excluded or lowest.
   - `cst_help_search` gets a kind filter (prose or code).
   - The query benchmark then decides whether code should be excluded from default results.
7. **Python scope.**
   - *Recommended:* index the 5 apps, their descriptors and the modules that carry VBA strings or `cst.*` calls. The rest of the `cstapps` framework (GUI and parsing code) is low-value.
   - Index `lib/`, not the duplicate wheel.
8. **Legacy items** (`0D`/`1D` folders, legacy-layout templates, "(Legacy)" names): index them, flag them, rank them lower.
9. **Bitmaps:** carry them as-is (37 MB), or convert them to PNG at build time. The standard library can do this (`zlib` for PNG; 4-, 8- and 24-bit BMP decoding is simple), which shrinks the Knowledge Base and helps clients that cannot show BMP.
10. **Exact copies:** pick a canonical path for each Alias group, for example the non-legacy folder (`Macros/File/` over `Macros/Converter/`?), or simply the first in sort order.

### Glossary changes to consider

- **Document:** widen it to "one help topic, one PDF, or one code file from the Library".
- **New terms:**
  - **Macro**, a VBA file started from CST's Macros menu: a control macro (`.mcr`) or a structure macro (`.mcs`, recorded into the history list).
  - **Result Template**, a `.rtp` VBA file whose `Define` and `Evaluate…` functions the post-processing framework calls.
  - **Display Name**, the name CST shows for a Macro or Result Template: the file stem before `^`, under its folder path.
  - **Application Filter**, the `^+MWS-DS`-style suffix.
  - **Usage**, a Section that references an API Entry, found by the build's heuristic scan.
  - **Variant**, possibly: Documents with the same Display Name in one folder that differ only by Application Filter.
- **Conflict:** the glossary lists "library" under _Avoid_ for Collection, but CST's own name for this folder and its location setting is "Library" (Global Library Path). One option is to keep "library" out of the domain vocabulary and call the Source "the CST Library folder". Another is to add an explicit note that "Library" names only CST's folder.
- Two ADRs could record these decisions: the Library as a Source with code Documents and Locators that keep the source extension, and the heuristic, build-time usage index.

### Questions only the user can answer

Settled since the first version of this list: the include libraries were found (`Includes/`, section 8), MWS is the preferred application, and heuristic usage links are accepted.

1. **Remaining support folders.** `Library/Misc/templates/` (8 references, PowerPoint and Word templates) and `Library/Bio Models/` (2) are still not in this copy. Are they needed?
2. **Which Library?** Is it the installation's `Library` only, or the user's configured Global Library Path (File > Options > Library Path)? The latter may contain the user's or their company's own macros, under different licensing or confidentiality. The same applies to materials: "Add to Material Library" writes to the configured material library, which may hold the user's own or company materials.
3. **Control Server behaviour.** Does mcp-cst-studio resolve `'#include` against `Library/Includes/` (and `'#Uses`) when it runs code? If not, examples that call Include helpers cannot be reused directly, and the Knowledge Base should show the include closure (section 8.6) prominently or offer the helper code inline.
4. **Scope of Python.** Is the `cstapps` framework in scope, or only scripts that drive CST?
5. **Scrambled macros.** Should they appear at all, with metadata only?
6. **Companion documents.** Are the PPT and DOC files without a PDF counterpart (5 files) worth an Office reader, or can they be skipped?
7. **Unused Includes.** No Library file includes `vba_globals.lib` (obsolete since 2007), `array_wizard.lib`, `machines_functions.lib` or `mafia_globals.lib`. Do the user's own macros include any of them? If not, should they be indexed at all, or only flagged?
8. **Loading a library material from VBA.** Can the user confirm in CST 2024 that "Load from Material Library" records the block described in section 9.4 (`'@ define material: <name>`, `With Material`, `.Reset`, `.Name`, `.Folder ""`, then the file's definition)? If it does, Material Documents can offer that block as a ready-to-send snippet; until then it stays an inference from 9 copies in Library code.
9. **Material aliases.** The files carry no aliases. Should the Synonym Sets include hand-written material aliases (FR4 → FR-4, Teflon → PTFE, Kapton → Polyimide, Al2O3 → Alumina, RT/duroid → RT-duroid), and who curates them?
10. **Material families.** Are all vendor families relevant: 334 Panasonic laminate and prepreg variants (307 of them share their definition with another file) and 60 ECCOSORB absorbers with tables of up to 1,799 rows? Or should some be collapsed or left out?

---

## 8. Includes (`Includes/`)

The method is the same as in sections 1 to 7: standard-library scans run with `python -I`, and nothing was executed. Helper usage and API attribution are heuristic token matches. They skip comments, strings (except where stated), member accesses and locally declared names (`Dim`, `Const`, parameters), and the text says where a count depends on that heuristic. With the two new folders, the Library has 1,536 files.

### 8.1 Inventory, encoding and structure

**30 `.lib` files, 0.96 MB, 25,434 lines, 677 procedures.** All are ASCII with CRLF line endings, with no BOM and no NUL byte. 16,424 lines (65%) contain tabs. The longest line has 381 characters (`farfield_calculator.lib`). The folder has no subfolders.

| File | Lines | Procedures (`_LIB`) | With a comment block | Included by (files) | History | Header |
|---|---:|---:|---:|---:|---|---|
| `vba_globals_all.lib` | 2,299 | 100 (29) | 35 | 256 | 2004–2021 | purpose |
| `vba_globals_3d.lib` | 2,730 | 28 (4) | 17 | 79 | 2007–2023 | purpose |
| `template_conversions.lib` | 1,526 | 27 (10) | 19 | 36 | 2010–2021 | purpose |
| `template_results.lib` | 666 | 5 (5) | 4 | 28 | 2014–2022 | purpose |
| `complex.lib` | 828 | 53 (1) | 9 | 25 | 2005–2019 | purpose |
| `mws_ports.lib` | 135 | 4 | 3 | 17 | 2017 | none |
| `vba_globals_ds.lib` | 222 | 13 | 5 | 14 | 2010–2021 | history only |
| `infix_postfix.lib` | 3,651 | 119 (2) | 87 | 12 | 2010–2023 | purpose |
| `exports.lib` | 281 | 9 (7) | 9 | 10 | 2015–2021 | purpose |
| `video_creation.lib` | 818 | 18 | 10 | 8 | 2020–2021 | purpose |
| `coordinate_systems.lib` | 624 | 18 | 12 | 7 | 2003–2023 | purpose |
| `farfield.lib` | 2,558 | 32 (24) | 25 | 7 | 2010–2023 | purpose |
| `OptenniLibrary.lib` | 132 | 6 | 1 | 5 | 2021–2023 | history only |
| `OptenniLibrary_MWS.lib` | 269 | 6 | 0 | 4 | 2022–2023 | purpose |
| `particles.lib` | 25 | 1 | 0 | 3 | none | none |
| `signal_processing.lib` | 99 | 2 | 1 | 3 | none | none |
| `mws_evaluate-results.lib` | 125 | 3 | 0 | 2 | none | none |
| `biofreq.lib` | 108 | 4 | 1 | 1 | none | purpose |
| `farfield_calculator.lib` | 584 | 16 | 2 | 1 | 2021 | purpose |
| `lin_systems.lib` | 321 | 11 | 6 | 1 | 2013–2016 | purpose |
| six `Eye_*_FUNCTIONS.lib` (DEBUG, DigSequence, Encoding, Equalization, Histogram, MatrixVector) | 3,638 | 80 | 36 | 1 each | 2016–2018 | history only (MatrixVector: none) |
| `machines_functions.lib` | 768 | 23 (21) | 4 | **0** | 2021–2023 | purpose |
| `mafia_globals.lib` | 420 | 8 | 1 | **0** | 2003–2009 | purpose |
| `array_wizard.lib` | 19 | 1 | 0 | **0** | 2012 | purpose |
| `vba_globals.lib` | 2,588 | 90 (1) | 19 | **0** | 2003–2009 | obsolescence notice |

`lin_systems.lib` and the six `Eye_*` files are included only by `Result Templates/Time Signals/Eye Diagram Tool^+DS+MWS.rtp`.

**Header comments follow no template.**

- 18 files open with a purpose statement, such as "This library provides functions for exporting results". 7 open with a change history only, and 5 with neither: `Eye_MatrixVector_FUNCTIONS.lib`, `mws_evaluate-results.lib`, `mws_ports.lib`, `particles.lib` and `signal_processing.lib`.
- 25 files hold 456 dated history lines (`DD-Mon-YYYY initials: text`), from 2003 to November 2023. 7 files carry a copyright line.
- `'#Language "WWB-COM"` appears in 2 files (`infix_postfix.lib`, `lin_systems.lib`). `Option Explicit` is active in only 1 (`OptenniLibrary.lib`), and `template_results.lib` says it must stay disabled for standalone DS.
- At module level there are 146 names (variables, constants, `Type` and `Enum` definitions), 122 of them public, such as `lib_rundef` and the `Complex` type. There are no `Declare` statements, so no Include calls a DLL directly.

**Procedures.**

- 506 are `Function` and 171 `Sub`. 655 have no scope keyword and are public by default; 14 say `Public` and 8 say `Private`.
- Lines per procedure: median 19, p90 73, max 422. 18 procedures and 23 files exceed 150 lines.
- 44 signatures continue over several lines with ` _`.
- Procedure names are unique within each file.

**Doc comments are informal.**

- 29 procedures have a comment block directly above the signature, and 282 have one at the top of the body (after optional blank lines). Together that is 306 of 677 (45%), and 128 of them have at least two lines.
- Of the 104 `_LIB` procedures, 65 have a block and 39 have two or more lines. `GetExportPathMaster_LIB` (13 calling files) has none.
- There is no structured convention. `Input:`, `Output:`, `Usage:` and `Example:` lines occur 7 times, in 3 files. Some top-of-body comments are implementation notes rather than descriptions.

**Duplicated and colliding names.**

- **`vba_globals.lib` is obsolete.** Its header says so (July 2007), 28 Library files record that they replaced it (mostly in 2011), and no file includes it.
- 79 procedure names and 11 module-level names are defined both in `vba_globals.lib` and in `vba_globals_all.lib` or `vba_globals_3d.lib`. The only `_LIB` name among them is `GetSimulationProjectByName_LIB`.
- Three Include procedures carry Result Template entry-point names: `Evaluate0D` and `Evaluate1D` in `mws_evaluate-results.lib`, and a test `Sub Main2` in `lin_systems.lib`. 70, 67 and 79 Library files define these names themselves.
- No Include procedure shares its name with a documented Application method or VBA object.

### 8.2 `_LIB` helpers, and helpers without the suffix

- **No helper is missing.** In this scan, the earlier "64 helpers in 95 files" are 63 identifiers in 95 files once case is folded. VBA is case-insensitive, and `Start_LIB`/`start_lib` and two spellings of `RestoreAndReEnableFarfieldPlot_LIB` both occur. The 63 split into:
  - 53 Include procedures, called from 89 files;
  - 8 public Include variables with the suffix, for example `DSResultFolder_LIB` (15 files), `MWSResultFolder_LIB` (6), `PlotMode_LIB` and `folderContents_LIB`;
  - 2 local variables in Library code, `bFound_lib` (6 files) and `sLine_lib` (1), which are not helpers.
- Every file that calls an Include helper includes the defining Include directly: 186 file-helper pairs, without exception.
- `Includes/` defines 103 distinct `_LIB` procedures. 53 are called from Library code, 47 only from other Includes, and 3 from nowhere.
- **The suffix is a convention, not a boundary.** `template_results.lib` asks that newly added functions end in `_LIB`, but only 103 of 591 public procedure names do. Of the other 488, 205 are used by Library code in 204 files (token match). The most used:

  | Helper | Files | Defined in |
  |---|---:|---|
  | `NoForbiddenFilenameCharacters` | 117 | `vba_globals_all.lib` |
  | `FindListIndex` | 95 | `vba_globals_all.lib` |
  | `FillArray` | 41 | `vba_globals_all.lib` |
  | `ShortName` | 28 | `vba_globals_all.lib` |
  | `CST_MkDir`, `DirName` | 22 each | `vba_globals_all.lib` |
  | `PushBrowse2D3DResults` | 14 | `vba_globals_3d.lib` |
  | `FillModeNumberArray` | 13 | `mws_ports.lib` |
  | `GetTaskScriptSetting`, `StoreTaskScriptSetting` | 9 each | `vba_globals_ds.lib` |

  The `vba_globals_all.lib` names above are also defined in the obsolete `vba_globals.lib`.
- Library code also uses 49 public module-level names, such as `lib_rundef` (27 files), `TaskNameArray` (13) and the `Complex` type (12).
- 41 Include procedures are used nowhere, 7 of them in `vba_globals_all.lib`.
- **Library code redefines Include names.** 284 procedure definitions in 161 Library files share a name with an Include procedure.
  - Most are the entry points above (`Main2`, `Evaluate0D`, `Evaluate1D`).
  - The rest are copied utilities (`ShortName` in 15 files, `Quote` in 6).
  - `Macros/Results/EMC/Determine Plot Peaks^+MWS+DS.mcr` defines 16 procedures that it also pulls in through `vba_globals_all.lib`.
- No file references the two `.lib` files in `Macros/` (`CST_Compatibilty_Settings_{DS,MWS}.lib`, section 2.5).

### 8.3 How Includes depend on each other

- **No Include includes another.** No `.lib` has an active `'#include`. There are two disabled ones: `'a'#include "complex.lib"` in `lin_systems.lib` and `''include "complex.lib"` in `infix_postfix.lib`.
- **Stated dependencies exist only in comments.**
  - `template_results.lib` says it requires `template_conversions.lib`.
  - `farfield.lib` requires the host macro to declare a global `sFullCompString`, and all 7 includers do.
  - `farfield.lib` also duplicates buffered-file code to avoid "dependency problems" with `exports.lib`.
- **Implicit dependencies**, found by resolving the names each Include uses against the names the others define:

  | Include | Needs | Names used |
  |---|---|---:|
  | `vba_globals_3d.lib` | `vba_globals_all.lib` | 17 |
  | `video_creation.lib` | `vba_globals_all.lib` | 14 |
  | `farfield.lib` | `vba_globals_all.lib` | 8 |
  | `mafia_globals.lib` | `vba_globals_all.lib` | 8 |
  | `template_conversions.lib` | `vba_globals_all.lib` | 3 |
  | `template_results.lib` | `template_conversions.lib` | 3 |
  | `farfield_calculator.lib` | `farfield.lib` (`Integrate2D_LIB`); `vba_globals_all.lib` | 1; 3 |
  | `infix_postfix.lib` | `complex.lib`; `vba_globals_all.lib` | 20; 1 |
  | `biofreq.lib` | `complex.lib` | 7 |
  | `lin_systems.lib` | `complex.lib` | 5 |
  | `Eye_Equalization_FUNCTIONS.lib` | `lin_systems.lib`; `vba_globals_all.lib` | 5; 1 |
  | `coordinate_systems.lib`, `mws_evaluate-results.lib` | `vba_globals_all.lib` | 2 each |
  | `Eye_Histogram_FUNCTIONS.lib` | `vba_globals_all.lib` | 1 |

  Every `vba_globals_all.lib` edge could also be satisfied by the obsolete `vba_globals.lib`, which defines the same names.
- **The graph has no cycles.** The longest chains have three levels:
  - `Eye_Equalization_FUNCTIONS.lib` → `lin_systems.lib` → `complex.lib`;
  - `farfield_calculator.lib` → `farfield.lib` → `vba_globals_all.lib`;
  - `template_results.lib` → `template_conversions.lib` → `vba_globals_all.lib`.

  16 Includes depend on no other.
- **Library code satisfies every edge.** Each file that includes an Include also includes what that Include needs, listing the whole closure flat.
  - 79 of the 79 files that include `vba_globals_3d.lib` also include `vba_globals_all.lib`.
  - 28 of the 28 that include `template_results.lib` also include `template_conversions.lib`.
  - The commonest include sets are `vba_globals_all.lib` alone (103 files) and `vba_globals_3d.lib` with `vba_globals_all.lib` (59).

### 8.4 API members used by the Includes (heuristic)

- **Mostly documented.** The Includes use 93 distinct `Object.Member` pairs on 22 objects (`ResultTree` 15, `WCS` 10, `Pick` 9, …), and 84 of them are documented.
  - 51 documented Application methods are called unqualified, most often `GetProjectPath` and `ReportError` (11 Includes each).
  - The `DS.` calls (`GetActivePostprocessingTask`, `GetTreeNameScriptSetting`, …) are documented on `mP/VBA_DES/special_vbacommands/projectobject.htm`.
- **9 member pairs are undocumented:**

  | Member | Used in | Help |
  |---|---|---|
  | `Units.GetFrequencyUnit` | `Eye_Equalization_FUNCTIONS.lib`, `OptenniLibrary_MWS.lib` | No heading. A stale VBA_DES index entry points to `special_vbacommands/unitsobject.htm`, which does not document it. |
  | `Units.GetTimeUnit`, `Units.GetGeometryUnit` | `Eye_DEBUG_FUNCTIONS.lib`, `particles.lib` | no heading |
  | `Mesh.GetNx`, `GetNy`, `GetNz` | `mafia_globals.lib` | named in prose on the Mesh Object page (`mP/VBA_3D/special_vbamesh/special_vbamesho.htm`) |
  | `ResultTree` `.File2` and `.ReferenceImpedance`, inside `With Resulttree` | `vba_globals.lib`, `vba_globals_3d.lib` | none |
  | `WCS.AlignWCSWithGlobalCoordinates` | `machines_functions.lib` | only as an option name (`Tip-Note-Heading`) on the WCS Object page |

- **Some unqualified functions appear in neither the VBA reference nor the WinWrap reference.**
  - `CallByName` is used in 5 Includes, and `SetLocale` and `IsLinux` in 2 each.
  - Used once each: `IsWindows`, `GetPathSeparator`, `MakeNativePath`, `MakeWindowsPath`, `RunCommand`, `RunExecutable`, `ModuleLoadThis` and `StartHelp`.
  - `GetGlobalNameFromTreeName` (`machines_functions.lib`) is named only in prose on `mP/VBA_3D/common_vbageneral/common_general_global_names.htm`.
  - Some of these may be WinWrap built-ins that its 315-page reference omits; the scan cannot tell.
  - `StartHelp` is also the call behind the 126 help links of section 2.8, and no help page documents it.
- **`CallByName` hides API calls.** `template_conversions.lib` makes 7 such calls, passing the names of tree and result methods such as `GetResultFromTreeItem` as strings, which a scan of code tokens does not see.

### 8.5 The bare `.lib` names

- This scan counts **26 distinct bare names** (the earlier count was 25), in 525 include lines in 260 files. **All 26 resolve** to a file in `Includes/` when compared case-insensitively.
- Resolution must ignore case in two places: the directive is spelled `'#Include` 9 times, and one target is spelled `vba_globals_3D.lib`.
- The 7 relative targets (`..\Result Templates\<folder>\<file>`, 11 include lines) also resolve from `Includes/`, so `Includes/` is the base folder for `'#include`.
- 4 Includes are included by no Library file: `array_wizard.lib`, `machines_functions.lib`, `mafia_globals.lib` and `vba_globals.lib`.

### 8.6 Design implications

**Forced by the facts**

1. **Includes are code Documents of kind Include, in the `macros` Area, read by the Library reader.**
   - They get the Macro layout: a header Section (purpose comments, history, module-level declarations) and one Section per procedure. 7 of the 30 files are under 150 lines and stay whole.
   - Anchors come from procedure names, which are unique within each file.
   - The Locator rule applies unchanged (`…/includes/template_conversions.lib.md`). These names contain only letters, digits, `_` and `-`, and lowercasing collides nothing.
2. **`'#include` resolution ignores case and looks in `Includes/`.** Both the directive and the target need case folding. Each Macro and Result Template lists its includes as Locator links (ADR 0003), and all 260 including files resolve.
3. **Dependencies must be computed, because they are not declared.**
   - The build resolves the names each Include uses, and records a "requires" list on every Include Document and a "required by" list on each provider.
   - The resolver prefers a provider that some file actually includes. So for the 79 duplicated names, `vba_globals_all.lib` wins over the obsolete `vba_globals.lib`.
   - One check follows: every including file lists the closure of what it includes. It holds for the whole Library today, which makes it a good regression test for the resolver.
4. **The earlier dependency hazard narrows.** "Code that is not self-contained" (section 7) and "missing dependencies" (hazard 6) now concern only `Library/Misc/templates/` and `Library/Bio Models/`. Forced implication 10 (dependencies on each Document) can now link each called helper to its Section.
5. **The usage index covers the Includes.**
   - Include Sections count as Library Sections.
   - Their 9 undocumented member pairs and the unqualified functions above are reported as "undocumented, used in N files", like any other code.
   - A method name passed to `CallByName` as a string counts as a usage of that member.
6. **The help never documents the Includes.** Their Documents must say so ("Library helper, not part of the documented CST API"), so that agents do not mistake a helper for an API Entry.

**Judgment calls (recommendation first)**

1. **Name-table entries for Include procedures.**
   - *Recommended: add them.* Without them, `cst_help_lookup` cannot resolve the 53 `_LIB` helpers and 205 unsuffixed helpers that Library code calls.
   - Index every public procedure, and the public module-level names at lower weight. Leave out the 8 `Private` procedures.
   - Index the names that collide with Library-local entry points (`Evaluate0D`, `Evaluate1D`, `Main2`) only in qualified form, such as `mws_evaluate-results.lib/Evaluate0D`.
   - Rank the obsolete `vba_globals.lib` duplicates below their current twins, or show them only as "also defined in".
   - The exact API Entry table stays first (ADR 0008). A helper is returned when no API Entry matches. It is labelled as a helper and never merged with an API Entry.
   - *Alternative:* `_LIB` procedures only (103). That misses `NoForbiddenFilenameCharacters` (117 files) and `FindListIndex` (95).
2. **What an entry shows.** Every line comes straight from the source, without rewriting:

   ```text
   GetLastResult_LIB                     Library helper (Include), not a CST API Entry
   Function GetLastResult_LIB(ByVal sResultName As String, ByVal sResultType As String, Optional ByVal sToType As String) As Variant
   <comment block from the top of the body, verbatim: here 3 lines on the parameters and the return type>
   Defined in   …/includes/template_conversions.lib.md#getlastresult_lib
   Include      '#include "vba_globals_all.lib"
                '#include "template_conversions.lib"
   Used in      13 Library files (top 3 by the usage-index rank)
   ```

   - The signature is joined across ` _` continuations, which 44 procedures need.
   - The comment block is the one directly above the signature, otherwise the one at the top of the body. 371 of 677 procedures have neither, and their entry says "no description in source".
   - The include lines are the dependency closure in dependency order, providers first, ready to paste.
3. **Obsolete and unused Includes.** Index them and rank them lowest. Flag `vba_globals.lib` as "obsolete" and the other 3 as "included by no Library file". User question 7 asks whether to skip them instead.
4. **Glossary.** The name-table entry needs a term distinct from API Entry. A candidate is **Helper**: a public procedure or variable defined in an Include, addressable by name, and not part of the documented API.

---

## 9. Materials (`Materials/`)

The method is the same as in section 8. The mapping to the Material Object page uses the API Entry extraction of section 4, with the corrections described in 9.2.

### 9.1 Inventory and format

**779 `.mtd` files, 12.5 MB, 215,086 lines**, all in one flat folder.

- All files are ASCII with CRLF line endings, with no BOM and no NUL byte. All file names are ASCII too.
- The median file has 2.6 KB and 83 lines. The largest is `ECCOSORB Coolzorb-600.mtd` (286 KB), and the longest is `ECCOSORB QZorb-2388.mtd` (3,672 lines).
- 95 files exceed 150 lines: 60 ECCOSORB, 30 Preperm, 2 STACEM, `Iron`, `ST37` and `Steel-1010`.
- **76% of all lines are data rows** (164,506 `Add…Value` lines).

**Five kinds of section.** No file has text before its first section.

| Section sequence | Files |
|---|---:|
| `[Definition]` `[Type]` `[Attributes]` `[Description]` | 747 |
| the same, with `[Type]` and `[Attributes]` twice | 20 |
| the first sequence plus a final `[Folder]` | 11 |
| the same, with `[Type]` and `[Attributes]` three times | 1 (`Iron.mtd`) |

The structure, with placeholders:

```text
[Definition]
     .FrqType "<material set: all | static | hf>"
     .Type "<Normal | Lossy metal | PEC>"
     .MaterialUnit "Frequency", "<unit>"        (newer files; older ones use .SetMaterialUnit "<f unit>", "<l unit>")
     .Epsilon "<value>"
     .<Member> "<value>"[, "<value>" …]
     .AddDispersionFittingValueEps "<f>", "<value>", "<value>", "<weight>"   (0 to 1,799 rows)
     .FrqType "<next material set>"             (metals repeat the block)
     …
     .Colour "<r>", "<g>", "<b>"
     .Create

[Type]                 one per material set
FrqType: <set>
<type>

[Attributes]           one per material set, aligned "Key = value [unit]" lines
FrqType: <set>
<Key>  = <value> [<unit>]

[Description]          0 to 4 lines of free text
[Folder]               CHT fluids only
```

- **`[Definition]` is the body of a VBA `With Material` block**: the lines that follow `.Reset`, `.Name` and `.Folder`, up to `.Create`. Every non-blank line is a `.Member args` line, and every file has exactly one `.Create`. **The material name is not in the file.** It exists only as the file stem.
- **Material sets.** A material holds one block of properties per problem type, each opened by `.FrqType`. The Load from Material Library dialog calls these "material sets" and lists the "problem types of all available material sets" (`mP/3D/common_general/common_general_load_from_material_library.htm`).
  - 758 files have one set and 21 have more.
  - 20 metals add a `static` set (type Normal) to their `all` set (type Lossy metal).
  - `Iron.mtd` has `static`, `all` and `hf` sets, and `ST37.mtd` has `hf` and `all`.
  - In 427 files, thermal and mechanical members (`.Rho`, `.ThermalType`, `.SpecificHeat`, `.MechanicsType`, …) come before the first `.FrqType`.
- **`[Type]` and `[Attributes]` restate the definition in readable form, once per set.** The same dialog page says the attributes are "generated automatically". They use 17 keys, with units in brackets:

  | Key | Lines | Key | Lines |
  |---|---:|---|---:|
  | Type | 801 | Rho | 80 |
  | Mu | 775 | Specific heat | 72 |
  | Dispersive eps | 454 | Diffusivity | 71 |
  | Epsilon | 324 | Electric cond. | 54 |
  | Thermal cond. | 307 | Young's modulus, Poisson's ratio, Thermal expan. | 44, 44, 43 |
  | Electric tand | 137 | Dispersive mu, Dyn. viscosity, Nonlin. mu type, Curve type | 25, 11, 5, 5 |

- **There are two file generations:**

  | Generation | Files | Units | Electric conductivity | Families |
  |---|---:|---|---|---|
  | older | 313 | `.SetMaterialUnit` with `"GHz", "mm"` (293), `"MHz", …` (20) or `"Hz", …` (13) | `.Kappa`, `.KappaM` | Rogers, Taconic, 71 generic |
  | newer | 470 | four `.MaterialUnit` lines (Frequency, Geometry, Time, Temperature) | `.Sigma`, `.SigmaM` | Panasonic, ECCOSORB, Preperm, Schott, CHT fluids, 11 generic |

  - The two rows overlap by 4 files: `Aluminum`, `Copper (pure)`, `Gold` and `Silver` carry both styles, and `Copper (pure)` sets `Sigma` and `Kappa` to the same value.
  - Frequencies such as `.TanDFreq "10.0"` are in the file's frequency unit.

### 9.2 Members and the documented Material object

- **88 distinct members, 202,983 occurrences.** 127,593 of the occurrences are `AddDispersionFittingValueEps` and 36,739 are `AddDispersionFittingValueMu`.
- The Material Object page is `mP/VBA_3D/special_vbalayer/special_vbalayerolayer_object.htm`.
- **Extracting its members needed two corrections:**
  - 66 method headings in 16 VBA_3D pages use the class `vba-heading-method` in lower case, 34 of them on the Material page.
  - 116 headings in 21 pages list several members, as in `ThermalConductivity / ThermalConductivityX / …`. 28 of them are on the Material page.

  Case-sensitive matching that takes only the first name finds 206 Material members. Case folding and splitting find 322. Across VBA_3D and VBA_DES, the object and member pairs grow from 5,491 to 5,712.
- **70 of the 88 members are documented; 18 are not:**

  | Undocumented member | Files | Mentioned in the help? |
  |---|---:|---|
  | `FrqType` | 779 | only inside an example on the Solid Object page (`mP/VBA_3D/common_vbasolido/common_vbasolido_solid_object.htm`) |
  | `ErrorLimitNthModelFitEps`, `…Mu` | 465, 464 | no |
  | `SetConstTanDStrategyEps`, `…Mu` | 368 | in prose on the Material page |
  | `IntrinsicCarrierDensity` | 334 | in prose on the Material page |
  | `SetMaterialUnit` | 313 | no (the documented member is `MaterialUnit`) |
  | `Kappa`, `KappaM` | 312 | not on the Material page (the documented names are `Sigma`, `SigmaM`) |
  | `SetActiveMaterial` | 265 | no |
  | `EnableUserConstTanDModelOrderEps`, `…Mu` | 97 | no |
  | `NonlinearMeasurementError` | 16 | no |
  | `ThermalExpansionRateVolume` | 5 | no |
  | `AddNonlinearCurveValue`, `GenerateNonlinearCurve`, `SetNonlinearCurveType` | 4 | no |
  | `AddGeneralDispersionValueEps` | 3 | in prose on the Material page |

- **Most documented members are set in nearly every file.**
  - `Colour`, `Create`, `Mu`, `Rho`, `Transparency`, `Type` and `Wireframe` appear in all 779 files.
  - `Epsilon`, the `TanD…` members, `DispModelEps`, `DispModelMu` and `DispersiveFittingScheme…` appear in 777 or 778.
  - `ThermalConductivity` appears in 761.

### 9.3 Metadata per material

| Property | Where | Values |
|---|---|---|
| Material set (frequency type) | `.FrqType` | `all` 779 sets, `static` 20, `hf` 2 |
| Type | `.Type`, `[Type]` | Normal 778 sets, Lossy metal 22 (21 `all`, 1 `hf`), PEC 1 (`PEC.mtd`) |
| Permittivity | `.Epsilon` | 85 distinct values. **487 files say `1`, and 450 of these define ε through a fitting table instead** |
| Permeability | `.Mu` | 1 almost everywhere; 1000 in 5 sets, 600 in 2, just below 1 in 5 |
| Electric conductivity | `.Kappa` (older) or `.Sigma` (newer) | nonzero in 54 sets, mostly the 22 lossy metals |
| Loss tangent | `.TanD`, `.TanDFreq`, `.TanDGiven`, `.TanDModel` | `TanDGiven "True"` in 137 files, at `TanDFreq` 10 (129) or 1 (8) in the file's unit. Models: ConstTanD 771, ConstSigma 6, ConstKappa 2 |
| Magnetic loss | `.TanDM`, `.KappaM`/`.SigmaM` | zero in all 779 files; magnetic dispersion exists only as μ tables in 25 files |
| Dispersion models | `.DispModelEps`, `.DispModelMu` | `None` everywhere except `Debye1st` in `Water (Debye Model).mtd` |
| Fitted dispersion | `.UseGeneralDispersionEps "True"` with `AddDispersionFittingValueEps` rows (format `Real_Tand` 388, `Real_Imag` 62) | 450 files. Rows per table: 6 (329 Panasonic files), 12 (18 Schott), 201 (2 STACEM), 791 (30 Preperm), 1,799 (56 ECCOSORB), and a few others |
| Nonlinear B-H curve | `ResetHBList`, `AddNonlinearCurveValue` | `Iron`, `ST37`, `Steel-1008`, `Steel-1010` |
| Thermal | `.ThermalType`, `.ThermalConductivity`, `.SpecificHeat`, `.Rho` | types Normal 767, Anisotropic 1 (`FR-4 (lossy - thermal anisotropic)`), PTC 1; conductivity in 761 files; nonzero specific heat in 72, nonzero density in 80 |
| Mechanics | `.MechanicsType`, `.YoungsModulus`, `.PoissonsRatio`, `.ThermalExpansionRate` | Isotropic 44, Unused 466 |
| Display | `.Colour`, `.Transparency`, `.Wireframe`, … | every file |

**Descriptions carry no provenance.**

- 687 files have a non-empty `[Description]` and 92 an empty one. 601 descriptions are one line long, 85 two lines and 1 four lines.
- The commonest lines are:
  - "EM(HF) properties measured @ 10GHz" (253 files) and its 1 MHz variant (21);
  - Panasonic's "Thickness: …, Cloth style: …, Ply: …, Resin Content: …" (334);
  - an interpolation note in 19 Schott files;
  - "Multilayer material with N layers" (20 ECCOSORB files);
  - "Chemical symbol: …" (13);
  - the two-line CHT note (11).
- No description contains a URL, a datasheet or other source reference, a date or a copyright notice. The vendor appears only in the file name.

**Categories.** The folder is flat, and no field names a category.

- `[Folder]` appears only in the 11 CHT fluids, always with the value `Fluid`.
- Families can be read from the first word of the name: Panasonic 334, Rogers 156, Taconic 86, ECCOSORB 60 (absorbers), Preperm 30 and Schott 24 (glass). That makes 690 vendor-named materials.
- The other 89 are the 11 CHT fluids and 78 generic materials: metals, ceramics, soils, `FR-4`, `PTFE`, `Polyimide` and similar.

### 9.4 Names, and how code refers to materials

**The file stem is the material name**, in the form `<base>[ (<qualifier>)]…`.

- 457 names have no parenthesised suffix, 288 have one and 34 have two.
- The last qualifier is `loss free` 137 times, `lossy` 133 times and `CHT` 11 times. The other qualifiers are physical variants, such as `back`/`front`/`middle` (ECCOSORB layers), `dry`/`wet`, `96%`/`99.5%`, `20C 1atm` and `Dk=2.17`. There are 38 distinct qualifiers in all.
- The 334 Panasonic names embed parentheses without a space: `Panasonic <series> <Laminate|Prepreg> <code>(<resin>) Thickness(<n>um) Cloth style(<n>)`.
- **Spelling is not uniform.** CuClad 217 uses `(Dk=2.20)`, but DiClad 880, IsoClad 217 and IsoClad 917 use `(Dk=2.2)`.
- Apart from letters, digits, space, `-` and `.`, names use only `(` and `)` (1,226 each), `=` (16) and `%` (8). The longest name has 83 characters.
- Lowercasing collides nothing, and neither reading of the Locator rule produces a collision: each character replaced by `-`, or each run collapsed to one `-`. The two readings give different Locators for 652 files, for example `air--cht-.mtd.md` and `air-cht-.mtd.md`, so the rule must say which one applies.

**No code loads library files.**

- No Library macro, template, Include or Python module references `.mtd`, the `Materials` folder or a load method.
- None of the 322 documented Material members loads from the library, and `.mtd` appears nowhere in the help.
- The Material Library exists only as GUI dialogs: Load from Material Library, Add to Material Library, and Update Properties from Material Library (`mP/3D/common_general/common_general_*_material_library.htm`).

**Code uses the stem verbatim.**

- `.Material "<name>"` occurs 161 times with 28 distinct values: 113 times in code and 48 in strings built for `AddToHistory`.
- 112 occurrences name a library stem exactly: `PEC` (73, in 36 files), `Vacuum` (23, in 14 files), `Copper (annealed)` (11, in 5 files) and `ST37` (5, in 5 files).
- No `With Material` block defines `PEC`, and only one defines `Vacuum`, so macros rely on both being present without loading them.
- The other values are project-local names (`substrate`, `Ferrite`, …) or names built at run time. One local name, `silicon`, differs only in case from the base of `Silicon (lossy)`.
- The name in code equals the file stem exactly, with its spaces, parentheses and case, and without the extension.

**Library materials reach projects as copied history blocks.**

- Library code has 89 `With Material` blocks: 49 in code and 40 built as strings. 74 of them create a material, and 65 of those are project-specific.
- 9 carry a library stem: `ST37` 5 times, `Aluminum` twice, and `Copper (annealed)` and `Vacuum` once each. Their shape is:

  ```vb
  '@ define material: <name>
  With Material
       .Reset
       .Name "<file stem>"
       .Folder ""
       <the [Definition] lines>
  End With
  ```

- Only the 2 `Aluminum` copies, in the two `Heat Sink with Thermal Source` macros, equal the current file.
- The other 7 have drifted. For example, the `Copper (annealed)` copy in `Macros/Construct/Demo Examples/JS - Resistive Spot Welding - Loss Density^+EMS.mcs` matches all 44 definition lines except the two `DispersiveFittingScheme…` values.
- That "Load from Material Library" records exactly this block is an inference (user question 8).

**The help rarely names library materials.**

- 17 stems occur verbatim in help text, and almost all are one-word names: `PEC` (204 pages), `Vacuum` (33), `Air` (19), `Iron` (11), …
- Qualified names hardly ever occur: `Copper (annealed)` on 3 pages and `FR-4 (lossy)` on 1 (`Python/source/cst.eda.html`). The base name `FR-4` occurs on 9 pages.

### 9.5 Duplicates and variants

- **Exact duplicates: 74 byte-identical pairs (148 files), each with two different names.**
  - 59 pairs are Panasonic resin variants of the same thickness and cloth style: `(G)`/`(K)` and `(GN)`/`(N)`.
  - 10 pairs are Taconic siblings: `TLT-n` and `TLX-n`, `TLP-5` and `TLY-5`, `TSM-DS3` and `TSM-DS3b`.
  - 2 pairs are ECCOSORB: `BSR-2` and `MFS-117`, `LS-26` and `QR-13AF`.
  - 3 pairs cross vendors: `Rogers RO3003 (loss free)` and `Taconic NF-30 (loss free)`, and `Rogers RT-duroid 5870` and `Taconic TLY-3` in both loss variants.
- **Same definition, different description: 83 groups (307 files)**, ignoring colour and other display members.
  - 67 groups (275 files) are Panasonic thickness and cloth-style variants that differ only in their `[Description]` line.
  - The other 16 groups are the exact pairs above, plus `Rogers IsoClad 217 (Dk=2.2) (loss free)` and `Rogers IsoClad 233 (loss free)`. These two differ only in colour, and both have ε 2.2.
- **`(lossy)` and `(loss free)`: 133 pairs**, plus 4 Panasonic CEM-3 pairs of a bare name and a `(loss free)` name.
  - In 130 pairs, the definitions differ in exactly `TanD`, `TanDFreq`, `TanDGiven` and `Colour`. Of the other 3, one differs only in the three `TanD…` members, one also in `Epsilon`, and one in `Kappa` and `TanD` (`Silicon`).
  - `(loss free)` sets `TanD` to 0. `(lossy)` adds a constant loss tangent at the measurement frequency (`TanDGiven "True"` in 132 of 133).
  - The description is identical within every pair.
  - In the CEM-3 pairs only the fitting-table rows differ: the bare name has the tan δ column, and the `(loss free)` name has zeros.
- **`(CHT)`: 11 fluids**, such as `Air (CHT)`, `Water liquid (20C) (CHT)` and several gases. Their description says they were created for CHT and that their EM properties need checking before EM use.
  - They carry `[Folder]` `Fluid` and use the newer format.
  - Only `Air` has a non-CHT twin (`Air.mtd`, older format). The two differ in 38 members, so the qualifier marks a separate material, not a loss model.
- **The other qualifiers are physical variants**: purity (`96%`, `99.5%`), state (`dry`/`wet`, `20C 1atm`), absorber layer (`front`/`middle`/`back`) and grade (`Dk=2.17`, `Dk=2.2`).

### 9.6 Design implications

**Forced by the facts**

1. **The Library reader needs a parser for the `.mtd` format.**
   - It reads sections by their `[Name]` lines and splits `[Definition]` into material sets at each `.FrqType`.
   - It parses `.Member "arg", …` lines with VBA's `""` escapes, and keeps the file verbatim (ADR 0002).
   - It pairs `[Type]` and `[Attributes]` with the sets in order.
2. **A Material Document's name is the file stem, verbatim.** The stem is the only place the name exists, and code uses it exactly (`.Material "Copper (annealed)"`). The title, the name-table key and any rendered `.Name` line must keep its case, spaces, parentheses, `%` and `=`.
3. **ε must not be read from `.Epsilon` alone.** In 450 files it is `1`, and the real permittivity is in the fitting table. For these files the metadata summarises the table: the frequency range with its unit, the ε′ range, and the tan δ (or ε″) range, all computed from the rows without interpretation.
4. **Units come from the file.** `SetMaterialUnit` (older files) or `MaterialUnit "Frequency"` (newer files) gives the unit of `TanDFreq` and of the table frequencies. `Kappa` and `Sigma` both hold electric conductivity. `Kappa` is undocumented in 2024, so the rendered metadata names the documented `Sigma` next to it.
5. **`[Attributes]` is CST's own summary, with units.** It is rendered verbatim per material set, and is the most readable source for the materials with constant properties.
6. **API Entry extraction must fold case in CSS classes and split `A / B / C` headings.** Otherwise 116 documented Material members look undocumented. Other objects are affected too (66 lowercase headings on 16 pages, 116 multi-name headings on 21 pages), which changes the undocumented-member counts of section 4 slightly.
7. **Undocumented members are shown as written.** The Material Document marks the 18 members as undocumented, `FrqType` included, although it occurs in every file.
8. **There are no categories to import.** Vendor (from a list of known prefixes, 690 files), type and material sets become filterable attributes. `[Folder]` is kept for the 11 fluids. The Area stays `materials`, as decided.
9. **No provenance can be cited.** Documents present values "as shipped in the CST 2024 material library". The only measurement context is the description line, such as "measured @ 10GHz".
10. **Exact duplicates are not Aliases.** In the code tree, an Alias is the same Document published twice. Here the two files are different products, and the name is their identity (`Rogers RO3003 (loss free)`, `Taconic NF-30 (loss free)`). Each keeps its own Document, with a "same definition as" relation.
11. **Links from code to materials are by exact stem.**
    - They cover 112 occurrences of 4 stems, 96 of them `PEC` and `Vacuum`. These are worth a link, but not a place in usage rankings.
    - The 9 inline `With Material` copies that carry a library name are linked to that material. The 7 whose body differs are flagged "copy differs".
12. **Search skips the table rows.** Table rows are 76% of the lines and hold nothing searchable. Material Documents index the name, the qualifiers, `[Attributes]` and `[Description]`, and keep the rows out of the full-text index (ADR 0008).
13. **ADR 0001 applies.** These files are vendor data in CST form, so tests use synthetic `.mtd` fixtures.

**Judgment calls (recommendation first)**

1. **Rendering: metadata first, definition verbatim.**
   - *Recommended:* in this order:
     1. the title (the exact name) and a "use as" line, `.Material "<exact name>"`;
     2. a metadata table per material set: set, type, ε or the table summary, μ, σ, tan δ at its frequency, dispersion model, and thermal and mechanical values, all with units;
     3. `[Attributes]` and `[Description]`, verbatim;
     4. the variants (the other loss qualifier, CHT, physical qualifiers) and the "same definition as" names, as Locator links;
     5. the `[Definition]` in a fenced `vb` block.
   - *Option:* also show the definition wrapped in the history block of section 9.4, ready for an agent to send through the Control Server. It stays labelled as inferred until user question 8 is answered.
   - *Alternative:* the file verbatim with no derived metadata. It is simpler, but agents would then read ε = 1 for 450 materials.
2. **Sections.** One Section holds the metadata, attributes and description, and a second holds the definition. Tables of more than about 150 rows (90 files) go into a third, data-only Section that is rendered but not indexed.
3. **Name table: several keys per material, each returning the exact name.**
   - Keys:
     - the exact stem;
     - the base without the trailing loss qualifier: `Rogers RO4350B` returns the `(lossy)` and `(loss free)` files, with the qualifier as an attribute;
     - the name without the vendor prefix (`RO4350B`, `RT-duroid 5880`). It also matches longer names such as `Rogers RO4350B LoPro (lossy)`, which rank after the exact base;
     - a normalised key: lowercase, with punctuation and spaces dropped and numbers compared by value. Then `FR4` finds `FR-4`, `RT duroid` finds `RT-duroid`, and `Dk=2.2` finds `Dk=2.20`;
     - hand-written aliases (`Teflon` → `PTFE`, `Kapton` → `Polyimide`) as Synonym Sets, only if user question 9 says so.
   - Filterable attributes: type per set, qualifier, vendor, the sets present, and "fitted dispersion".
   - "Which copper material for a lossy metal" then becomes `copper` with type Lossy metal. That returns `Copper (annealed)` and `Copper (pure)`, both Lossy metal in their `all` set, with conductivity and description in the result lines.
   - *Ranking:* with MWS preferred, `(lossy)` comes before `(loss free)` when the query names no qualifier, and both are always returned. CHT fluids rank last for EM queries.
4. **Panasonic and other large families.** Keep one Document per file, since the name is the identity. In lookup results, group them by product (for example `Panasonic MEGTRON6 Laminate R-5775`), with the thickness and cloth-style variants as a compact list.
5. **Materials and the usage index.** Leave material files out of the API usage lists; otherwise `Material.Colour` would list 779 "examples". Instead, give the API Entry of each Material member one count: "set in N library materials".
6. **Glossary.** Consider adding **Material set**: the block of a Material's properties for one problem type (`FrqType` `all`, `static` or `hf`), as the Material Library dialogs call it.
