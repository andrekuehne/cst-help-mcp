# CST Studio Suite 2024 documentation corpus: profile

Facts gathered from the installed CST Studio Suite 2024 help and manuals, to inform the design of an ingestion tool. Nothing in the corpus was modified.

- **Corpus root:** `.ingestion/2024/` (local, licensed copy; not committed, see ADR 0001).
- **Path convention:** unless prefixed with `Documentation/`, every path below is relative to `.ingestion/2024/Online Help/`. `mP/` abbreviates `mergedProjects/`.
- **Method:** Python 3.12 standard-library scans (`os.walk`, `html.parser`, `xml.etree`, `zlib`, `hashlib`), plus `pypdf` for PDFs. Counts are exact for what was scanned. Where a count depends on a heuristic, the text says so.
- **Excerpts** show markup structure only. Vendor prose has been left out on purpose.

---

## 1. Inventory

`Online Help/` holds **13,996 files, 608.7 MB**. `Documentation/` holds 11 PDFs, 74.8 MB.

By extension across `Online Help/`:

| Extension | Files | MB |
|---|---:|---:|
| .js | 1,231 | 232.5 |
| .png | 5,247 | 162.5 |
| .htm | 5,362 | 85.6 |
| .svg | 44 | 72.8 |
| .jpg | 536 | 15.6 |
| .gif | 1,084 | 12.8 |
| .zip | 2 | 8.6 |
| .bmp | 21 | 7.8 |
| .html | 205 | 4.6 |
| other (.css .ico .log .lng .woff .xml .txt .pdf .ffs .nfd .inv .json ...) | 264 | ~5 |

Two items take a large share of the bytes:

- **MathJax 3.2.0 is copied 16 times.** There is one 12.0 MB copy (24 files) under `mathjax/` and one under each `mP/*/mathjax/`, plus the 17.5 MB Sphinx copy in `Python/_static/MathJax/`. Together they make up about 198 MB of the 232 MB of JS.
- **A single unreferenced 65.9 MB SVG** sits at `Python/_static/images/radar/range_angle_xy_targets.svg`. The pages reference a PNG version under `_images/` instead.

### Per top-level subtree

"Topic pages" means content pages. WebHelp skin and frame pages, `whgdata/` lists, search pages and framesets are excluded. Section 2 explains how pages were classified.

| Subtree | Files | MB | Dominant extensions | Topic pages |
|---|---:|---:|---|---:|
| (root files) | 139 | 0.9 | 34 gif, 33 htm, 32 png, 25 js | 2 (`menu.htm`, `user_scipts.htm`) + 31 WebHelp shell pages |
| `mergedProjects/` (15 modules) | 11,459 | 419.8 | see the next table | 2,676 |
| `FEST3D/` | 715 | 33.5 | 538 png (25.8 MB), 126 html, 24 css, 21 js (4.6 MB) | 118 |
| `SPARK3D/` (not listed in the brief) | 235 | 12.1 | 138 png, 51 html, 24 css, 21 js | 43 |
| `IdEM/` | 519 | 21.2 | 359 png, 138 htm, 1 zip (8.6 MB), 1 pdf (2.9 MB) | 107 content pages (+ frameset, `help_home.htm`, 28 menu pages) |
| `Python/` | 172 | 92.2 | 83 js (17.6 MB), 28 svg (72.3 MB), 23 woff, 21 png, 11 html | 8 (+ 3 generated: genindex, py-modindex, search) |
| `sax_basic/` | 315 | 2.1 | 315 htm | 315 |
| `ribbons/` | 57 | 1.0 | 29 png, 28 htm | 28 |
| `userinterface/` | 38 | 1.2 | 22 htm, 16 png | 22 |
| `general/` | 70 | 2.6 | 50 png, 19 htm | 19 |
| `advanced/` | 6 | 0.1 | 6 htm | 6 |
| `simulation_acceleration/` | 29 | 0.6 | 25 png, 4 htm | 4 |
| `license/` | 3 | <0.1 | 3 htm | 3 |
| `vba/` | 8 | 0.3 | 7 png, 1 htm | 1 |
| `mathjax/` | 24 | 12.0 | js | 0 |
| `search_files/` (Zoom search engine) | 5 | 5.8 | 4 js, 1 html | 0 |
| `whdata/`, `whgdata/`, `whxdata/` (root WebHelp nav data) | 11 / 116 / 15 | 0.0 / 2.1 / 0.8 | js, htm, xml | 0 |
| `icon_images/`, `image/`, `resource/`, `analysis/` | 39 / 19 / 1 / 1 | ~0.1 | png, js | 0 |

The 2 + 400 topic pages at the root and in its own subtrees (`advanced`, `general`, `license`, `ribbons`, `sax_basic`, `simulation_acceleration`, `userinterface`, `vba`) belong to the top-level RoboHelp project. The root full-text topic table lists 399 of them.

### Per `mergedProjects` module

Every module also carries its own WebHelp runtime:

- 66 to 87 JS files (12 to 18 MB including its MathJax copy). `mP/Python` is the exception: 44 JS files, 0.4 MB, no MathJax.
- About 30 to 40 skin GIFs.
- 61 to 311 navigation HTML pages under `whgdata/`, `whdata/` and the module root.

| Module | Files | MB | htm/html | Topic pages | Images (png/gif/jpg/bmp/svg) |
|---|---:|---:|---:|---:|---|
| 3D | 3,398 | 95.2 | 1,414 | 1,103 | 1,385 / 319 / 165 / 3 / 0 |
| DES | 1,816 | 41.4 | 803 | 541 | 795 / 113 / 12 / 7 / 0 |
| VBA_3D | 799 | 29.7 | 609 | 372 | 55 / 39 / 8 / 0 / 0 |
| EXP_HF | 1,053 | 46.7 | 294 | 159 | 504 / 126 / 50 / 0 / 0 |
| Filter_Designer_3D | 563 | 18.6 | 219 | 116 | 210 / 32 / 7 / 0 / 16 |
| PCB | 673 | 26.2 | 255 | 110 | 161 / 41 / 135 / 0 / 0 |
| EXP_LF | 708 | 39.0 | 182 | 72 | 338 / 55 / 54 / 0 / 0 |
| EXP_DES | 612 | 29.9 | 180 | 68 | 301 / 38 / 8 / 7 / 0 |
| VBA_DES | 307 | 18.0 | 157 | 47 | 10 / 48 / 8 / 4 / 0 |
| EXP_MP | 367 | 17.9 | 133 | 40 | 106 / 42 / 8 / 0 / 0 |
| EXP_PD | 276 | 15.3 | 114 | 23 | 35 / 41 / 8 / 0 / 0 |
| EXP_PCB | 275 | 14.8 | 94 | 9 | 32 / 38 / 35 / 0 / 0 |
| CHI | 229 | 13.0 | 90 | 8 | 21 / 32 / 7 / 0 / 0 |
| EXP_CBL | 220 | 13.4 | 83 | 7 | 15 / 38 / 8 / 0 / 0 |
| Python | 163 | 0.7 | 62 | 1 | 6 / 33 / 7 / 0 / 0 |

Other files that are not pages:

- RoboHelp build manifests (`*.log`), for example `mP/3D/online_help.log` and `de-online-help.log`.
- Placeholder `readme.txt` files (`mP/3D/readme.txt`) describing the "merged WebHelp" folder.
- Downloadable sample data: `mP/3D/example_files/*.ffs`, `*.nfd`, `nfs_example_files.zip`, `IdEM/Examples/idem_examples.zip` (Touchstone `.sNp` files), and `mP/3D/special_solvopt/sheettransimport.txt`.
- A FlexNet PDF at `IdEM/Installation/FlexLicenseAdministration.pdf`.

**Total topic pages: 3,354.** That is 3,076 RoboHelp, 161 Innovasys, 109 IdEM (107 content plus the frameset and home page) and 8 Sphinx.

---

## 2. Generators and how the projects are wired

### 2.1 RoboHelp: root project and all `mergedProjects/*`, plus `advanced`, `general`, `license`, `ribbons`, `sax_basic`, `simulation_acceleration`, `userinterface`, `vba`

