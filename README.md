# cst-help

`cst-help` builds a private Knowledge Base from your own CST Studio Suite installation: a folder of
Markdown that coding agents (Claude Code, Codex, Cursor) read with their own file tools. There is no
server and no database. The folder is the product (ADR 0014).

The documentation is Dassault Systèmes' copyrighted material, licensed to you. The tool contains none
of it; every user builds from their own installation, and the built folder stays private (ADR 0001).

## What it produces

```
<kb>/
  cst-2024/                 one folder per Release: open this one
    AGENTS.md               what is where and how to find it with grep; CLAUDE.md imports it
    toc.md                  CST's table of contents, as nested links
    keywords.md             CST's author keyword index, each term linking to its pages
    api.md                  every API Entry on one line: name, Area, signature, path with anchor
    3d/ vba_3d/ general/ …  one Markdown page per help topic, with frontmatter (title, Area, source,
                            table-of-contents paths, keywords); the file path is the page's Locator
    assets/                 the images the pages show, as PNG or JPEG
    work/ guides/           for what agents write; builds and assemblies carry them over untouched
  cst-2025/                 a second Release, if you build one, beside the first
  pdfs/                     a release-independent Collection of PDFs, beside every Release
    AGENTS.md               what the folder holds; every Release's AGENTS.md points at it
    documents.md            every PDF on one line, with the CST version it was written for
    <name>.pdf, .pdf.md     each PDF as it is, with its Text Companion
  AGENTS.md                 lists the Releases and tells a session to stay in one; CLAUDE.md imports it
  builds/ assemblies/       immutable Builds and their manifests, reports and navigation data
  active.json               the pointer to the active assembly
```

Only what agents read goes into a Release folder, so a grep there returns pages and nothing else.
Every assembly regenerates `AGENTS.md`, `CLAUDE.md` and the index files, so don't edit them.
Each Build's report (`builds/<collection>/<build>/report.json`) lists what could not be converted.

## Building

Describe the Knowledge Base in a TOML file, such as the development `cst-help.toml`:

```toml
[knowledge_base]
path = 'C:\cst-help-kb'

[collections.cst-2024]
release = "2024"

[[collections.cst-2024.sources]]
type = "cst-release"
path = 'C:\Program Files (x86)\CST Studio Suite 2024'
```

A folder of PDFs gathered apart from any Release is a release-independent Collection: it takes
no `release`, and each PDF states the CST version it was written for when its file name, title or
first pages name one ("CST Studio Suite 2023").

```toml
[collections.pdfs]

[[collections.pdfs.sources]]
type = "pdf-folder"
path = 'C:\CST PDFs'
```

Then build each Collection, and check the result:

```bash
uv run cst-help build cst-2024 --config cst-help.toml
```

```bash
uv run cst-help validate --kb C:\cst-help-kb
```

A single Release builds without a TOML file too: `--source` names the installation (or a copy of
its `Online Help`, `Documentation` and `Library` folders) and `--kb` the Knowledge Base. The Release
comes from a name like `cst-2024`, or from `--release`.

```bash
uv run cst-help build cst-2024 --source "C:\Program Files (x86)\CST Studio Suite 2024" --kb C:\cst-help-kb
```

`build` converts the Collection into a new Build and assembles it: the Release folder switches to the
new Build only once it is complete. `--strict` fails the build if any Document fails. `assemble`
rebuilds the Release folders from the newest Builds, which also repairs a damaged folder.
Each Collection builds on its own, so adding PDFs to the folder and running `build pdfs` rebuilds
only that Collection.
`remove <collection> --kb <kb>` removes a Collection, such as an old Release: its folder, with
what agents wrote into `work/` and `guides/`, and its Builds. Nothing else removes one.
`validate` checks the Builds' files against their manifests and every link between the pages.

## Opening it in an agent

Open a session in the Release folder (`<kb>/cst-2024`) and ask:

- **Claude Code:** `cd` into the folder and run `claude`.
- **Codex:** `cd` into the folder and run `codex`.
- **Cursor:** File > Open Folder, and pick the folder.

To consult the Knowledge Base from one of your own project repositories instead, add the folder to
that project's sessions. `cst-help instructions` prints the folder's path and an `AGENTS.md` section
to paste into the project: how to add the folder (`claude --add-dir`, `codex --add-dir`, or File >
Add Folder to Workspace in Cursor) and how to find things in it with grep.

```bash
uv run cst-help instructions --kb C:\cst-help-kb
```

## Developing

```bash
uv run pytest
```

Tests build from the real CST 2024 corpus in `.ingestion/2024/` (see `tests/conftest.py`). The
benchmark in `docs/benchmark.toml` is scored by agents run from the folder with file tools only:
`scripts/agent-run.py` runs each question and counts the tool calls to the first expected page
(see its docstring and `docs/benchmark-draft.md`).
