"""What a project repository needs to consult the Knowledge Base: the Release folder and an AGENTS.md
section that says how to add it to a session and how to navigate it (ADR 0014).

The rules and recipes are those of the hand-written AGENTS.md that answered the benchmark from
the folder alone (`.scratch/cst-help-kb/files-only-experiment.md`).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from cst_help_mcp import layout
from cst_help_mcp.errors import KnowledgeBaseError


@dataclass(frozen=True)
class ReleaseFolder:
    """The readable view of one Collection of a Release, as the active assembly holds it."""

    collection: str
    release: str
    path: Path
    failed: int  # Documents that failed to build
    pages: Counter[str]  # Documents by top-level folder


def release_folders(kb_path: Path, release: str | None = None) -> list[ReleaseFolder]:
    """The folders of one Release, the newest by default."""
    assembly = layout.assemblies_dir(kb_path) / layout.active_assembly(kb_path)
    folders = []
    for collection, build in layout.assembly_builds(assembly).items():
        manifest = layout.BuildManifest.read(layout.build_dir(kb_path, collection, build))
        pages = Counter(
            locator.partition("/")[0] if "/" in locator else "." for locator in manifest.documents
        )
        folders.append(
            ReleaseFolder(
                collection, manifest.release, (kb_path / collection).resolve(), manifest.failed, pages
            )
        )
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


RULES = """\
- **Grep finds pages; it never answers.** Before you answer, open every page you cite with your
  read tool, even when the grep lines already seem to hold the answer. A snippet leaves out the
  conditions, figures and exceptions around it. Pages are short; most are under 10 KB.
- Cite the file path and the Release of every page you rely on.
- If an identifier is in no page under `vba_3d/`, say it is not documented in this Release. Never
  invent a method, its arguments or its behaviour.
- Some answers are only in a figure. Open the image file with your read tool; equation images are
  not transcribed, so look rather than guess."""

ANATOMY = """\
- `toc.md` is CST's table of contents as nested links; `keywords.md` is CST's author keyword
  index, the authors' own terms, each linking to the pages it means. `assets/` holds the images.
- Every page has frontmatter: `title`, `area`, `source`, and when CST gave them, `keywords` and
  `toc_paths`. Links between pages are relative to the Release folder.
- Dialog pages: the `## ` line right under the title is the Ribbon Path, where the dialog is
  reached in the CST ribbon. Dialog fields are bold lines with a `: ` definition under them.
- VBA pages under `vba_3d/`: one page per object, `## General Methods` and similar groups, then
  `### MethodName` with a ```vba signature block and the description.
- Folder names in `3d/` say what a page is: `special_solvopt_*` solver and setup dialogs,
  `special_overview_*` overviews, `special_theory_*` theory, `special_postpr_*` post-processing,
  `special_process_*` parameter sweeps and optimisation, `common_*` shared across products."""

RECIPES = """\
**An identifier** (`Solver.FrequencyRange`, a bare `FrequencyRange`, an object name): grep the
member as a heading, case-insensitively, in `vba_3d/`: `^### FrequencyRange`. For an object, grep
its title: `^title: "Solver Object`. Then read the page or the heading's section.

**A concept or how-to question**: work from the vendor's own vocabulary outward.
1. Grep `keywords.md` for your main noun, case-insensitively.
2. Grep `toc.md` the same way to see the neighbourhood of pages.
3. Grep titles: `^title:.*discrete port` across `3d/`.
4. Only then grep bodies, with the two or three most specific words, listing files only (no
   context lines); then read the best match.
Prefer pages whose title or Ribbon Path matches over pages that merely mention the words. The
defining page is usually the dialog (`special_solvopt_*`) for settings, the overview
(`special_overview_*`) for concepts.

**Where a setting lives in the UI**: the Ribbon Path line of the dialog page.

**Which VBA call does what a dialog does**: find the dialog page in `3d/`, then grep the dialog's
title words in `vba_3d/` titles; dialog and object usually share a name (Solver Parameters and
`Solver Object`, Port and `Port Object`).

**Theory and equations**: `special_overview_*` and `special_theory_*` pages in `3d/`. TeX is inline
as `$…$` or `\\begin{equation}`; where an equation is an image, open it.

**Terminology**: CST says "transient" and "time domain" for the same solver, "farfield" for
radiation patterns, "monitor" for a field recording, "port" for excitation; the VBA `Solver`
object is the time domain solver, `FDSolver` the frequency domain solver."""


def agents_section(folders: list[ReleaseFolder]) -> str:
    """The AGENTS.md section for a project repository that consults one Release."""
    release = folders[0].release
    paths = ", ".join(f"`{f.path}`" for f in folders)
    first = folders[0].path
    pages = Counter[str]()
    for f in folders:
        pages.update(f.pages)
    table = "\n".join(f"| `{name}/` | {count:,} |" for name, count in sorted(pages.items()) if name != ".")
    return f"""\
The CST Studio Suite help of Release {release} is a folder of Markdown files: {paths}. Every page
is the vendor's text. Consult it with your own file tools (grep, glob, read); there is no server.
The paths below are relative to that folder.

Add the folder to the session before you need it:
- Claude Code: start with `claude --add-dir "{first}"`, or run `/add-dir {first}`.
- Codex: start with `codex --add-dir "{first}"`.
- Cursor: File > Add Folder to Workspace, and pick the folder.

{_incompleteness(folders)}### Rules

{RULES}

### What is where

| Folder | Pages |
|---|---:|
{table}

{ANATOMY}

### Recipes

{RECIPES}
"""


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