- **Adobe RoboHelp 11, classic frameset WebHelp 5.50.** It is neither Responsive HTML5 nor frameless.
  - Entry pages declare it: `cst_studio_suite_help.htm` has `<meta name="generator" content="Adobe RoboHelp 11" />` and `<meta name="description" content="WebHelp 5.50" />`. The runtime library header in `whver.js` reads `//	WebHelp 5.10.006`.
  - 5,114 HTML files carry the RoboHelp 11 generator meta.
  - The output has classic WebHelp artifacts: `whskin_*.htm`, `whframes.js`, `whdata/`, `whgdata/`, `whxdata/`, `cshdat_webhelp.htm`, `whcsh_home.htm`. There are no `rh*.js` files.
  - The frameset entry `cst_studio_suite_help.htm` selects a navigation mode at runtime (`nWebhelpNavPaneMode = 1 //1: DHTML 2:PureHTML 3:Noframe`).
- **Source projects** are named in the build logs:
  - `de-online-help.log` has `|SourceProjectName:de-online-help.hpr` / `|DestinationProjectName:cst_studio_suite_help.htm`.
  - `mP/3D/online_help.log` names `online_help.hpr` → `index.htm`.
  - Each child module has its own `index.htm`, `index_csh.htm` and `index_rhc.htm`.
- **Topic pages are XHTML 1.0 Transitional.** They start with `<?xml version="1.0" encoding="utf-8"?>` (3,077 files) and include `whtopic.js` (3,075 files).
- **One top-level project with merged child projects.**
  - `whxdata/whproj_xml.js` (root) registers exactly 8 remote projects:
    ```xml
    <project homepage="general/welcome_de.htm" langid="1033" datapath="whxdata" toc="whtoc.xml" index="whidx.xml" brs="whbrs.xml">
      <remote url="mergedProjects/3D" /> <remote url="mergedProjects/DES" /> <remote url="mergedProjects/Filter_Designer_3D" />
      <remote url="mergedProjects/VBA_3D" /> <remote url="mergedProjects/PCB" /> <remote url="mergedProjects/VBA_DES" />
      <remote url="mergedProjects/CHI" /> <remote url="mergedProjects/Python" />
    </project>
    ```
    The root declares no `fts=` attribute. Each child declares `fts="whfts.xml"`. The child declarations are in `mP/<X>/whxdata/whproj_xml.js` (wrapper `mP/<X>/whproj_xml.js`).
  - **Child TOCs are spliced into the root TOC by placeholders.** `whxdata/whtdata0_xml.js` contains `<project name="3D" ref="mergedProjects/3D" />`, and `whxdata/whtoc_xml.js` records where each child sits:
    ```xml
    <toc root="whtdata0.xml">
      <project url="mergedProjects/VBA_3D" path="Automation and Scripting Visual Basic (VBA) ">
        <subpath name="Automation and Scripting"><subpath name="Visual Basic (VBA)"></subpath></subpath>
      </project> ...
    ```
  - **The seven example projects (`EXP_CBL`, `EXP_DES`, `EXP_HF`, `EXP_LF`, `EXP_MP`, `EXP_PCB`, `EXP_PD`) are published into `mergedProjects/` but are not registered as remotes and do not appear in the root TOC.**
    - Each one is a standalone WebHelp project whose own TOC has a single item (its introduction page), for example `mP/EXP_HF/whxdata/whtdata0_xml.js`.
    - Inbound `<a>` links from outside each project are rare: EXP_DES 4, EXP_HF 6, EXP_LF 1, EXP_MP 4. EXP_CBL, EXP_PCB and EXP_PD have none.
    - The "Tutorials and Examples > Overview" TOC entry (`general/cst_studio_suite_examples_overview.htm`) does not link to any EXP project.
    - They are, however, in the global Zoom search index (section 3.2).
  - **Other cross-tree wiring is done through ordinary TOC items:**
    - The 3D TOC links FEST3D and SPARK3D: `<item name="Fest3D" url="..\..\FEST3D\webframe.html" target="_top" />`.
    - The `mP/Python` TOC has one item, `..\..\Python\main.html`.
    - The DES TOC points into `..\3D\special_dslink\DS_Link.htm` and `..\..\userinterface\views\...`.
- **Root versus child homepages:** the root homepage is `general/welcome_de.htm`, and 3D's is `common_overview/common_overview_welcome.htm` (see `mP/*/whxdata/whproj_xml.js`).
- **Word-to-RoboHelp import residue:**
  - `class="MsoNormal"` or `mso-` styles appear in 107 files.
  - Image folders named like a Word HTML export (`*-dateien/imageNNN.png`, `*_files/imageNNN.png`) occur 42 times with 713 files, for example `mP/EXP_HF/examplesoverview/patch_antenna-dateien/` and `mP/DES/analysis/simulation/tasks/transienttask/fromtd2fd_files/`.
  - CSS class names are often German: `Überschrift-Popup` (116 files), `StandardNeu`, `ZentriertesBild`, `DokuText`.

### 2.2 FEST3D and SPARK3D: Innovasys HelpStudio

- The navigation pages say so: `<meta name="GENERATOR" content="Innovasys (www.innovasys.com)" />` appears in `FEST3D/webtoc.html`, `webindex.html`, `websearch.html` and `webnav.html`, and in the same files under `SPARK3D/`.
- Topics are full of `<!--DXMETADATA start type="..."-->...<!--DXMETADATA end-->` template markers and initialise `Innovasys.Content.Document`.
- The matching PDFs report `Producer: Generated by HelpStudio` (`Documentation/CST Studio Suite - FEST3D User Manual.pdf`, `... SPARK3D User Manual.pdf`).
- The output type is frames-based "web" output with a responsive template:
  - `webframe.html` contains `<iframe id="i-content">` and `<iframe id="i-nav" src="webnav.html">`.
  - `webframedesktop.html`, `webframetablet.html` and `webframemobile.html` are variants.
  - Topics carry the settings JSON `"isFrameless":false,"navigationKind":"frames"`.
- The bundled libraries are jQuery 1.11.3 and jQuery UI 1.11.4 under `FEST3D/template/packages/`.
- All 177 FEST3D/SPARK3D HTML files start with a UTF-8 BOM.

### 2.3 IdEM: hand-built HTML 4 frameset

- `IdEM/index.htm` is `<frameset id="whPfset" cols="250,*">`. Its frames are named `colonna menu` and `bsscright`.
- The navigation script `IdEM/script_menu/funzioni.js` uses Italian identifiers (`aggiorna_menu`, `evidenzia_link`), and the content container is `<div id="corpo">`.
- Some menu files carry a `<!-- WebHelp version 5.10 -->` comment (`IdEM/menu/frame_menu.htm`), but no RoboHelp runtime or data files exist here.
- Generator metas are empty (`<meta name="generator" content="">`). No index or search is provided.

### 2.4 `Python/`: Sphinx 4.4.0

- Version evidence: `Python/main.html` says "Created using Sphinx 4.4.0", and topics carry `<meta name="generator" content="Docutils 0.17.1: ..." />`.
- The theme is `sphinxdoc`.
- `objects.inv` is Sphinx inventory v2 (`# Project: CST Python Libraries`, `# Version: 1.0`).
- Other build files present: `searchindex.js`, `genindex.html`, `py-modindex.html`, `search.html` and `.buildinfo`.
- `_static/documentation_options.js` sets `HAS_SOURCE: false`, so no `_sources/` folder is shipped.
- `sphinxcontrib-plantuml` output is present (`_plantuml/<hash>/*.png`, `_images/plantuml-*.png`).
- Math uses MathJax 3.2.0 `tex-chtml-full.js`.

### 2.5 Global search: Wrensoft Zoom Search Engine

- `search_files/search.html` begins with the comment "Search page for the JavaScript Wrensoft Zoom Search Engine".
- `search_files/settings.js` sets `Version = "Version 8.0.1012 ENT 64-bit"`, `NumPages = 3131`, `Charset = "windows-1252"`.
- RoboHelp's skin `whskin_tbars.htm` points at `search_files/`.

---

## 3. Navigation and editorial metadata

### 3.1 RoboHelp data formats

None of these files needs JS execution to read. Each `*_xml.js` file is a single assignment of a JS string literal holding an XML document:

```js
gXMLBuffer ="<?xml version='1.0' encoding='utf-8' ?>  <tocdata>  <item name=\"...\" url=\"...\" /> ... </tocdata>";
```

