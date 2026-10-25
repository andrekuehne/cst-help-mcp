"""How agents find their way around a Release folder: the AGENTS.md that assembly writes into it, and
the AGENTS.md section that a project repository adds to consult it from outside (ADR 0013, ADR 0014).

Both are built from the same rules and recipes, those of the hand-written AGENTS.md that answered
the benchmark from the folder alone (`.scratch/cst-help-kb/files-only-experiment.md`).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.library import TREE_FOLDER


@dataclass(frozen=True)
class ReleaseFolder:
    """The readable view of one Collection of a Release, as the active assembly holds it."""

    collection: str
    release: str
    path: Path
    failed: int  # Documents that failed to build
    pages: Counter[str]  # Documents by top-level folder

    @classmethod
    def of(cls, manifest: layout.BuildManifest, path: Path) -> ReleaseFolder:
        """The view at ``path`` of the Build that ``manifest`` describes."""
        pages = Counter(
            locator.partition("/")[0] if "/" in locator else "." for locator in manifest.documents
        )
        return cls(manifest.collection, manifest.release, path, manifest.failed, pages)


def release_folders(kb_path: Path, release: str | None = None) -> list[ReleaseFolder]:
    """The folders of one Release, the newest by default."""
    assembly = layout.assemblies_dir(kb_path) / layout.active_assembly(kb_path)
    folders = []
    for collection, build in layout.assembly_builds(assembly).items():
        manifest = layout.BuildManifest.read(layout.build_dir(kb_path, collection, build))
        folders.append(ReleaseFolder.of(manifest, (kb_path / collection).resolve()))
    releases = sorted({f.release for f in folders})
    if not releases:
        raise KnowledgeBaseError(f"The Knowledge Base at {kb_path} holds no Release")
    if release is None:
        release = releases[-1]
    elif release not in releases:
        raise KnowledgeBaseError(
            f"The Knowledge Base at {kb_path} has no Release '{release}'; available: {', '.join(releases)}"
        )
    return [f for f in folders if f.release == release]


# What each top-level folder holds, for the table of folders.
FOLDERS = {
    "3d": "3D simulation: solver dialogs, overviews, theory, post-processing, modelling",
    "vba_3d": "VBA object reference: one page per object, one `###` heading per member",
    "vba": "Overview of the VBA macro language",
    "sax_basic": (
        "WinWrap Basic language reference: the macro language's keywords and built-in functions "
        "(`Dir$`, `Open`, `Print #`, `Format$`, `MsgBox`), one page each"
    ),
    "general": "Product overview and general features",
    "userinterface": "The main window and its dialogs",
    "ribbons": "The ribbon pages",
    "advanced": "Command line, environment variables and other advanced topics",
    "license": "Licensing",
    "simulation_acceleration": "Simulation acceleration",
    "python": (
        "Python reference (`cst.interface`, `cst.results`, `cst.eda`, `cst.asymptotic`, `cst.radar`, "
        "`cst.units`), one page per package, and its overview"
    ),
    "manuals": (
        "Word manuals (Getting Started: installation, licensing, first steps; High Frequency "
        "Simulation: workflow and solver choice), each a PDF with a `.pdf.md` text companion"
    ),
    TREE_FOLDER: "CST's Library: Macros, Result Templates and Includes, as VBA code",
    ".": "Python menu topics (CST Apps, user scripts), also copied into `python/`",
}

# What each entry file at the root of a Release folder holds.
ENTRY_FILES = {
    layout.ENTRY_FILES["toc"][0]: "CST's table of contents, as nested links",
    layout.ENTRY_FILES["keywords"][0]: (
        "CST's author keyword index: the authors' own terms, each linking to the pages it means"
    ),
    layout.API_ENTRY_FILE: (
        "every API Entry on one line: qualified name, Area, signature, path with anchor; grep it, "
        "it is too long to read whole"
    ),
    layout.LIBRARY_ENTRY_FILE: (
        "every Library file on one line: kind, menu path and Display Name, Application Filter, "
        "Variants, first comment, Helpers"
    ),
}

ANATOMY = """\
- Every page has frontmatter: `title`, `area`, `source`, and when CST gave them, `keywords` and
  `toc_paths`. Links between pages are relative to the Release folder; `assets/` holds the images.
- Dialog pages: the `## ` line right under the title is the Ribbon Path, where the dialog is
  reached in the CST ribbon. Dialog fields are bold lines with a `: ` definition under them.
