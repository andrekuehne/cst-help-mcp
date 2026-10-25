# CST Help Knowledge Base

Tooling that turns a user's own licensed CST Studio Suite documentation into a Knowledge Base folder that agents read with their own file tools, so that generated macros, scripts and how-to answers are grounded in the documentation.

## Language

### Building and holding documentation

**Knowledge Base**:
The self-contained, relocatable result of a build: readable documents, their images and originals, the copied Library code and PDFs, and the index files agents navigate by. Built from one user's licensed documentation; never distributed with the tool.
_Avoid_: KB bundle, output, corpus, index

**Release**:
One version of CST Studio Suite, such as 2024. Each Release is its own folder, and a session works in one Release together with the release-independent Collections.
_Avoid_: version, year

**Collection**:
A named unit of documentation that is built, replaced or removed as a whole. A Collection either belongs to one Release (everything shipped with that installation) or is release-independent, like separately gathered example PDFs, and then sits as a sibling folder beside every Release.
_Avoid_: corpus, module

**Area**:
A part of a Collection that comes from one help project or document family, such as VBA 3D, WinWrap Basic, Python, Example Projects, Manuals, Macros or Materials. An Area is a folder, so a grep can be confined to one.
_Avoid_: module, category, project

**Build**:
One immutable result of building a single Collection from its Sources. A Knowledge Base serves the Builds of its active Assembly, so a new Build takes over only after it is assembled.
_Avoid_: version, snapshot, run

**Assembly**:
One immutable combination of one Build per Collection, together with the entry files and `AGENTS.md` that come from them. A Knowledge Base has one active Assembly at a time.
_Avoid_: deployment, snapshot, index

**Source**:
One input folder of a Collection together with the format it is written in, such as RoboHelp help, a Sphinx reference, a folder of PDFs or the Library.
_Avoid_: input, adapter

**Document**:
One help topic, one PDF, or one code or data file from the Library, within a Collection.
_Avoid_: page, file, topic (except when speaking of RoboHelp itself)

**Text Companion**:
The Markdown beside a PDF Document that holds the text of each of its pages under a `page-<n>` anchor, named after the PDF with `.md` appended. It is the Document's Locator; agents grep it to find the page, then open the PDF at that page.
_Avoid_: sidecar, extract, transcript

**Alias**:
Another source path under which the same Document was published identically; a link to an Alias reaches the Document.
_Avoid_: duplicate, copy

**Section**:
An addressable part of a Document, reached by its anchor.
_Avoid_: chunk, passage

**Ribbon Path**:
The line under a dialog topic's title that says where the dialog is reached in CST's ribbon, such as "Simulation: Solver > Setup Solver". Metadata of the Document, not one of its headings.
_Avoid_: breadcrumb (a breadcrumb is a table-of-contents path), menu path (reserved for the Library)

**Asset**:
An image or other non-text file that a Document references.
_Avoid_: attachment, resource

**API Entry**:
One documented VBA object, method or property, Python class, function or method, or WinWrap Basic keyword or built-in function (`Left$`, `Begin Dialog`), addressable by its Area and qualified name. The same qualified name can exist in several Areas, as with the VBA `Solver` object.
_Avoid_: symbol, command

**Locator**:
The single address of a Document or Section, a path into the Knowledge Base's files, with an anchor for a Section.
_Avoid_: ID, reference, URL

### CST's example code

**Example Project**:
One of the tutorial projects published inside CST's help (the `EXP_*` projects), together forming the Example Projects Area.
_Avoid_: example, tutorial

**Library**:
CST's folder of ready-made Macros, Result Templates, Includes, Material Definitions and Python apps, shipped with each Release (CST's "Global Library Path"). Used only for this folder.
_Avoid_: using "library" for a Collection or the Knowledge Base

**Macro**:
A VBA program started from CST's Macros menu: a control macro, or a structure macro whose commands are recorded into the history list.
_Avoid_: script (reserved for Python), VBA file

**Result Template**:
A VBA program that CST's template-based post-processing calls through its `Define` and `Evaluate` functions to produce results.
_Avoid_: post-processing template, RTP

**Include**:
A VBA file of shared helper procedures that Macros and Result Templates pull in with `'#include`.
_Avoid_: lib, library file

**Helper**:
A public procedure or variable defined in an Include, addressable by name. Library code relies on Helpers, but they are not part of the documented CST API and never count as API Entries; `AGENTS.md` says so.
_Avoid_: lib function, utility, API

**Python app**:
A Python program in the Library that CST starts from a menu, described by a JSON descriptor that gives its menu path and the module it runs. Its modules drive CST through the `cst` package and send VBA as string literals through `add_to_history` or `execute_vba_code`.
_Avoid_: CST App (the help's name for the menu), script

**Material Definition**:
A Library file that defines one named material of CST's material database, together with its electromagnetic and thermal properties. Its file name is the material's exact name.
_Avoid_: material file, MTD

**Material Set**:
The part of a Material Definition that holds its properties for one problem type (all, static or high frequency), as CST's Material Library dialogs call it.
_Avoid_: property block, profile

**Display Name**:
The name under which CST shows a Macro or Result Template: its file name before the Application Filter, under its folder path as the menu path.
_Avoid_: title, menu title

**Application Filter**:
The suffix of a Library file name that says in which CST applications (such as MWS, DS, EMS) the item is shown or hidden.
_Avoid_: app suffix, caret suffix

**Variant**:
One of several Library items with the same Display Name in the same folder that differ only in their Application Filter.
_Avoid_: duplicate, copy

### Derived from the documentation

**Undocumented Member**:
A VBA object member that Library code uses but no help page documents. An agent that finds one by grep reports it as such instead of as "not documented".
_Avoid_: hidden API, internal API

**Guide**:
A generated Markdown file in the workspace that summarises patterns, idioms and pitfalls across many Documents and Library files, always marked as generated and citing the Locators it draws on.
_Avoid_: infosheet, summary, cheat sheet

### Around the Knowledge Base

**Control Server**:
A separate MCP server that drives a running CST Studio Suite, such as mcp-cst-studio. The Knowledge Base informs what an agent sends to it but never executes anything itself.
_Avoid_: CST MCP, automation server