To read one: strip `gXMLBuffer = "` and the trailing `";`, decode the JS string escapes (`\"`, `\\`, `\uXXXX`), and parse the result as XML. All 16 projects parsed cleanly this way. The plain `.xml` siblings (`whxdata/whfts.xml`, `synonym.xml`) are real XML.

| Artifact | Files (per project) | Schema |
|---|---|---|
| Project manifest | `whxdata/whproj_xml.js` | `<project homepage langid datapath toc index fts brs glossary?>` + `<remote url>` |
| TOC wiring | `whxdata/whtoc_xml.js` | `<toc root="whtdata0.xml"><project url path><subpath name>` |
| TOC | `whxdata/whtdata0_xml.js` (one chunk in every project) | `<tocdata>` → `<book name url? target?>`, `<item name url target?>`, `<project name ref>` |
| Index (author keywords) | `whxdata/whidx_xml.js` (chunk list) + `whidata0_xml.js` | `<index><chunkinfo url first last num>` / `<indexdata><key name><topic name url/><key name>…</key></key>` |
| Glossary | `whxdata/whglo_xml.js` | `<glossary>    </glossary>`: **empty in all 16 projects**, including the 3 whose manifest declares `glossary="whglo.xml"` (EXP_HF, EXP_MP, VBA_DES) |
| Synonyms | `whxdata/synonym_xml.js`, `synonym.xml` | `<syn></syn>`: **empty in all projects** |
| Browse sequences | `whbrs_xml.js` (project root) | `<browsesequencelist><browsesequence name><item name link="dir\File.htm"/>` |
| Context-sensitive help | `whcsh_xml.js` (data); `cshdat_webhelp.htm`, `cshdat_robohelp.htm`, `whcsh_home.htm`, `whcshdata.js` (runtime) | `<csh-info><item mapid mapnum topicurl/>` |
| Full-text search | `whxdata/package_N_xml.js`, `packageindex_xml.js`, `topictable_N_xml.js`, `topictableindex_xml.js`, `whfts.xml` | words: `<pk><wd nm="word" rd="topicIdx,0:pos,pos|topicIdx,0:pos..."/>`; topics: `<ck><di ky="0" rd="url|Title" ct="first ~60 chars of text ..."/>` |
| Pure-HTML fallbacks | `whdata/whtdata0.htm`, `whidata0.htm`; `whgdata/whlstt*.htm` (TOC), `whlsti*.htm` (index), `whlstf*.htm` (FTS), `whlstg*.htm` (glossary) | `whdata/*.htm`: JS calls such as `aTE(2,0,"Title","url")`; `whgdata/*.htm`: static `<a href>` lists with `../` relative paths (the 3D FTS lists contain 2,521 backslash hrefs, all to `.txt` files) |

Excerpts:

```xml
<!-- mP/3D/whxdata/whtdata0_xml.js (after unescaping) -->
<book name="3D Simulation">
  <item name="Main Features" url="common_overview/common_overview_welcome.htm" />
  <item name="Fest3D" url="..\..\FEST3D\webframe.html" target="_top" />
  <book name="CAD Data Import and Export"> <item name="..." url="common_tools/..." /> ...

<!-- mP/3D/whxdata/whidata0_xml.js -->
<key name="2D Colormap">
  <topic name="2D Colormap Plot Overview" url="special_postpr/special_postpr_pp_colourmap.htm" />
  <topic name="Color Map Plot" url="common_ribbons/3d/common_ribbons_2dplot.htm" /> </key>
<key name="Macros"> <topic .../> <key name="Calculate / Calculate analytical Line Impedance"> <topic .../> ...

<!-- whcsh_xml.js (root) -->
<item mapid="DS_Online_Help_Welcome" mapnum="2501" topicurl="general/welcome_de.htm" />

<!-- mP/3D/whbrs_xml.js -->
<browsesequence name="common_GENERAL">
  <item name="Background Properties" link="common_general\common_general_background.htm" /> ...
```

Entry counts per project. TOC "items" are leaf entries and "books" are folders. Index "refs" are `<topic>` children. The FTS column gives distinct words / topics in the topic table.

| Project | TOC items / books / max depth | Index keys / refs / sub-keys | Browse seqs / items | CSH ids | FTS words / topics |
|---|---|---|---|---|---|
| (root) | 35 / 10 / 3 (+ 8 `<project>` refs) | 366 / 405 / 4 | 11 / 8 | 3 | 3,799 / 399 |
| 3D | 212 / 61 / 5 | 919 / 1,147 / 57 | 11 / 197 | 0 | 13,026 / 1,106 |
| DES | 378 / 71 / 7 (26 books carry a url) | 314 / 631 / 0 | 11 / 42 | 31 | 5,354 / 541 |
| VBA_3D | 310 / 59 / 6 | 733 / 734 / 0 | 24 / 72 | 0 | 9,632 / 372 |
| VBA_DES | 22 / 5 / 3 | 322 / 348 / 0 | 0 | 0 | 3,331 / 47 |
| PCB | 96 / 19 / 4 | 46 / 46 | 0 | 0 | 2,971 / 110 |
| Filter_Designer_3D | 44 / 6 / 4 | 44 / 44 | 0 | 0 | 1,450 / 116 |
| CHI | 7 / 1 | 1 / 1 | 0 | 0 | 544 / 8 |
| Python | 1 / 0 | 1 / 1 | 0 | 0 | 20 / 1 |
| EXP_HF | 2 / 1 | 149 / 286 | 2 / 49 | 0 | 3,497 / 159 |
| EXP_LF | 1 / 1 | 31 / 31 | 2 / 3 | 0 | 2,436 / 72 |
| EXP_DES | 1 / 1 | 1 / 1 | 2 / 0 | 0 | 2,581 / 68 |
| EXP_MP | 1 / 1 | 15 / 15 | 2 / 2 | 0 | 1,274 / 40 |
| EXP_PD | 1 / 1 | 19 / 19 | 2 / 2 | 0 | 1,136 / 23 |
| EXP_PCB | 1 / 1 | 0 | 0 | 0 | 677 / 9 |
| EXP_CBL | 1 / 1 | 0 | 0 | 0 | 204 / 7 |

Notes:

- **TOC coverage is partial.**
  - Only 1,343 of the 3,354 topic pages appear in any TOC (RoboHelp TOCs, the Innovasys `webtoc.html` files and the IdEM menu combined).
  - Per module: 3D 204 / 1,103, DES 367 / 541, VBA_3D 302 / 372, Filter_Designer_3D 44 / 116, EXP_HF 2 / 159, `sax_basic` 1 / 315, `ribbons` 0 / 28.
  - The other topics are reachable only through in-page links. Only 7 topic pages, all in IdEM, are reachable by neither a TOC nor any link.
- **Breadcrumb or TOC path is embedded in 1,096 of 3,076 RoboHelp topics** as a JS call, for example `addTocInfo("3D Simulation\nTheoretical Background\nPolarization");` in `mP/3D/special_theory/special_theory_polarization.htm`. The same pages build the visible breadcrumb with `document.write(...)` and `AddMasterBreadcrumbs(...)`.
- **CSH maps are nearly empty.** The root has 3 ids (mapnum 501, 2501, ...), DES has 31 (`DS_Online_Help_*` mapids), and every other project has none. The 3D project, the largest, has no CSH map.
- **TOC and index targets resolve well.** All index topic URLs resolve. The only failing TOC targets are `..\Licenses\Legal Notices.htm` (outside the corpus) and four case mismatches:
  - `..\..\userinterface\views\ParametricResultsOverview.htm` in the 3D and DES TOCs, while the file on disk is `parametricresultsoverview.htm`;
  - `..\3D\special_dslink\DS_Link.htm` versus `ds_link.htm`;
  - `..\3D\special_overview\EMS_DS_Co-Simulation_Overview.htm`.
- **Browse sequences are stale.**
  - Every link uses backslashes and the original mixed-case source names. For example, `mP/VBA_3D/whbrs_xml.js` has `common_VBAApp\common_VBAAppApplication_Object.htm` while the file on disk is all lower case.
  - Resolved case-sensitively, most targets fail. 3D: 182 of 197 ok, 14 missing. VBA_3D: 59 case-only, 13 missing. DES: 39 case-only, 3 missing. EXP_HF: 48 case-only, 1 missing.
  - The root has 11 sequences but only 8 items, most sequences being empty.