- VBA pages under `vba_3d/`: one page per object, `## General Methods` and similar groups, then
  `### MethodName` with a ```vba signature block and the description.
  `special_vba<topic>/..._object.htm.md` is one VBA object (for example
  `special_vbasolver/special_vbasolver_solver_object.htm.md` is the `Solver` object), and
  `common_vbaapp/` holds the application-level objects.
- WinWrap Basic pages under `sax_basic/`: file names are numbers (`ww_00069.htm.md`), so find a
  keyword by its title, `^title: "Dir\\$ Function`, or in `api.md`. Each has the syntax in a
  ```vba block, then `## Parameter Description` and `## Example`. `ww_00003.htm.md` lists the
  keywords by group. The operators (`Mod`, `And`, `Xor`, `^`) share one page, `ww_00179.htm.md`,
  and are not in `api.md`.
- Python pages under `python/source/`: one page per package (`cst.results.html.md`), each name
  under a heading with its dotted name and a ```python signature block, then its description and
  `**Parameters**`. `python/main.html.md` covers setup.
- Folder names in `3d/` say what a page is: `special_solvopt_*` solver and setup dialogs,
  `special_overview_*` overviews, `special_theory_*` theory, `special_postpr_*` post-processing,
  `special_process_*` parameter sweeps and optimisation, `common_*` shared across products."""

RECIPES = """\
**An identifier** (`Solver.FrequencyRange`, a bare `FrequencyRange`, an object name): grep
`api.md` for it, which gives the signature and the page with its anchor; grep a bare member with
its dot and a trailing space, `.FrequencyRange `, to see every object that has it. Or grep the
member as a heading, case-insensitively, in `vba_3d/`: `^### FrequencyRange`. For an object,
grep its title: `^title: "Solver Object`. Then read the page or the heading's section.

**A macro language keyword or built-in** (`Left$`, `Open`, `Print #`, file and string handling,
`MsgBox`, dialogs): grep `api.md` for it, or the titles in `sax_basic/`. These are not CST objects;
they are the WinWrap Basic language that every macro is written in.

**A Python name** (`cst.results.ResultModule.get_run_ids`, a bare `get_run_ids`): grep `api.md`
for it; a name's last parts are enough (`ResultModule.get_run_ids`).

**A concept or how-to question**: work from the vendor's own vocabulary outward.
1. Grep `keywords.md` for your main noun, case-insensitively. The index terms are the authors'
   synonyms; "Transient Solver Parameters" points at the time domain solver dialog.
2. Grep `toc.md` the same way to see the neighbourhood of pages.
3. Grep titles: `^title:.*discrete port` across `3d/`.
4. Only then grep bodies, with the two or three most specific words, listing files only, and narrow
   by a second word.
5. For a choice (which port or solver, when one is good enough), also grep `manuals/`: the
   manuals weigh the options against each other, the help describes each alone.
Prefer pages whose title or Ribbon Path matches over pages that merely mention the words. Read the
one or two most likely pages. The defining page is usually the dialog (`special_solvopt_*`) for
settings, the overview (`special_overview_*`) for concepts.

**Which VBA call does what a dialog does**: find the dialog page in `3d/`, then grep the dialog's
title words in `vba_3d/` titles; dialog and object usually share a name (Solver Parameters and
`Solver Object`, Port and `Port Object`).

**A manual** (installation, the workflow of a solver, choosing between solvers or ports): grep the
text companions in `manuals/`, the `.pdf.md` files, which hold each page's text under a
`## page-<n>` heading. A hit's page is the nearest such heading above its line; grep with line
numbers to find both. Read that section; open the PDF at that page when the layout, a table or a
figure matters. Cite the PDF and its page.

**Theory and equations**: `special_overview_*` and `special_theory_*` pages in `3d/`. TeX is inline
as `$…$` or `\\begin{equation}`; where an equation is an image, open it.

**Terminology**: CST says "transient" and "time domain" for the same solver, "farfield" for
radiation patterns, "monitor" for a field recording, "port" for excitation; the VBA `Solver`
object is the time domain solver, `FDSolver` the frequency domain solver."""


LIBRARY_RECIPES = """\
**Working code**: grep `library/` for the API Entry or idiom, listing files only, or `library.md`
for a menu path or Display Name; prefer the `+MWS` Variant. `'#include "X"` is the file
`library/Includes/X`; a public procedure there (`GetLastResult_LIB`) is a Helper, not a
documented CST API Entry. A dialog's `.bmp` is beside its Macro as a `.png`."""


def recipes(folders: list[ReleaseFolder]) -> str:
    """The recipes, with the Library's when the folders hold one."""
    if any(TREE_FOLDER in f.pages for f in folders):
        return f"{RECIPES}\n\n{LIBRARY_RECIPES}"
    return RECIPES