### 3.2 Zoom global search: `search_files/`

- `zoom_pageinfo.js` holds `pageinfo = [[0,0,0,2,"00000"], ...]` (category bit strings), then `pagedata = [["../cst_studio_suite_help.htm","Title","Description",""], ...]` with 3,131 rows.
- `zoom_index.js` holds `dictwords = ["word page score flags ...", ...]` with 26,572 keywords, followed by `skipwords` and `catnames`.
- `settings.js` defines 5 categories: "3D Simulation", "Circuits & Systems", "PCBs & Packages", "VBA", "Python".
- **The files are windows-1252, not UTF-8.** `settings.js`, `zoom_index.js` and `zoom_pageinfo.js` fail strict UTF-8 decoding.
- They can be parsed as JS array literals, and a regex is enough.
- **Coverage:**
  - Indexed: 3D 1,109, DES 544, VBA_3D 375, `sax_basic` 315, EXP_HF 161, Filter_Designer_3D 120, PCB 111, EXP_LF 74, EXP_DES 70, VBA_DES 50, EXP_MP 42, plus smaller subtrees, and 11 `.txt` files.
  - Not indexed: FEST3D, SPARK3D and IdEM. No PDFs are indexed.
- `mP/*/search_files/` contain only `search.html`.

### 3.3 Innovasys (FEST3D, SPARK3D)

- **TOC:** `webtoc.html`. It is static HTML (`<div id="i-toc-container"><ul id="i-root"><li rel="-1" data-is-new="False"><a href="intro.html">...`) with **no closing `</li>` tags**.
  - FEST3D: 127 `<li>`, of which 8 are group nodes with `href="#"`.
  - SPARK3D: 44 `<li>`.
  - All 118 / 43 page targets resolve.
- **Per-topic TOC metadata:**
  - `<meta name="Microsoft.Help.Id" content="<GUID>"/>`, `Microsoft.Help.TocParent` (parent GUID, or `-1`), `Microsoft.Help.TocOrder`, `Microsoft.Help.ContentType` (for example `Concepts`) and `<meta name="Description">` (an auto-generated synopsis of at most 250 characters).
  - The breadcrumb is static HTML in `div.i-breadcrumbs-container`.
- **Index:** `webindex.html` is a flat list of `<a target="i-content" href="x.html">Text</a><br />`. It has 118 / 43 entries, and every entry text equals the target page's `<title>`, so it is not an author-defined keyword index.
- **FTS:** `ftsindex.js` wraps the data in a function. File records look like `f["1"]=new c("gui.html","Graphical User Interface (GUI)",0);` (118 files) and word records like `s["_word"]="fileIdx:pos|pos,fileIdx:pos";` (3,627 words, including Greek letters). Regex-parseable.
- There is no glossary, synonym list or CSH map.

### 3.4 IdEM

- **TOC:** the accordion menu is exploded into 24 static menu-state pages (`IdEM/menu/indice_menu.htm` and the `menu_*.htm` files), among 28 files in `IdEM/menu/`. Each page shows one expansion state as `<ul id="menu_sezione">` / `<ul id="menu_interno">` / `<ul id="menu_corrente">` with `<li><a href="../idem/x.htm">`. The full tree is the union of all menu pages: 98 distinct topic targets, 1 missing.
- Each topic announces its menu position: 108 pages contain `<body ... onload="window.top.aggiorna_menu('../menu/menu_3_2_2.htm#3');">`.
- There is no index, search, glossary or CSH map.

### 3.5 Sphinx (`Python/`)

- **`objects.inv`:** zlib-compressed after 4 header lines. It holds 764 entries: py:module 21, py:class 86, py:property 263, py:method 340, py:function 36, std:label 10, std:doc 8. Entry format: `name domain:role prio uri dispname`.
- **`searchindex.js`:** `Search.setIndex({docnames:[...],envversion:{...},filenames:["main.rst","source\\cst.rst",...],objects:...})`. It is a JS object literal with unquoted keys, so it is not strict JSON.
- **`genindex.html` and `py-modindex.html`:** generated HTML (`table.indextable`).
- The toctree lives in `main.html`.

---

## 4. Topic HTML anatomy (representative pages)

### 4.1 RoboHelp topics (common frame)

- **Encoding:** `charset=utf-8` is declared in every RoboHelp topic (meta, plus the XML declaration in 3,077 files).
  - Most files are pure ASCII, with non-ASCII written as numeric entities (`&#160;`, `&#176;`). The rest are valid UTF-8; no RoboHelp file failed strict UTF-8.
  - For example, 3D has 1,018 ASCII-only files and 394 with valid UTF-8 multibyte content.
- **Boilerplate before the content:**
  1. `<head>` includes the WebHelp scripts (`whmsg.js`, `whver.js`, `whutils.js`, `whproxy.js`, `whlang.js`, `whtopic.js`) and, where present, the MathJax config and loader.
  2. A `<script>` in the body runs `addTocInfo`, `AddMasterBreadcrumbs` and `document.write` to build the breadcrumb.
  3. `<script src="../ehlpdhtm.js">`.
  4. A 2-column layout `<table>` with the logos `ds_simulia.png` and `3dexp.png` (3,031 files).
- **Content then runs until** `<?rh-p style="..." ?>` (a processing instruction, 3,055 occurrences) followed by `<div id="footer">` (3,065 files). The footer is a rule, a 2-column table holding the "CST Studio Suite 2024" label and the `3ds.png` logo, and a final script (`writeIntopicBar`, `highlightSearch`).
- **Nothing in the markup delimits the content** (no `<main>` or content `<div>`): it is a run of sibling elements between the header table and `div#footer`.
- **Every topic carries two layout tables** (header and footer). Leaving those out, RoboHelp topics have 1,430 tables on 776 of 3,074 pages; many of them are figure grids.
- **Structural classes are generic, not semantic:**
  - Dialog field and button terms use `p.Tip-Note-Heading` (9,353 occurrences in 1,473 files). The most common values are "See also" (617), "Help", "Cancel" and "OK".
  - Descriptions use `p.Topic-Text-Indent` (16,367) or `p.Tip-Note-Text` (14,273).
- **There is no note or warning markup.** Notes are plain paragraphs that start with "Note:" in assorted classes, for example `<p class="Topic-Text-Indent"><span>Note:</span>`, `<h3><span>Note:</span>`, `<p class="Tip-Note-Heading">Note:</p>`.
- **Lowercase class variants coexist** with the capitalised ones: `p.topic-text-indent` (259), `p.vba-text-indent` (669) and others.

### 4.2 Theory or background page: `mP/3D/special_theory/special_theory_polarization.htm`

- XHTML, UTF-8 declared, ASCII bytes only.
- One `h1`. Body paragraphs use inline `style="font-family: Arial, sans-serif;"`.
- MathJax config inline: `inlineMath: [['$', '$'], ['\\(', '\\)']]`, then `../mathjax/es5/tex-svg.js`.
- Six display equations written as `\begin{equation} ... \end{equation}` **inside running `<p>` text**, plus 22 TeX commands (`\vec`, `\frac`, `\mathrm`).
- Figures are centred `<p><img src="../image/plane_wave_linear.png" alt="">` with empty alt. There is also one 2-column figure table with caption cells.

### 4.3 Dialog reference page: `mP/3D/common_struct/common_struct_brick.htm`

- `h1` is the page title. `h2` holds the ribbon path: an icon, a popup link "Modeling:" and "Shapes > Brick".
- **The introductory prose paragraphs are tagged `<h3>`** (5 of them).
  - Across the corpus, 736 topic pages have at least one heading element containing more than 150 characters of text: 3D 532 pages (1,132 such `h3`), PCB 89 (863 `h3`), DES 50, Filter_Designer_3D 42.
  - 404 headings are empty or whitespace-only, 208 of them in Filter_Designer_3D.