def rules(folders: list[ReleaseFolder]) -> str:
    """The rules, first among them that grep finds pages and never answers."""
    release = folders[0].release
    if any(TREE_FOLDER in f.pages for f in folders):
        documented = f"""\
- If an identifier is in no page under `vba_3d/`, `sax_basic/` or `python/` and nowhere in
  `library/`, say that it is not documented in Release {release}. Never invent a method, its
  arguments or its behaviour.
- A member that code in `library/` uses but no page documents is an Undocumented Member: use it
  only knowingly, and say that it is one."""
    else:
        documented = f"""\
- If an identifier is in no page under `vba_3d/`, `sax_basic/` or `python/`, say that it is
  not documented in Release {release}. Never invent a method, its arguments or its behaviour.
  This folder holds no Library, so there is no Undocumented Member (one that Library code uses
  but no page documents) to find."""
    return f"""\
- **Grep finds pages; it never answers.** Before you answer, open every page you cite with your
  read tool, even when the grep lines already seem to hold the answer. A snippet leaves out the
  conditions, figures and exceptions around it. Pages are short; most are under 10 KB. Grep
  bodies with no context lines.
- Cite the file path and the Release of every page you rely on.
{documented}
- Some answers are only in a figure. Open the image file with your read tool; equation images are
  not transcribed, so look rather than guess. A manual's figures are only in its PDF."""


def agents_md(folder: ReleaseFolder) -> str:
    """The AGENTS.md at the root of a Release folder, which a session opened there reads first."""
    release = folder.release
    return f"""\
# CST Studio Suite {release} help, as files

This folder is the CST Studio Suite help of Release {release}, converted to Markdown:
{folder.pages.total():,} pages. Every page is the vendor's text; nothing but the Guides was written
by a model. Use your own file tools: grep, glob, read. Paths are
relative to this folder. Write what you make, such as macros and notes, into `{layout.WORK_DIR}/`.

{_incompleteness([folder])}## Rules

{rules([folder])}

## What is where

{_folder_table([folder])}

{_entry_files(folder)}

## Page anatomy

{ANATOMY}

## Recipes

{recipes([folder])}

## Guides

{_guides(folder)}
"""


def agents_section(folders: list[ReleaseFolder]) -> str:
    """The AGENTS.md section for a project repository that consults one Release."""
    release = folders[0].release
    paths = ", ".join(f"`{f.path}`" for f in folders)
    first = folders[0].path
    return f"""\
The CST Studio Suite help of Release {release} is a folder of Markdown files: {paths}. Every page
is the vendor's text. Consult it with your own file tools (grep, glob, read); there is no server.
The paths below are relative to that folder.

Add the folder to the session before you need it:
- Claude Code: start with `claude --add-dir "{first}"`, or run `/add-dir {first}`.
- Codex: start with `codex --add-dir "{first}"`.
- Cursor: File > Add Folder to Workspace, and pick the folder.

{_incompleteness(folders)}### Rules

{rules(folders)}

### What is where

{_folder_table(folders)}

{_entry_files(folders[0])}

{ANATOMY}

### Recipes

{recipes(folders)}
"""


def _folder_table(folders: list[ReleaseFolder]) -> str:
    pages = Counter[str]()
    for f in folders:
        pages.update(f.pages)
    rows = [
        f"| {'`' + name + '/`' if name != '.' else '(top level)'} | {count:,} | {FOLDERS.get(name, '')} |"
        for name, count in sorted(pages.items(), key=lambda item: (item[0] == ".", item[0]))
    ]
    return "\n".join(["| Folder | Pages | Content |", "|---|---:|---|", *rows])


def _entry_files(folder: ReleaseFolder) -> str:
    present = [f"- `{name}`: {what}" for name, what in ENTRY_FILES.items() if (folder.path / name).is_file()]
    return "Entry files at the root of the folder:\n" + "\n".join(present)


def _guides(folder: ReleaseFolder) -> str:
    guides = sorted((folder.path / layout.GUIDES_DIR).glob("*.md"))
    if not guides:
        return f"`{layout.GUIDES_DIR}/` holds Guides that agent sessions write. There are no Guides yet."
    listed = "\n".join(f"- `{layout.GUIDES_DIR}/{guide.name}`" for guide in guides)
    return (
        "Guides are generated by agent sessions, not the vendor's text: check every claim against the "
        f"pages a Guide cites before you rely on it.\n\n{listed}"
    )


def _incompleteness(folders: list[ReleaseFolder]) -> str:
    failed = [f for f in folders if f.failed]
    if not failed:
        return ""
    lost = "; ".join(
        f"{f.failed} Document{'s' if f.failed != 1 else ''} of Collection {f.collection} failed to build"
        for f in failed
    )
    return (
        f"This Knowledge Base is incomplete: {lost}. A 'not documented' answer may come from a "
        "Document that failed, so tell the user when you rely on one.\n\n"
    )