- The field list is a flat alternation of `<p class="Tip-Note-Heading">Name</p>` and `<p class="Topic-Text-Indent">...</p>`, ending with OK, Preview, Cancel, Help and See also.
- Image `alt` and `title` hold Windows paths: `alt="image\brick.gif" title="image\brick.gif"`. 209 alt attributes contain backslash paths (3D 142, EXP_HF 55, DES 12).
- The anchors `id="A1"` to `id="a10"` exist only to feed `FilePopupInit('A1')` popups (section 5).

### 4.4 VBA object reference: `mP/VBA_3D/special_vbaports/special_vbaports_planewave_object.htm`

- **No `<h1>`.** Headings are classed paragraphs:
  - `p.VBA-Heading-Object` ("PlaneWave Object") for the object;
  - `p.VBA-Heading-Category` with `<a name="Methods">` for sections;
  - `p.VBA-Heading-Method` for each method signature.
  - The signature is inline markup: `Normal ( <a href="../common_vbageneral/common_general_double.htm" id="a5">double</a> <span><i>xcomponent,</i></span> ... )`.
  - 172 of 372 VBA_3D topics and 21 of 47 VBA_DES topics have no `h1`.
- A mini table of contents is `ul > li.p-VBA-Index-Category > p > a[href="#Methods"]`.
- **Code samples are one `<p class="VBA-Text-Example">` per line**, indented with `&#160;&#160;&#160;&#160;`. There is no `<pre>` or `<code>`. `p.VBA-Text-Example` appears 7,043 times in 331 files.
- Type names (`double`, `enum`) are popup links to `common_vbageneral/*.htm` pages. Those target pages use `p.Überschrift-Popup`.

### 4.5 Python API page: `Python/source/cst.results.html`

- HTML5. `<meta charset="utf-8">`, valid UTF-8 with 191 non-ASCII bytes.
- Content in `<div class="body" role="main">`, with `div.related` (nav bars), `div.sphinxsidebar` and `div.footer` around it.
- Headings `h1` to `h3`, each with `<a class="headerlink">¶</a>`.
- API entries are `<dl class="py class|method|property|function">` with `dt.sig` / `span.sig-name` / `em.sig-param`.
- Code is `div.highlight-python` / `div.highlight-default` / `highlight-winbatch` containing `<pre>` with Pygments spans; 14 `<pre>` blocks on this page.
- `div.admonition note|warning`, plus a custom `admonition-set-up-a-demo-example-project`.
- Math (in `cst.radar.html` and `cst.asymptotic.html`): `<span class="math notranslate nohighlight">\(...\)</span>`.
- Links from Sphinx pages back into RoboHelp pages: 10 in total, all in `cst.results.html` (for example `../../mergedProjects/DES/analysis/simulation/simulation_task_overview.htm#Simulation_Project`).

### 4.6 FEST3D page: `FEST3D/emce.html`

- HTML5 doctype with a UTF-8 BOM. Charset declared inside a DXMETADATA comment: `<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">`.
- The title appears three times: in `<title>`, in `meta name="Title"` and in `div.i-page-title-text`.
- Content is `<div id="i-body-content">` wrapping `<!--DXMETADATA start type="TopicSection" name="BodyText"--> ... <!--DXMETADATA end-->`. A "See Also" scrap and `div#i-footer-content` (copyright) follow it.
- **There are several `<h1>` per page**: 96 of 118 FEST3D topics and 22 of 43 SPARK3D topics have more than one. Anchors are written `<h2><a id="X" name="X"></a>Text</h2>`.
- **Retired content survives inside HTML comments.** The page contains a commented-out block of old markup in which some lines start with LaTeX-style `%` (`%Using automatic <a href=...>`). Commented-out content of more than 80 characters, excluding DXMETADATA comments, appears in 12 FEST3D topics, 10 DES, 9 3D and a few others.
- FEST3D renders math as CSS `div` grids: in `FEST3D/step.html` a matrix is `<div class="matrixtable"><div class="vector"><div>cos [α]</div>...`.

### 4.7 IdEM page: `IdEM/idem/model_options.htm`

- HTML 4.0 Frameset doctype. **No charset declaration** in any of the 138 IdEM HTML files. 136 are pure ASCII, `dataops_Mixed_Mode_Conversion.htm` is UTF-8, and `idemmp_fitting_xml.htm` contains cp1252 bytes (curly quotes 0x91/0x92).
- Layout: `<div id="header"><div id="banner4"></div></div><div id="corpo">` content `</div>`.
- Clean `h1` / `h2` / `h3` hierarchy, `<ul><li><strong>Term:</strong> ...`, bare `<img src="../Idem_image/x.png">` with no alt.
- Code: `<pre><span class="code">...</span></pre>` (15 pages have `<pre>`), plus `span.code` inline (998 occurrences in 41 files).
- Tables use `table.large` / `table.short`, with no row or column spans.

### 4.8 Additional anatomy: `sax_basic/ww_*.htm` (WinWrap Basic reference, 315 pages)

- Numeric filenames; content as `<br />`-separated lines with `<b>Syntax:</b>`, `<b>Group:</b>` and similar labels.
- Code examples are prose lines in which keywords are hyperlinks and some `<br />` elements sit inside `<a>` (`<a href="ww_00062.htm"><br />Debug</a>`).
- Import residue: in `ww_00050.htm` the interval codes are `<br />`-separated lines (code letter followed by a word), except one entry rendered as a lone `ul > li.kadov-p` holding only "Quarter", with no code letter.

### 4.9 Tables (all topics)

- Nesting is rare: 5 pages have nested tables, for example `mP/DES/components/block/import/capacitancematrixblock.htm` and `SPARK3D/Command-line interface.html`.
- `rowspan` appears on 11 topic pages, for example `mP/DES/idem_studio/user_interface/ribbon_home.htm` and `mP/3D/common_preloadedmacro/common_preloadedmacro_0d_evaluate_field_in_arbitrary_coordinates_(0d_1d_2d_3d).htm`.
- `colspan` appears on 90 pages, 69 of them in Filter_Designer_3D.
- Maximum table depth is 2.

---

## 5. Hidden and interactive content

| Mechanism | Where / count | Is the text in the HTML? |
|---|---|---|
| RoboHelp drop-down / expanding text (`dropspot`, `expandspot`, `droptext`, `rh-dropdown`, twisties) | **0 instances.** `class="expandtext"` appears in 9 files (for example `license/specifylicense.htm`, `general/job_control_center.htm`), but only as span styling with no toggle. `li.kadov-p` in 24 `sax_basic` files is a class name only. | n/a |
| RoboHelp link popups: `FilePopupInit('aN')` after an ordinary `<a href="x.htm" id="aN">` | 394 files, 1,449 anchors (VBA type links, ribbon and "expression" links) | The popup shows **the linked topic**. The text is in the target file, not on the page. |
| RoboHelp `BSSCPopup`: `href="javascript:void(0);"` with `onclick="BSSCPopup('../common_ribbons/3d/common_ribbons_simulation_hf.htm')"` | 11 links in 7 files (for example `mP/3D/special_solvopt/special_solvopt_cht_time_step_settings.htm`, `mP/EXP_MP/examplesoverview/mechanical/spring.htm`) | Target is in a separate file. The URL exists **only in the JS attribute**. |
| `ehlpdhtm.js` (RoboHelp DHTML effects library) | Referenced by 3,075 topics as `../ehlpdhtm.js` and similar; **none of those references resolve**. The file exists only at `analysis/`, `mP/3D/common_modi/`, `mP/DES/analysis/`, `mP/EXP_LF/examplesoverview/`, `mP/EXP_MP/examplesoverview/`, `mP/EXP_PD/examplesoverview/` and `mP/VBA_3D/special_vbaobjects/`. | n/a |
| Netscape-only tooltips: `onmouseover="... ehlp_showtip(this,event,'text')"` with `<div class='WebHelpPopupMenu'>` written by `document.write` | 54 files, 148 handlers (for example `mP/3D/common_modi/common_modi_localfaceconstraints.htm`) | The tooltip text duplicates the link text. |
| JS-generated content: breadcrumb (`document.write`), in-topic nav bar (`writeIntopicBar`) | All RoboHelp topics (`document.write` appears in 3,570 HTML files) | The breadcrumb text exists only inside `<script>` strings. |
| Innovasys collapsible sections (`div.i-section-heading` + `div.i-section-content`) | FEST3D 75 files (mostly the "See Also" block, `div.i-see-also-link` 255×), SPARK3D 2 files (12×, with `span.i-hidden`) | Yes, present in the HTML. |
| Innovasys "Collapse All / Expand All" labels | All 161 Innovasys topics | Boilerplate text in the HTML. |
| Innovasys conditional build flags: `<span class="hs-buildflag-markup" data-build-flags="<GUID>">` | SPARK3D 46 occurrences in 17 files; FEST3D 3 | Yes, the text is present but tagged. |
| iframes / frames | Only in shells: `FEST3D/webframe*.html`, `webnav.html` (`i-toc`, `i-index`, `i-search`), the RoboHelp `whgdhtml.htm` family, `IdEM/index.htm`, `IdEM/idem/index_idem_des.htm` (frameset) | No topic body is loaded through an iframe. |
| Video | No `<video>` or embeds. `general/getting_started_videos.htm` links to `../../Videos/.../*.html`, which is outside the corpus. | n/a |

---

## 6. Equations

### 6.1 MathJax pages (TeX notation; no MathML anywhere: 0 `<math>` elements)

- **175 pages load MathJax 3.2.0:**
  - by module: 3D 141, DES 18, VBA_3D 6, PCB 3, Python 3, EXP_HF 2, EXP_MP 1, Filter_Designer_3D 1;
  - by loader: `tex-svg.js` in 102 pages, `tex-svg-full.js` in 70, `tex-chtml-full.js` in the 3 Sphinx pages.
- Each RoboHelp module loads its own copy through a relative path, for example `../../../../../mathjax/es5/tex-svg-full.js` from deep DES pages, which resolves to `mP/DES/mathjax/`. All loader paths resolve.
- **Configuration:**
  - 172 RoboHelp pages enable **single-dollar inline math**: `inlineMath: [['$', '$'], ['\\(', '\\)']]`.
  - About 21 add `tags: 'ams'`.
- **Notation actually used** in the 172 RoboHelp MathJax pages (counted outside `<script>`):
  - `\begin{env}...\end{env}`: 466 blocks in 124 pages. Environments: equation 372, align* 58, array 53, align 24, bmatrix 8, equation* 8, cases 5.
  - `$...$` inline: about 1,420 occurrences in 123 pages.
  - `$$...$$`: about 200 in 38 pages (particle and PIC pages, for example `mP/3D/special_overview/special_overview_tracking_solver_overview.htm`).
  - `\(...\)`: 28 occurrences in 3 pages.
  - `\[...\]`: 1 page (`mP/DES/userinterface/xyplot/curveselection.htm`).
- **TeX source sits inside ordinary `<p>` and `<span>` text**, with HTML entities inside the TeX: 78 environment blocks and 34 `$$` blocks contain `&amp;`, `&lt;` and similar.
- **The `$` delimiter mis-pairs** on at least two pages (found by a regex scan):
  - `mP/3D/cbls/meshing_modeling/impedance_calculator.htm` has a `$` pair that spans across `</p><p>`;
  - `mP/3D/special_overview/special_overview_plane_wave_overview.htm` pairs `$` signs from a path or VBA string.
- 5 MathJax pages contain no detected TeX, for example `mP/DES/analysis/simulation/tasks/interference/blocks/lowpassmask.htm`.
- **Literal `$` outside MathJax pages** is common in VBA and WinWrap text (`Left$`): 57 `sax_basic` pages, 13 VBA_3D pages, and a few FEST3D pages. The `$$...$$` strings in FEST3D and SPARK3D are Innovasys placeholders (`$$VIEW_WITH_NAVIGATION_TOOLS_TIP$$`), not math.
- No TeX commands appear in any page that does not load MathJax.

### 6.2 Equations as images (heuristic; lower bound)

- **Equation image files: 41** (heuristic: names matching formula, formel, equation or corrformular, plus the Filter Designer theory SVGs; images of 32 px or less are counted as icons instead).
  - `mP/DES/theory/pictures/formula1.png` to `formula14.png` (about 200–400 × 33–76 px, 0.8–2.4 KB), used in `mP/DES/theory/power_definitions_for_combine_results.htm`. They appear inside `<p>` and table cells, sometimes indented with runs of `&#160;`.
  - `mP/EXP_LF/formula1.jpg`, `formula2.jpg`, `mP/EXP_LF/image/sphere_cap_formula.png`, `mP/EXP_LF/examplesoverview/tutorials/low_frequency-dateien/formel_lf_*.png` (inline symbols of 10–40 px).
  - `mP/VBA_DES/image/corrformular001.png`, `002.png`.
  - `IdEM/Idem_image/mp_formula_1.png`, `mp_formula_2.png`.
  - `image/db10equation.png`, `db20equation.png` (used by `userinterface/overview/units.htm`).
- **Filter Designer theory equations are SVG files:** `mP/Filter_Designer_3D/theory/*.svg` (15 files, Inkscape 0.91, glyphs drawn as paths with no `<text>` element in any of them).
  - Their `<img>` tags carry a plain-text formula in `alt`, for example `alt="ReturnLoss=1-Ripple"` in `theory/equiripple.htm` and `alt="f0=sqrt(f1*f2)"` in `theory/normalized_frequency.htm`.
- **Context hits:** images followed by "where" or preceded by phrases like "is defined as" or "is given by" were found in 46 pages, 64 page/image pairs, many of them false positives. Equation-like examples:
  - `mP/DES/analysis/simulation/tasks/ac_simulation_task_results.htm` (`../../../image/balance.png`);
  - `mP/DES/analysis/simulation/tasks/s-parameter_simulation_task_results.htm` (`sparabalance.png`);
  - `mP/PCB/pcbs/5_simulating_a_pcb/eda_decap_tool.htm` (`decap_tool_metric_m.png`);
  - `mP/DES/components/block/common/rectangularwaveguide.htm` (`kzmn.gif` inline);
  - `mP/DES/analysis/simulation/tasks/transienttask/fourier_series_approximation.htm` (Word-export `fromtd2fd_files/image014.png` etc., inline).
- **Estimate:** a few dozen pages use equation images. That is roughly 40–100 images, against 175 MathJax pages.
- **Python:** `span.math` with `\(...\)` (28 spans in 3 pages).

---

## 7. Images

- **Counts:** 6,980 image files: png 5,247 (162.5 MB), gif 1,084 (12.8 MB), jpg 536 (15.6 MB), ico 48, svg 44 (72.8 MB), bmp 21 (7.8 MB). There are no webp, tif, emf or wmf files.
- **Byte sizes:**
  - quantiles: p10 572 B, p50 10.6 KB, p90 63.7 KB, p99 315 KB; maximum 65.9 MB (the unreferenced SVG);
  - buckets: under 1 KB 1,422; 1–10 KB 1,994; 10–100 KB 3,227; 100 KB–1 MB 327; over 1 MB 10.
- **Pixel size (largest dimension; 6,911 images with readable headers):**

  | Largest dimension | Images |
  |---|---:|
  | ≤ 16 px | 880 |
  | 17–32 px | 248 |
  | 33–100 px | 321 |
  | 101–400 px | 2,245 |
  | 401–1000 px | 2,654 |
  | over 1000 px | 563 |

- **Kinds (heuristic, by path, name and size):**
  - 3,809 large rasters of 300 px or more: screenshots of dialogs, plots, 3D views (178.7 MB);
  - 1,384 mid-size images of 33–299 px (13.1 MB);
  - 778 icons, of 32 px or less or under `icon_images/` (`icon_images/de/`, `icon_images/des/`, `mP/*/icon_images/<area>/*_16.png`);
  - 713 WebHelp/Innovasys/Sphinx chrome images;
  - 185 Word-export `imageNNN` images;
  - 70 logo copies;
  - 41 equation images (section 6.2);
  - 7 animated GIFs, for example `mP/EXP_HF/image/mri_animated.gif` (3.5 MB) and `mP/DES/analysis/simulation/tasks/machinetask/hover.gif`.
- **References:**
  - 17,308 `<img>` tags in topic pages. 9,114 of them are the three per-page logos (`ds_simulia.png` 3,030, `3dexp.png` 3,030, `3ds.png` 3,054), which leaves about 8,200 content image references.
  - Alt text is almost always missing: empty in 16,445, absent in 476, and present in only 387 (many of those are Windows paths, see 4.3).
  - 1,393 images sit inside paragraphs that also contain text; 1,290 of those are icons of 32 px or less.
  - 932 image files are never referenced by any topic `<img>`: largely skin GIFs in every module, plus 61 in FEST3D.
- **Duplicates (MD5):**
  - Across all images: 5,811 unique hashes; 1,169 redundant copies (17%), dominated by WebHelp skin and logo files copied into 16 projects.
  - Content images only: 6,146 files, 5,730 unique, 416 redundant copies (7%). 188 hash groups span more than one subtree (for example ribbon screenshots shared between `ribbons/`, `mP/3D/common_ribbons/` and `mP/DES/ribbons/`).
- **Filename quirks:** `.PNG` versus `.png` case drift in FEST3D, and double extensions such as `mP/DES/analysis/simulation/tasks/interference/image/inttask_components_importtx_result_inputpowerdensity_txchnarrowband.png.png`.

---

## 8. Links

Scope: hrefs and srcs in the 3,354 topic pages, excluding `<script>` and `<link>` tags.

| Kind | Count |
|---|---:|
| internal (relative) | 53,479 (36,169 `<a>`, 17,308 `<img>`, 2 `<frame>`) |
| fragment-only `#x` | 4,833 |
| http(s) | 6,134 |
| `javascript:` | 11 (all `javascript:void(0);` + `BSSCPopup`) |
| empty `href=""` | 16 |
| `ms-its:`, `mk:@MSITStore`, `.chm`, `mailto:` | 0 |

- **Patterns:**
  - 33,937 internal links use `../`.
  - 6,371 internal links carry a fragment.
  - No topic link is percent-encoded.
  - 339 links contain a literal space. These are FEST3D/SPARK3D filenames such as `href="frequency specs.html"` and `SPARK3D/Visualizing a model Regions, signals and materials.html`.
  - Topic hrefs contain **no backslashes** outside HTML comments. Backslashes occur in navigation data (TOC items, browse sequences, `whdata/*.htm`, `whgdata/whlstf*.htm`) and in commented-out markup (`mP/3D/special_overview/special_overview_whichsolver.htm`).
- **Target types:** .htm 33,989, .png 16,281, .html 2,130, .gif 528, .jpg 452, .svg 45, .bmp 28, downloads (.zip 9, .ffs 7, .txt 4, .nfd 1).
- **Resolution:**
  - **8 internal targets fail case-insensitively** (5 distinct). Examples: `+Selected_Segments` in `mP/3D/cbls/creating_harness/export_to_mws.htm`, `Open-Ended_Nodes` in `mP/PCB/pcbs/3_checking_a_pcb/layout_check.htm` (fragments missing their `#`), and `../../general/printed_documentation.htm` from `mP/3D/special_dslink/ds_link.htm`, which resolves to a non-existent `mergedProjects/general/`.
  - **152 fail case-sensitively** but resolve case-insensitively:
    - VBA_DES 62 (`../common_VBAGeneral/...` versus `common_vbageneral/`);
    - FEST3D 36 image links (`.PNG` / `.png`, `rectcavityCST` / `rectcavitycst`);
    - 3D 18, PCB 11, VBA_3D 9, DES 5, EXP_HF 5, IdEM 3, EXP_CBL 2, SPARK3D 1.
  - 18 links leave `Online Help/`:
    - 12 to `../Documentation/*.pdf`: 9 from `general/printed_documentation.htm` and 3 from `mP/EXP_PD/...`;
    - 2 to `../Licenses/Legal Notices.htm`, from `FEST3D/` and `SPARK3D/`. The root TOC and the IdEM menu link there as well.
    - 4 to `../Videos/...`, from `general/getting_started_videos.htm` and similar.

    The `Licenses/` and `Videos/` folders are not in the corpus.
  - **Fragments:** 6,265 resolve to an `id` or `name` in the target, 84 are missing (mostly FEST3D, for example `FEST3D/2d_iris.html#Errors`), 6 match only case-insensitively, and 16 point at a page whose path matches only case-insensitively.
  - Script srcs: the `ehlpdhtm.js` references fail 3,075 times (section 5).
- **Cross-project `<a>` links (top):**

  | From → to | Links |
  |---|---:|
  | VBA_DES → VBA_3D | 55 |
  | 3D → `userinterface` | 32 |
  | VBA_DES → DES | 32 |
  | 3D → `simulation_acceleration` | 30 |
  | DES → `userinterface` | 30 |
  | EXP_HF → `general` | 29 |
  | DES → 3D | 26 |
  | 3D → DES | 23 |
  | VBA_3D → 3D | 22 |

  Further notable flows:
  - DES → IdEM: 8 links, to `IdEM/idem/index_idem_des.htm` and `IdEM/index.htm`.
  - Links into FEST3D: 63 (61 from 3D). Links into SPARK3D: 68 (61 from 3D).
- **Links into the Sphinx docs:** 6 from outside (5 to `Python/source/cst.eda.html`, 1 to `Python/main.html`). There are also the TOC entry `mP/Python` → `..\..\Python\main.html` and the wrapper topic `mP/Python/python_overview.htm`.
- **Navigation data:** TOC and index URLs are project-relative and use backslashes (section 3.1). Cross-project TOC URLs climb out of the project with `..\..\`.

---

## 9. Languages

- **Only English content exists.** Nothing translated was found: no locale folders and no alternative-language pages.
- Every RoboHelp project uses `langid="1033"` (en-US).
- `de` in `icon_images/de/`, `ribbons/de/`, `mP/*/common_ribbons/de/` and `general/welcome_de.htm` is **not German**. It appears to stand for the Design Environment: the root source project is `de-online-help.hpr`, `ribbons/de/homede.htm` is titled "Home", and the main executable is `cst_design_environment` (see `advanced/commandlineoptions.htm`). `icon_images/des/` sits alongside it.
- `lang` attributes are unreliable Word/RoboHelp residue on English text: `EN-US` 31,554, `EN-GB` 696, `IT` 278, `FR` 124, `DE` 122, `de` 28, `PT-BR` 4. For example, `lang="FR"` wraps the text "Cancel interactive mode" in `mP/3D/common_modi/common_modi_3dpolygon_creation_mode.htm`.
- Non-English residue is limited to identifiers: German CSS class names (section 2.1), Italian IdEM ids and filenames (`colonna menu`, `corpo`, `indice_menu.htm`), and German Word-export folder names (`-dateien`).

---

## 10. `Documentation/` (11 PDFs, 74.8 MB)

| File | MB | Pages | Producer | Text layer | Outline (bookmarks) | Tagged | What it is |
|---|---:|---:|---|---|---|---|---|
| `CST Studio Suite - Getting Started.pdf` | 5.6 | 72 | Microsoft Word 2016 | yes | **none** | yes | Getting-started manual (installation, modeling, post-processing) |
| `CST Studio Suite - High Frequency Simulation.pdf` | 7.6 | 119 | Word 2016 | yes | none | yes | Workflow & solver overview manual |
| `CST Studio Suite - Low Frequency Simulation.pdf` | 5.7 | 97 | Word 2016 | yes | none | yes | Workflow & solver overview |
| `CST Studio Suite - Charged Particle Simulation.pdf` | 6.2 | 105 | Word 2016 | yes | none | yes | Workflow & solver overview |
| `CST Studio Suite - Thermal and Mechanical Simulation.pdf` | 4.3 | 72 | Word 2016 | yes | none | yes | Workflow & solver overview |
| `CST Studio Suite - PCB and Package Simulation.pdf` | 5.8 | 102 | Word 2016 | yes | none | yes | Workflow & solver overview |
| `CST Studio Suite - Circuit Simulation and SAM (System Assembly and Modeling).pdf` | 5.0 | 89 | Word 2016 | yes | none | yes | Introduction / workflow manual |
| `CST Studio Suite - Cable Simulation.pdf` | 5.0 | 78 | Word 2016 | yes | none | yes | Workflow & solver overview |
| `CST Studio Suite - Release Notes.pdf` | 0.2 | 13 | Microsoft Word LTSC (2024-02-15) | yes | none | no | Service-pack release notes |
| `CST Studio Suite - FEST3D User Manual.pdf` | 23.3 | 634 | Generated by HelpStudio | yes | 128 entries, depth 5 (top: Table of Contents / Fest3D Online Help / Index) | no | PDF build of the FEST3D online help (same source as `Online Help/FEST3D/`) |
| `CST Studio Suite - SPARK3D User Manual.pdf` | 6.0 | 170 | Generated by HelpStudio | yes | 45 entries, depth 5 | no | PDF build of the SPARK3D online help |
| *(also)* `Online Help/IdEM/Installation/FlexLicenseAdministration.pdf` | 2.9 | 260 | FrameMaker 12 / Acrobat Distiller 15 | yes | 277 entries, depth 4 | n/a | FlexNet Publisher 2017 License Administration Guide (third-party) |

Notes:

- **All PDFs are born-digital.** Every sampled page had extractable text; the only exception is HelpStudio cover pages, which carry 16 characters.
- **The Word manuals have no bookmark outline but are tagged PDFs** (`/StructTreeRoot`, `/MarkInfo {/Marked true}`). For example, *Getting Started* has structure elements `H1` ×7, `H2` ×32, `H3` ×30, `TOC`/`TOCI` ×71, `Table` ×27 and `Figure` ×262.
- The Word manuals have a printed table of contents on page 3, with dot leaders ("Chapter 1 – Introduction ......").
- Every page carries a running header "© Dassault Systèmes | CST Studio Suite 2024" and a page number.
- Link annotations: 55–108 per Word manual, mostly internal TOC links. 1,353 in the FEST3D PDF.
- The *Charged Particle Simulation* PDF contains stale `file:///F:/Programme/CST%20STUDIO%20SUITE%202009/Online%20Help/...` links.
- The online help links to these PDFs from `general/printed_documentation.htm` ("Getting Started Books") via `../../Documentation/<name>.pdf`.

---

## 11. Other things that would break or mislead a naive HTML-to-Markdown conversion

- **Boilerplate on every page:** the logo header table, the breadcrumb built by `document.write`, the footer table "CST Studio Suite 2024" with its logo, Innovasys "Collapse All / Expand All" labels and the copyright footer, and the Sphinx sidebar and related bars.
- **Spacer paragraphs:**
  - 24,849 empty or `&#160;`-only `<p>` in RoboHelp topics, and 1,813 in Innovasys topics;
  - indentation built from runs of `&#160;`, for example in VBA examples and equation images.
- **Processing instructions** `<?rh-p ... ?>` (3,055) and the XML declaration in front of HTML.
- **Invisible text in HTML comments:**
  - commented-out content blocks, including whole tables and `%`-prefixed lines (`FEST3D/emce.html`, `FEST3D/index7.html`);
  - DXMETADATA comments wrapped around real content. Innovasys titles, breadcrumbs and the body all sit inside DXMETADATA comment pairs, so the markers can be dropped but the content between them must be kept.
- **Duplicate topics with identical body text:** 215 topics in 45 groups (170 redundant copies). They are mainly the ribbon pages copied into several projects, for example `mP/3D/common_ribbons/3d/common_ribbons_view3d.htm`, `mP/DES/ribbons/3d/common_ribbons_view3d.htm` and `mP/EXP_HF/ribbons/3d/common_ribbons_view3d.htm`. Titles repeat too: "Home" ×24, "View" ×16.
- **Very short pages:** 9 topics under 100 characters, for example `mP/EXP_LF/errormessage/error.htm`, `FEST3D/LegalNotices.html`, `IdEM/idem/model_export_vhdl.htm`. Median body length is 1,681 characters and the largest is 99.6 K (`mP/VBA_3D/special_vbalayer/special_vbalayerolayer_object.htm`).
- **Odd filenames:**
  - spaces (32 files), parentheses (51), commas (4) and `+` (8), for example `mP/3D/common_preloadedmacro/common_preloadedmacro_0d_+_0d_value_from_1d_result.htm`;
  - a filename truncated mid-phrase: `..._(rescale_xy,_fft,_derivation,.htm`;
  - mixed-case filenames, 572 in total and mostly in FEST3D/SPARK3D. There are no case-insensitive path collisions.
- **Dialog and VBA semantics expressed only through CSS classes** (`Tip-Note-Heading`, `VBA-Heading-Method`, `VBA-Text-Example`) and through `<h3>` used for prose (section 4).
- **`sax_basic` code inside running text**, with hyperlinked keywords and `<br />` inside `<a>` (section 4.8).
- **Word-export artifacts:** `MsoNormal` classes, `-dateien` and `_files` image folders, and alt or title attributes holding Windows paths.
- **Inconsistent encodings:**
  - RoboHelp and Sphinx files are UTF-8 or ASCII, with the RoboHelp ones declaring it;
  - Innovasys files are UTF-8 with a BOM;
  - IdEM files declare nothing, and one contains cp1252 bytes;
  - the Zoom search data is windows-1252.
- **Navigation data held as JS string literals** (`gXMLBuffer = "..."`) and JS function calls (`aTE(...)`, `f["n"]=new c(...)`). It is parseable without execution, but only after decoding JS string escapes.
- **Popup and JS-only links:** `FilePopupInit`, and `BSSCPopup` URLs found only in `onclick` attributes.

---

## Hazards for ingestion

1. **Three HTML generators plus Sphinx and hand-written IdEM**, each with its own content container: RoboHelp (between the logo `<table>` and `div#footer`), Innovasys (`div#i-body-content` inside DXMETADATA comments), IdEM (`div#corpo`) and Sphinx (`div.body[role=main]`).
2. **TOC coverage is about 40%.** 2,011 of 3,354 topics are not in any TOC. The seven `EXP_*` example projects are not wired into the root project at all, and three of them have no inbound links.
3. **Index, glossary and synonyms are thin.**
   - Glossaries and synonym files are empty everywhere.
   - The Innovasys "index" is just the list of page titles.
   - CSH maps cover only 34 ids, in the root and DES.
4. **Navigation metadata is not plain JSON or XML on disk.** It is XML inside JS strings, with backslash, project-relative and mixed-case paths. Browse sequences are stale against the lowercase output filenames.
5. **Case sensitivity.** 152 links and many TOC and browse-sequence entries only resolve on a case-insensitive filesystem.
6. **Math is TeX embedded in ordinary text** under a MathJax config that enables the `$` delimiter. The TeX contains HTML entities, and `$` also appears as literal VBA and path text. Separately, about 41 images are equations, 15 of them path-only SVGs; the Filter Designer SVGs at least carry a plain-text alt.
7. **Images have almost no alt text.** 17,308 image references; 9,114 of them are logo boilerplate, and 209 alt attributes contain Windows file paths.
8. **Heading semantics are unreliable:**
   - `<h3>` is used for prose (about 2,000 `h3` elements of more than 150 characters in 3D and PCB alone);
   - many topics have several `<h1>` (96 of 118 FEST3D topics);
   - 404 headings are empty;
   - VBA pages have no `<h1>` and mark headings through `p.VBA-Heading-*` classes.
9. **Code is rarely in `<pre>`.** VBA examples are one `<p>` per line with `&#160;` indentation, and WinWrap Basic code has hyperlinked keywords.
10. **Content that is not visible, or not for this page:** commented-out blocks in 38 topics, Innovasys build-flag spans, popup links whose text belongs to other files, and breadcrumbs that exist only inside `document.write` strings.
11. **Duplicate content:** 170 redundant topic copies (mainly the ribbon pages) and 416 redundant content images. The FEST3D and SPARK3D PDFs are separate builds of the same HelpStudio content as their HTML.
12. **Encodings vary by subtree:** BOMs in Innovasys files, undeclared encoding and stray cp1252 in IdEM, and windows-1252 Zoom data.
13. **Links point outside the corpus** (`../Licenses/`, `../Videos/`) and to absolute `file:///F:/...` URLs (in a PDF). `ehlpdhtm.js` is missing at all 3,075 referenced locations.
14. **Size outliers:** a 65.9 MB unreferenced SVG, 16 copies of MathJax (about 198 MB), and per-module WebHelp runtimes. A scan that does not exclude non-content files will spend most of its effort on them.
15. **The Word PDFs have no bookmark outline**, so chapter structure must come from tags (`H1` to `H3`) or the printed TOC. Running headers and footers repeat on every page.
