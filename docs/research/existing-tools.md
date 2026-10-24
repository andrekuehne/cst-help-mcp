# Existing tools we could reuse — research notes

Status: research input for design decisions. Verified 2026-10-24 against primary sources (official repos, PyPI metadata, Hugging Face model cards, vendor docs). Version numbers and dates come from the PyPI JSON API (`https://pypi.org/pypi/<name>/json`), GitHub releases, or the Hugging Face model API, unless stated otherwise. Some claims were also checked locally against the CST 2024 help sample in `.ingestion/2024/` and the Python interpreters installed on this machine; those checks are marked **(local check)**. Items that could not be verified are marked **Unverified**.

Benchmark numbers are mostly reported by the vendor of one of the tools being compared. Treat them as indications, not as evidence that a tool works on CST documents.

---

## Summary

| Responsibility | Top candidates | Verdict |
| --- | --- | --- |
| Whole "docs → local MCP" system | [haiku.rag](https://github.com/ggozad/haiku.rag), [arabold/docs-mcp-server](https://github.com/arabold/docs-mcp-server), [tobi/qmd](https://github.com/tobi/qmd) | **None fits as-is.** None reads RoboHelp metadata, routes exact identifiers, keeps MathJax TeX, and returns images together. Borrow their designs: FTS5 schema with RRF, tool shapes, image blocks. haiku.rag comes closest for PDFs. |
| CST-specific prior art | [MuziIsabel/CST-Studio-Suite-Help](https://github.com/MuziIsabel/CST-Studio-Suite-Help) | **Read it closely.** It covers the same corpus (RoboHelp, Sphinx, FEST3D/SPARK3D/IdEM), uses SQLite FTS5, a skill and a CLI, and is MIT-licensed. It handles text only: no PDFs, images or equations, and no use of whxdata. It was written in one day. Borrow ideas from it; don't depend on it. |
| RoboHelp WebHelp TOC, index and glossary | None. Write a custom parser with `lxml`. | No library exists for classic WebHelp. The data is XML inside `gXMLBuffer="…"` JS strings, so a small parser will do. |
| Sphinx API reference | stdlib `zlib`, or [sphobjinv](https://pypi.org/project/sphobjinv/) 2.4 | `objects.inv` lists 764 exact API targets with anchors. Its `searchindex.js` is not JSON. sphinx-markdown-builder can't be used because no sources ship. |
| HTML → Markdown | [markdownify](https://pypi.org/project/markdownify/) 1.2.3, [pandoc](https://github.com/jgm/pandoc) 3.12.1, [html-to-markdown](https://pypi.org/project/html-to-markdown/) 3.18.6 | Use markdownify with custom converters for control. Use pandoc for MathJax pages, because it reads `$…$` and `\(…\)` from HTML. Avoid html2text (GPL-3.0) and trafilatura, which removes boilerplate by heuristics. |
| PDF → structured Markdown | [Docling](https://github.com/docling-project/docling) 2.142.1, [MinerU](https://github.com/opendatalab/MinerU) 4.0.12, [Marker](https://github.com/datalab-to/marker) 2.0.0 | **Docling:** MIT/Apache/CDLA, runs on Windows, keeps provenance, formula enrichment. **MinerU 4:** top OmniDocBench scores, with a CPU + Vulkan path. **Marker:** fast on CPU, but its weights are under OpenRAIL-M. Run a bake-off on the real PDFs. |
| Equation image → LaTeX | [PP-FormulaNet_plus](https://huggingface.co/PaddlePaddle/PP-FormulaNet_plus-L) (Apache-2.0), [Pix2Text MFR 1.5](https://huggingface.co/breezedeus/pix2text-mfr-1.5) (MIT), small doc VLMs (PaddleOCR-VL-1.6, GLM-OCR) | 175 HTML topics already carry TeX through MathJax **(local check)**, so OCR is needed only for equation images. Benchmark on CST GIFs. |
| Lexical / exact search | stdlib `sqlite3` FTS5 (unicode61 + trigram), plus our own symbol table | FTS5 and trigram both work in python.org CPython 3.12 and 3.13 on Windows **(local check)**. tantivy and bm25s aren't needed at first. |
| Hybrid search later | [sqlite-vec](https://github.com/asg017/sqlite-vec) 0.1.9, [LanceDB](https://github.com/lancedb/lancedb) 0.40.0 | sqlite-vec keeps everything in one DB file but is pre-v1. LanceDB brings its own FTS and vectors. |
| MCP server | Official [`mcp`](https://pypi.org/project/mcp/) 2.3.0 (`MCPServer`, `Image`); [FastMCP](https://pypi.org/project/fastmcp/) 4.1.3 | The official SDK is enough. Claude Code, Codex and Cursor all document or test passing MCP images to the model. |
| Plain-files alternative | Markdown tree + `llms.txt`-style index + Agent Skill with a search CLI | A strong baseline. MCP adds ranked exact lookup in one call, bounded output, and one image/provenance contract across clients. Serve both from one index. |

### Most decision-relevant findings

1. **Closest prior art.** [MuziIsabel/CST-Studio-Suite-Help](https://github.com/MuziIsabel/CST-Studio-Suite-Help) is an MIT Agent Skill that already indexes a local CST help install into SQLite FTS5. It covers RoboHelp WebHelp, Sphinx Python docs and FEST3D/SPARK3D/IdEM, and adds a VBA symbol sidecar for exact-method boosts ([reference.md](https://github.com/MuziIsabel/CST-Studio-Suite-Help/blob/main/reference.md)). It is text-only: no images, equations, PDFs or whxdata metadata. All six commits are from 2026-06-23. It replaces maybe the first 20% of our plan, as a reference design.
2. **No tool replaces the whole build.** The pieces that are hard and specific to CST all have to be written: classic RoboHelp metadata, MathJax TeX preservation, exact API routing, and image delivery with provenance. Expensive PDF conversion, on the other hand, can be delegated entirely to Docling, MinerU or Marker.
3. **Images reach the model in all three clients.**
   - Claude Code: inline PNG/JPEG/GIF/WebP ([docs](https://code.claude.com/docs/en/mcp)).
   - Codex: forwards MCP `image` content as `input_image` ([test](https://github.com/openai/codex/blob/main/codex-rs/core/tests/suite/rmcp_client.rs)).
   - Cursor: "attaches returned images … If the model supports images, it analyzes them" ([docs](https://cursor.com/docs/mcp)).
   - Claude Code and Codex can also view image files on disk without MCP ([Read tool](https://code.claude.com/docs/en/tools-reference), [`view_image`](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/view_image_spec.rs)).
4. **The best PDF and formula accuracy now comes from small document VLMs** (0.8–1.2B) with Apache-2.0 or MIT weights: PaddleOCR-VL-1.6, MinerU2.5-Pro, GLM-OCR, TeleOCR, OvisOCR2. On OmniDocBench v1.6 they match or beat Gemini 3 Pro on formulas and clearly beat GPT-5.2 ([OmniDocBench](https://github.com/opendatalab/OmniDocBench)).
5. **On the AMD laptop, PyTorch runs on CPU only.** ROCm-on-Windows PyTorch supports neither the RX 6550M nor the 780M ([AMD matrix](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html)). The practical GPU route there is llama.cpp with Vulkan, which MinerU 4 uses by default ([MinerU](https://github.com/opendatalab/MinerU)). The NVIDIA machine opens vLLM-based tools: olmOCR, dots, DeepSeek-OCR, PaddleOCR-VL with vLLM.
6. **License traps.**
   - Copyleft code: PyMuPDF / PyMuPDF4LLM (AGPL-3.0, and Pix2Text depends on PyMuPDF), html2text (GPL-3.0), basic-memory (AGPL-3.0).
   - Restricted weights: Marker, Surya and Chandra (modified OpenRAIL-M with revenue caps), Nougat (CC-BY-NC-4.0), MinerU2.5-2509 (AGPL-3.0; the newer MinerU2.5-Pro is Apache-2.0), HunyuanOCR (custom license).
7. **Python MCP SDK v2 renamed `FastMCP` to `MCPServer`** (2026-07-28), and the import path moved to `mcp.server.mcpserver`. Code samples written for v1 need adjusting ([what's new](https://py.sdk.modelcontextprotocol.io/whats-new/)).

---

## 1. End-to-end "docs → MCP" and local docs search servers

### arabold/docs-mcp-server ("Grounded Docs MCP Server")

- **What it does:** Indexes websites, GitHub repos, npm/PyPI packages, local folders and ZIP/TAR archives. It serves search over MCP, a CLI and a web UI, and calls itself an open-source alternative to Context7, Nia and Ref ([repo](https://github.com/arabold/docs-mcp-server)).
- **License:** MIT ([repo](https://github.com/arabold/docs-mcp-server)).
- **Latest release:** v3.3.0 on 18 Oct; v3.2.1 was 2026-09-27 ([releases](https://github.com/arabold/docs-mcp-server/releases)). `package.json` says 3.3.0 ([package.json](https://github.com/arabold/docs-mcp-server/blob/main/package.json)).
- **Maintenance:** About 1.8k stars, last pushed 2026-10-24.
- **Search:**
  - SQLite FTS5 using "the Porter stemmer over the `unicode61` tokenizer" ([data-storage.md](https://github.com/arabold/docs-mcp-server/blob/main/docs/concepts/data-storage.md)).
  - "Without vector search, BM25 ranks the full-text matches alone." With vectors enabled (sqlite-vec), it fuses FTS and kNN rankings with Reciprocal Rank Fusion (same page).
  - Embeddings come from OpenAI, Ollama, Gemini and others. "Without an embedding model, search uses full-text matching" ([repo](https://github.com/arabold/docs-mcp-server)).
- **Local folders:** Supported through `file://` URLs. By default the server reads only the Documents folder until you add allowed roots ([basic-usage.md](https://github.com/arabold/docs-mcp-server/blob/main/docs/guides/basic-usage.md)).
- **PDFs:** Office files and PDFs go through Xberg ([content-processing.md](https://github.com/arabold/docs-mcp-server/blob/main/docs/concepts/content-processing.md)).
- **MCP tools:** `search_docs`, `list_libraries`, `fetch_url` and `scrape_docs`, plus `read_page`, `list_pages`, `find_version`, `refresh_version`, `remove_docs` and job tools ([mcp-clients.md](https://github.com/arabold/docs-mcp-server/blob/main/docs/guides/mcp-clients.md)). It runs over stdio or Streamable HTTP.
- **Telemetry:** "Usage telemetry is on by default" ([README](https://github.com/arabold/docs-mcp-server)).
- **Windows/CPU:** Needs Node.js 22+ or Docker ([README](https://github.com/arabold/docs-mcp-server)). Windows is not mentioned. **Unverified.**
- **Fit:** Good, as a ready-made search and MCP layer over a Markdown tree we generate. It has offline BM25 and optional local hybrid search through Ollama.
- **Gaps:**
  - No image results are documented.
  - Porter/unicode61 tokenization gives no exact-identifier path.
  - It knows nothing about RoboHelp TOC or index metadata, or about collection replacement per CST release.
  - It is Node-based, and telemetry has to be disabled.

### tobi/qmd

- **What it does:** "An on-device search engine" for Markdown notes and docs ([repo](https://github.com/tobi/qmd)). It offers three modes:
  - `search`: BM25 through SQLite FTS5.
  - `vsearch`: vector search.
  - `query`: hybrid, with query expansion, RRF and an LLM reranker.
  
  The models are GGUF files run through node-llama-cpp: embeddinggemma-300M, qwen3-reranker-0.6b, and a 1.7B query-expansion model. `QMD_LLAMA_GPU` accepts `vulkan` ([README](https://github.com/tobi/qmd/blob/main/README.md)).
- **License:** MIT.
- **Latest release:** v2.8.3, 2026-08-16 ([releases](https://github.com/tobi/qmd/releases)). The repo was last pushed 2026-10-15 and has about 30.6k stars.
- **MCP:** Tools `query`, `get`, `multi_get`, `status` and `metadata`, over stdio or HTTP. Provenance comes as docids and `path:line` ([README](https://github.com/tobi/qmd/blob/main/README.md)).
- **Tokenization:** porter unicode61. The changelog records a fix so that "quoted FTS phrases containing dotted tokens (e.g. `"1.0.21"`)" match ([CHANGELOG](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)). That is a reminder that punctuation-heavy identifiers need deliberate handling.
- **Windows:** Many open Windows issues, for example "Executing any qmd command on Windows fails", "npm bin scripts fail without Git Bash/WSL" and "Vector Search Hangs on Windows" ([issues](https://github.com/tobi/qmd/issues?q=is%3Aissue+windows)).
- **Fit:** Indexes Markdown only (default glob `**/*.md`), so it could serve our generated tree. It is fully local, with BM25, hybrid and reranking.
- **Gaps:** No image content. Node 22 or Bun. Shaky on Windows. No structured provenance beyond path and line.

### ggozad/haiku.rag

- **What it does:** "Agentic RAG" over local documents ([repo](https://github.com/ggozad/haiku.rag)).
  - **Ingestion:** Docling. "The stored DoclingDocument keeps headings, tables, pictures and page provenance."
  - **Search:** "hybrid vector and full-text retrieval", with optional reranking and an embedded LanceDB store.
  - **Models:** Ollama by default.
  - **Clients:** An MCP server (`haiku-rag mcp --stdio`) and a Claude Code plugin.
- **License:** MIT.
- **Latest release:** 0.101.0, 2026-10-23, with almost daily releases ([releases](https://github.com/ggozad/haiku.rag/releases)). It needs Python ≥3.12 and depends on `fastmcp` 4, `lancedb` and `docling-core` ([PyPI haiku.rag-slim](https://pypi.org/project/haiku.rag-slim/)).
- **MCP tools:** `search_documents` (with `include_images`), `get_document`, `get_document_outline`, `get_document_section`, `list_documents` and `execute_code`. "`search_documents` returns pictures from its results as image blocks" ([MCP docs](https://ggozad.github.io/haiku.rag/mcp/)).
- **Windows/CPU:** Docling and LanceDB ship Windows wheels; Ollama is needed for embeddings. Running haiku.rag itself on Windows is **unverified**.
- **Fit:** The best match among general tools. It has page provenance, image blocks over MCP, hybrid search, and runs locally.
- **Gaps:**
  - The docs describe search as hybrid; whether pure-FTS mode works without an embedder is **unverified**.
  - It has no RoboHelp TOC or index metadata and no MathJax TeX handling, because Docling's HTML backend has no math handling ([html_backend.py](https://github.com/docling-project/docling/blob/main/docling/backend/html_backend.py)).
  - It has no exact-identifier routing. It is fast-moving and has a large dependency surface (pydantic-ai and others).

### MinerU 4.0 document library (also listed under PDF tools)

MinerU 4.0 adds a "local document library and agent reading" mode ([README](https://github.com/opendatalab/MinerU)):

- It can "discover files, cache results, search content, continue by page or block, and preserve stable citation locators".
- It installs as an Agent Skill and CLI (`mineru search`, `mineru parse --json`), not as an MCP server.
- It has opt-out telemetry that "does not collect document contents …" ([README](https://github.com/opendatalab/MinerU)).

**Fit:** It could own the whole PDF side, including search. **Gap:** it is a separate index, so HTML help and PDFs would not share ranking.

### Hosted services (Context7, Ref, GitMCP)

None of these can run offline:

- **Context7** ([upstash/context7](https://github.com/upstash/context7), MIT, 63.6k stars) exposes `resolve-library-id` and `query-docs`. Its README states: "the supporting components — API backend, parsing engine, and crawling engine — are private and not part of this repository."
- **Ref** ([ref-tools-mcp](https://github.com/ref-tools/ref-tools-mcp), MIT client) needs an API key against `api.ref.tools`. Private PDFs and repos are uploaded to the service.
- **GitMCP** ([idosal/git-mcp](https://github.com/idosal/git-mcp), Apache-2.0) is "a free, open-source, remote MCP server" for GitHub repos.

### Smaller or less suitable candidates

- **[shinpr/mcp-local-rag](https://github.com/shinpr/mcp-local-rag)** (MIT, v0.23.1 2026-10-22, npx):
  - "Semantic similarity with keyword matching". Works offline after an approximately 90 MB embedding model downloads.
  - Ingests PDF, DOCX, Markdown and TXT. HTML only arrives through `ingest_data`. No image search.
  - Not the same project as the PyPI package [`mcp-local-rag`](https://pypi.org/project/mcp-local-rag/), which is AGPL-3.0 (0.4.1, 2026-07-16).
- **[basic-memory](https://github.com/basicmachines-co/basic-memory)** (AGPL-3.0, v0.24.1 2026-10-23): a Markdown knowledge base with hybrid full-text and FastEmbed vector search on SQLite. It is meant for notes the AI writes, not for vendor corpora. AGPL.
- **[markitdown-mcp](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp)** (MIT, 0.0.1a8 2026-10-21): one tool, `convert_to_markdown(uri)`. It converts but has no index ([README](https://github.com/microsoft/markitdown/blob/main/packages/markitdown-mcp/README.md)).
- **[docling-mcp](https://github.com/docling-project/docling-mcp)** (MIT, 3.3.0 2026-10-06): conversion and generation tools, with optional RAG through Milvus, LlamaIndex or LlamaStack. `DOCLING_MCP_IMAGE_EXPORT_MODE` can embed images ([README](https://github.com/docling-project/docling-mcp)).
- **[hannesrudolph/mcp-ragdocs](https://github.com/hannesrudolph/mcp-ragdocs)** (MIT, last push 2025-07-18): vector-only. It needs `OPENAI_API_KEY` and Qdrant ([README](https://github.com/hannesrudolph/mcp-ragdocs)), so it is not offline.
- **[langchain-ai/mcpdoc](https://github.com/langchain-ai/mcpdoc)**: llms.txt over MCP. The repo is **archived**.
- **[HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything)** (MIT): multimodal RAG on LightRAG and MinerU, handling images, tables and equations ([README](https://github.com/HKUDS/RAG-Anything)). It builds an LLM-derived knowledge graph, which conflicts with our "preserve originals, no LLM rewriting" rule.

---

## 2. Existing CST Studio Suite tooling

GitHub searches for "CST Studio Suite", "CST Studio MCP", "cst mcp server" and "CST Studio Suite help" turned up the projects below (`gh search repos`, 2026-10-24). PyPI name checks found `py4cst` and `pycst`. `cst-studio-mcp`, `cst-mcp`, `cst-python-api` and similar names return 404.

### MuziIsabel/CST-Studio-Suite-Help (documentation; directly relevant)

- **What it does:** An Agent Skill (`SKILL.md`) plus stdlib-only scripts. It locates `C:\Program Files (x86)\CST Studio Suite <YEAR>\Online Help`, parses RoboHelp WebHelp (`mergedProjects\*`), the Sphinx Python docs (`Online Help\Python`) and the FEST3D/SPARK3D/IdEM HTML, and builds a SQLite FTS5 index. Results carry title, `heading_path`, snippet and local path ([README](https://github.com/MuziIsabel/CST-Studio-Suite-Help), [SKILL.md](https://github.com/MuziIsabel/CST-Studio-Suite-Help/blob/main/SKILL.md)).
- **Design details worth borrowing** ([reference.md](https://github.com/MuziIsabel/CST-Studio-Suite-Help/blob/main/reference.md)):
  - Lists the CST 2023 module names: `3D, CHI, DES, EXP_*, Filter_Designer_3D, PCB, Python, VBA_3D, VBA_DES`. These match our 2024 sample **(local check)**.
  - Gets breadcrumbs from the inline `addTocInfo("…")`.
  - Chunks by h1–h3 with a maximum of 1,500 characters, using `unicode61 remove_diacritics 2`.
  - Builds a `symbols.json` sidecar of VBA method names (regex `Name(` or `Name <type> Returns`), with rank boosts of +6 when the topic contains the symbol and +5 when the chunk contains the exact name.
  - Swaps in rebuilt indexes atomically (`os.replace`).
  - It "does not index" whxdata, which "is useful for future enrichment".
- **License:** MIT.
- **Maintenance:** Created 2026-06-23. All six commits are from that day; 6 stars ([commits](https://github.com/MuziIsabel/CST-Studio-Suite-Help/commits/main)). Tested against CST 2023.
- **Windows/CPU:** Windows-first, Python 3.8+, stdlib only.
- **Gaps against our requirements:**
  - No images. Equations and MathJax are dropped.
  - No PDFs.
  - No TOC, index or glossary from whxdata.
  - No MCP server. It is a skill and CLI only.
  - Its query expansion is tuned for Chinese.
  - No Sphinx `objects.inv` use. Its own notes say Python chunks have "no `cst.*` dotted API symbols", yet the 2024 `objects.inv` lists 340 methods and 263 properties **(local check)**.

### CST automation MCP servers and plugins (not documentation tools)

These drive a running CST instance, and some embed hand-curated VBA references. None indexes the installed help.

- **[valenZW/cst-sim-agent](https://github.com/valenZW/cst-sim-agent)** (Apache-2.0, created 2026-08-25): a Claude Code plugin with an "embedded domain knowledge base (an 8-domain VBA syntax library, 158 official examples, pitfall checklists)" and hooks.
- **[bbl21/cst-runtime-cli](https://github.com/bbl21/cst-runtime-cli)** (MIT, 37 stars, pushed 2026-06-24): 113 CLI tools. Its README says `devkit/references/` holds a "complete official VBA API reference (1,890 lines)" and a "CST Python API reference (1,377 lines)" ([README](https://github.com/bbl21/cst-runtime-cli)). These appear to be copies of vendor material, which is a copyright caveat if we were to reuse them.
- **[guardianer9-debug/cst-studio-orchestrator-mcp](https://github.com/guardianer9-debug/cst-studio-orchestrator-mcp)** (AGPL-3.0): 177 tools with "built-in CST VBA reference data".
- **[woson-L/cst-studio-suite-mcp](https://github.com/woson-L/cst-studio-suite-mcp)** (MIT, created 2026-10-01): 84 tools.
- **[ismailakdag/cst-studio-mcp](https://github.com/ismailakdag/cst-studio-mcp)**: no license file, so all rights are reserved by default.
- **[cclyliuyi/mcp-cst-studio](https://github.com/cclyliuyi/mcp-cst-studio)**: AGPL-3.0.

### Python API wrappers

- **[py4cst](https://pypi.org/project/py4cst/)** 0.2.0 (2025-12-17, MIT per PyPI): "Automation/Scripting library for CST Studio Suite". Whether it is the same project as [JustArri/py4cst](https://github.com/JustArri/py4cst) (GitHub license "Other") is **unverified**.
- **[pycst](https://pypi.org/project/pycst/)** 0.0.1 (2022) / [renanmav/pycst](https://github.com/renanmav/pycst) (Apache-2.0).
- **[PlasticLie/mzcst_2024](https://github.com/PlasticLie/mzcst_2024)** (MIT).
- **[korvin011/CSTMWS-Matlab-Interface](https://github.com/korvin011/CSTMWS-Matlab-Interface)** (GPL-3.0).

None of these ships documentation we could use.

**Verdict:** Nothing existing covers images, equations, PDFs or MCP for CST documentation. The MuziIsabel skill is the useful reference design, plus evidence that the corpus layout is stable from 2023 to 2024.

---

## 3. Adobe RoboHelp output parsing

### What the CST corpus actually is (local check)

- **RoboHelp version and format:** Topics carry `content="Adobe RoboHelp 11"`. Each `mergedProjects/<module>/` folder is a **classic WebHelp** project, with `whproj_xml.js`, `whcsh_xml.js` and `wh*.js` runtime files. It is not Responsive HTML5.
- **Data files:** Every file in `whxdata/` wraps XML in a JS string, `gXMLBuffer="<?xml …>"`:

  | File | Content |
  | --- | --- |
  | `whtdata0_xml.js` | TOC: `<tocdata><book name><item name url>` |
  | `whidata0_xml.js` | Author keyword index: `<indexdata><key name><topic name url>`, 919 keys in the 3D module |
  | `whglo_xml.js` | Glossary; empty in the 3D module |
  | `synonym_xml.js` | Synonyms; empty |
  | `topictable_0_xml.js` | `<di ky rd="path\|title" ct="excerpt">` |
  | `package_*_xml.js` | Full-text postings: `<wd nm rd>` |
  | `whfts_xml.js` | Lists the search index files |
- **Math:** 175 of 5,567 HTML files load MathJax 3 (`mathjax/es5/tex-svg.js`) with `inlineMath: [['$','$'], ['\\(','\\)']]`. The TeX source is therefore in the HTML.
- **Size:** About 97 MB of HTML and about 6,900 raster or SVG images (1,084 GIF, 44 SVG). `Documentation/` holds 11 PDF manuals, 72 MB in total.

### Libraries and scripts found

- **No library for classic WebHelp `whxdata`.** I searched GitHub repos for "robohelp", "robohelp markdown", "robohelp converter", "robohelp webhelp" and "whxdata", and GitHub code for `whtdata0_xml`, `whidx_xml` and `topictable_0_xml`. Besides log files and CST prior art, the only hits were generic RoboHelp test repos.
- **Only Responsive HTML5 parsers exist,** and they target the newer `whxdata/toc.new.js` (`var toc = [...]`) format, not CST's:
  - [BloomBooks/bloom-docs `ref-docs/download.ts`](https://github.com/BloomBooks/bloom-docs/blob/main/ref-docs/download.ts) (MIT) parses that file with a regex and `JSON.parse`.
  - [TheAxiomFoundation/axiom-corpus](https://github.com/TheAxiomFoundation/axiom-corpus) (MIT) points at the same file.
- **[GamemakerChina/robohelp-to-markdown-script](https://github.com/GamemakerChina/robohelp-to-markdown-script)** (MIT, last push 2022-11-11): "semi-automatic, manual adjustment is required after use". It runs pandoc through batch files and makes manual global replacements.
- **CHM:** The 2024 sample has no `.chm` files **(local check)**, so CHM tools are irrelevant. For reference, [pychm](https://pypi.org/project/pychm/) is GPL with its last release in 2019, and [DTDucas/chm-converter](https://github.com/DTDucas/chm-converter) is MIT.

**Verdict:** Write the parser ourselves. Use a regex to pull out the `gXMLBuffer` string literal, unescape it as a JS string, then parse it with `lxml`. Prefer this over executing the bundled JavaScript, as the brainstorm suggested. The custom code amounts to about one parser per file type (TOC, index, glossary, topic table, CSH map).

---

## 4. Sphinx output reuse

- **[sphobjinv](https://pypi.org/project/sphobjinv/)** 2.4 (2026-03-23, MIT, Python ≥3.10; [repo](https://github.com/bskinn/sphobjinv)): "A toolkit for inspection/manipulation of Sphinx objects inventories", with decoding, encoding and fuzzy "suggest" ([docs](https://sphobjinv.readthedocs.io/en/stable/)). A stdlib `zlib.decompress` of the body is enough for us **(local check)**.
- **The CST 2024 inventory (local check):**
  - Header: `# Project: CST Python Libraries`, `# Version: 1.0`.
  - 764 entries: 340 `py:method`, 263 `py:property`, 86 `py:class`, 36 `py:function`, 21 `py:module`, 10 `std:label` and 8 `std:doc`.
  - URIs look like `source/cst.asymptotic.html#$`, where `$` stands for the object name.
  
  This is an authoritative exact-identifier → anchor map, ready for the exact-lookup table.
- **`searchindex.js`:**
  - The CST build says "Created using Sphinx 4.4.0". Its `searchindex.js` is `Search.setIndex({docnames:[…]…})` with **unquoted keys**, so `json.loads` fails **(local check)**.
  - Current Sphinx writes JSON (`json.dumps`, [sphinx/search/__init__.py](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/search/__init__.py)).
  - Which Sphinx release made that change is **unverified**.
  - Its postings don't matter for us, because we re-index the text ourselves. Its `titles` and `objects` duplicate `objects.inv`.
- **[sphinx-markdown-builder](https://pypi.org/project/sphinx-markdown-builder/)** 0.6.11 (2026-08-16, MIT) and **[sphinx-llms-txt](https://pypi.org/project/sphinx-llms-txt/)** 0.7.1 (2025-12-16, MIT) are Sphinx *builders*. They need the reST sources and a Sphinx build. The CST install ships only built HTML (`_images`, `_static`, `source/*.html`, no `_sources/`) **(local check)**, so neither applies.
- **Converting built Sphinx HTML:** Use the same HTML → Markdown converter, with Sphinx-specific rules. `dl.py.method` / `dt[id]` anchors match the `objects.inv` anchors.

---

## 5. HTML → Markdown converters

| Tool | Version / date | License | Hooks | Tables | Math |
| --- | --- | --- | --- | --- | --- |
| [markdownify](https://github.com/matthewwithanm/python-markdownify) | 1.2.3 / 2026-06-30 ([PyPI](https://pypi.org/project/markdownify/)) | MIT | Subclass `MarkdownConverter` and add `convert_<tag>(self, el, text, parent_tags)` ([README](https://github.com/matthewwithanm/python-markdownify#creating-custom-converters)) | GFM; `table_infer_header` | None; only `sub_symbol` / `sup_symbol`. Needs a custom converter that protects `$…$` / `\(…\)`. |
| [html-to-markdown](https://github.com/xberg-io/html-to-markdown) (Rust core) | 3.18.6 / 2026-10-22 ([PyPI](https://pypi.org/project/html-to-markdown/)), abi3 `win_amd64` wheel | MIT | `convert(html, options, visitor)`; "40+ callbacks for text, inline elements, links, images, headings, lists, blocks, and tables" ([Python README](https://github.com/xberg-io/html-to-markdown/blob/main/packages/python/README.md)) | GFM, plus `result.tables` structured data | Not documented (**unverified**) |
| [markitdown](https://github.com/microsoft/markitdown) | 0.1.9 / 2026-10-21 ([PyPI](https://pypi.org/project/markitdown/)) | MIT | HTML goes through a `_CustomMarkdownify(markdownify.MarkdownConverter)` ([source](https://github.com/microsoft/markitdown/blob/main/packages/markitdown/src/markitdown/converters/_markdownify.py)) | Through markdownify | None |
| [pandoc](https://github.com/jgm/pandoc) | 3.12.1 / 2026-10-08 ([releases](https://github.com/jgm/pandoc/releases)); [pypandoc](https://pypi.org/project/pypandoc/) and [pypandoc-binary](https://pypi.org/project/pypandoc-binary/) 1.17 | GPL-2.0-or-later (executable); pypandoc MIT | [Lua filters](https://pandoc.org/lua-filters.html) | Pipe or grid tables; complex tables can stay raw HTML | **Best of the group.** The HTML reader converts MathML to TeX through texmath, reads `<script type="math/tex">`, and skips MathJax-generated spans ([HTML.hs](https://github.com/jgm/pandoc/blob/main/src/Text/Pandoc/Readers/HTML.hs)). `tex_math_dollars` / `tex_math_single_backslash` "can also be used with HTML input. This is handy for reading web pages formatted using MathJax" ([manual](https://pandoc.org/MANUAL.html#math-input)). |
| [trafilatura](https://github.com/adbar/trafilatura) | 2.3.1 / 2026-10-06 ([PyPI](https://pypi.org/project/trafilatura/)) | Apache-2.0 | `favor_precision` / `favor_recall`, `include_tables`, `include_images` ([docs](https://trafilatura.readthedocs.io/en/latest/usage-python.html)) | Text of tables | Not mentioned |
| [html2text](https://github.com/Alir3z4/html2text) | 2025.4.15 / 2025-04-15 ([PyPI](https://pypi.org/project/html2text/)) | **GPL-3.0-or-later** | Options only | Basic | None |

**Verdict:**

- **Primary converter:** markdownify, or html-to-markdown if speed matters across about 5,600 topics. Add custom converters for RoboHelp dropdown/expand spans, image references, anchors, and MathJax TeX passthrough.
- **Pandoc:** Worth a side-by-side test on the 175 MathJax topics, and as a fallback for complex tables.
- **Avoid:** trafilatura, because main-content heuristics may drop content from well-formed help topics; and html2text, because of its GPL license.

---

## 6. PDF → Markdown / structured extraction

### Overview

Code license, weight license and hardware for each tool:

| Tool | Latest (date) | Code license | Model-weight license | Windows / CPU | Hardware notes |
| --- | --- | --- | --- | --- | --- |
| **[Docling](https://github.com/docling-project/docling)** | 2.142.1 (2026-10-23) | MIT | [layout-heron](https://huggingface.co/docling-project/docling-layout-heron): Apache-2.0. TableFormer [docling-models](https://huggingface.co/docling-project/docling-models): CDLA-Permissive-2.0 / Apache-2.0. [CodeFormulaV2](https://huggingface.co/docling-project/CodeFormulaV2): CDLA-Permissive-2.0. [granite-docling-258M](https://huggingface.co/ibm-granite/granite-docling-258M): Apache-2.0. | "Works on macOS, Linux and Windows … x86_64 and arm64" ([README](https://github.com/docling-project/docling)); CPU OK | VLM pipeline timings are listed only for Apple MPS ([vision models](https://docling-project.github.io/docling/usage/vision_models/)) |
| **[MinerU](https://github.com/opendatalab/MinerU)** | 4.0.12 (2026-10-11) | "MinerU Open Source License": Apache-2.0 plus a commercial-licence threshold above 100M MAU or USD 20M monthly revenue, and attribution for online services ([LICENSE.md](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md)) | [MinerU2.5-Pro-2604-1.2B](https://huggingface.co/opendatalab/MinerU2.5-Pro-2604-1.2B): Apache-2.0. [MinerU2.5-2509-1.2B](https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B): **AGPL-3.0**. | Windows PowerShell install documented. "small models run ONNX CPU inference and the VLM runs llama.cpp in Vulkan mode" ([README](https://github.com/opendatalab/MinerU)) | Base tier needs 2 GB RAM; standard needs 8 GB with Vulkan recommended (same) |
| **[Marker](https://github.com/datalab-to/marker)** | 2.0.0 (2026-07-20) | Apache-2.0 | Modified OpenRAIL-M: "free for research, personal use, and startups under $5M funding/revenue" ([README](https://github.com/datalab-to/marker#commercial-usage)) | "Works on GPU, CPU, or MPS". CPU uses `--mode fast` plus a llama.cpp `llama-server`. | `--disable_ocr` skips equations |
| **PyMuPDF4LLM** (now inside [PyMuPDF](https://github.com/pymupdf/PyMuPDF) 2.0, 2026-10-19) | The `pymupdf4llm` 2.0 package is now an empty shim ([PyPI](https://pypi.org/project/pymupdf4llm/)) | **AGPL-3.0** or Artifex commercial ([PyPI](https://pypi.org/project/pymupdf/)) | Layout model also folded into PyMuPDF 2 | abi3 `win_amd64`; very fast on CPU | — |
| **[olmOCR](https://github.com/allenai/olmocr)** | 0.4.27 (2026-03-12) | Apache-2.0 | [olmOCR-2-7B-1025](https://huggingface.co/allenai/olmOCR-2-7B-1025): Apache-2.0 | "Recent NVIDIA GPU … at least 12 GB of GPU RAM" (README) | Not on the laptop |
| **[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)** (PP-StructureV3, PaddleOCR-VL) | 3.7.0 (2026-06-11) | Apache-2.0 | [PaddleOCR-VL-1.6](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6): Apache-2.0 | `paddlepaddle` 3.3.1 has Windows wheels for cp310–cp313 ([PyPI](https://pypi.org/project/paddlepaddle/)). For VL, "vLLM, SGLang, and FastDeploy cannot run natively on Windows", but x64 CPU works through PaddlePaddle, Transformers or llama.cpp ([PaddleOCR-VL docs](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html)) | "inference may be slow" on CPU (same) |
| **[dots.ocr → dots.mocr](https://github.com/studio-dots-ai/dots.ocr)** | Renamed 2026-03-19 | MIT | [dots.ocr](https://huggingface.co/rednote-hilab/dots.ocr) and [dots.mocr](https://huggingface.co/dots-studio/dots.mocr): MIT | 3B; vLLM / GPU. Community GGUF builds exist. | — |
| **[DeepSeek-OCR](https://github.com/deepseek-ai/DeepSeek-OCR) / [-OCR-2](https://github.com/deepseek-ai/DeepSeek-OCR-2)** | No releases; last push 2026-02 | MIT / Apache-2.0 | [OCR](https://huggingface.co/deepseek-ai/DeepSeek-OCR): MIT. [OCR-2](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2): Apache-2.0. | "cuda11.8+torch2.6.0", vLLM 0.8.5 manylinux wheel, flash-attn ([README](https://github.com/deepseek-ai/DeepSeek-OCR-2)) | Linux + NVIDIA |
| **[Nougat](https://github.com/facebookresearch/nougat)** | 0.1.17 (2023-10-04, [PyPI](https://pypi.org/project/nougat-ocr/)) | MIT | [nougat-base](https://huggingface.co/facebook/nougat-base): **CC-BY-NC-4.0** | — | Unmaintained; superseded — avoid |
| **[Chandra 2](https://github.com/datalab-to/chandra)** | 0.2.0 (2026-03-18) | Apache-2.0 | Modified OpenRAIL-M: "free … under $2M … cannot be used competitively with our API" ([README](https://github.com/datalab-to/chandra#commercial-usage)) | 4B; GPU | — |
| **[Surya 2](https://github.com/datalab-to/surya)** | 0.22.1 (2026-07-20) | Apache-2.0 | Modified OpenRAIL-M | 0.65B; vLLM or llama.cpp (CPU) | — |

### Benchmarks, formula handling and provenance

- **Docling:**
  - olmocr-bench 50.3 on GPU, as reported by Marker's vendor ([Marker README](https://github.com/datalab-to/marker#benchmarks)). Not in the OmniDocBench v1.6 table.
  - Formulas to LaTeX through `do_formula_enrichment` (`CodeFormulaV2` by default). Enrichments are "disabled by default" ([enrichments](https://docling-project.github.io/docling/usage/enrichments/), [pipeline_options.py](https://github.com/docling-project/docling/blob/main/docling/datamodel/pipeline_options.py)).
  - Provenance: DoclingDocument with pages, bboxes and pictures ([haiku.rag](https://github.com/ggozad/haiku.rag)).
- **MinerU:**
  - OmniDocBench v1.6: MinerU2.5-Pro scores 95.75 overall with formula CDM 97.45; the pipeline backend scores 86.47. OmniDocBench is run by the same organization as MinerU ([OmniDocBench](https://github.com/opendatalab/OmniDocBench)).
  - Output: LaTeX among nine render targets. "stable page/block locators" ([README](https://github.com/opendatalab/MinerU)).
- **Marker:**
  - olmocr-bench, self-reported: 76.0 in balanced mode on GPU; 43.6 for fast, no-OCR on CPU at 23.7 pages/s ([README](https://github.com/datalab-to/marker#benchmarks)).
  - OmniDocBench v1.6: 78.44 overall, formula 85.24 ([OmniDocBench](https://github.com/opendatalab/OmniDocBench)).
  - Math as `$$` LaTeX in Markdown and `<math>` in HTML. JSON blocks carry a page-scoped id (`/page/10/SectionHeader/0`) and a 4-corner `polygon` ([README](https://github.com/datalab-to/marker)).
- **PyMuPDF4LLM:** Extracts the text layer. I found no formula-to-LaTeX path (**unverified**).
- **olmOCR:** OmniDocBench v1.6: 85.74 overall, formula 88.10.
- **PaddleOCR-VL-1.6:**
  - OmniDocBench v1.6: 96.34 overall, formula 97.53.
  - JSON carries `block_bbox` and `block_order`. Markdown output; `show_formula_number`.
  - Per its README, PP-StructureV3 "provides more fine-grained coordinate information" than the VL models.
- **dots.ocr:** 90.77 on OmniDocBench v1.6.
- **DeepSeek-OCR 2:** 90.25 on OmniDocBench v1.6, formula 91.84.
- **Chandra 2:** olmocr-bench 85.8 ± 0.8, self-reported.
- **Surya 2:**
  - olmOCR-bench 83.3, self-reported; ArXiv 88.3, OldMath 81.4, MultCol 82.4.
  - Math "inside `<math>…</math>` tags … in KaTeX-compatible LaTeX" ([README](https://github.com/datalab-to/surya#math--equations)).

### 2026 entrants (OmniDocBench v1.6)

Overall score / formula CDM from the [OmniDocBench README](https://github.com/opendatalab/OmniDocBench); licenses from Hugging Face:

| Model | Size | Overall | Formula CDM | Weight license |
| --- | --- | --- | --- | --- |
| [TeleOCR](https://huggingface.co/XingChen-AGI/TeleOCR) | 1.2B | 96.91 | 96.59 | Apache-2.0 |
| [OvisOCR2](https://huggingface.co/ATH-MaaS/OvisOCR2) | 0.8B | 96.47 | 97.49 | Apache-2.0 |
| [GLM-OCR](https://huggingface.co/zai-org/GLM-OCR) | 0.9B | 95.22 | 97.18 | MIT; official GGUF at [ggml-org/GLM-OCR-GGUF](https://huggingface.co/ggml-org/GLM-OCR-GGUF), so llama.cpp and Vulkan apply |
| [Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR) | 3B | 94.00 | — | MIT |
| [HunyuanOCR](https://huggingface.co/tencent/HunyuanOCR) | 1B | 89.95 | — | Custom "tencent-hunyuan-community" |

Also new: [LightOnOCR-2-1B](https://huggingface.co/lightonai/LightOnOCR-2-1B) (Apache-2.0) and [Infinity-Parser2-Pro](https://huggingface.co/infly/Infinity-Parser2-Pro) (Apache-2.0, olmOCR-bench 87.6 per [Surya's table](https://github.com/datalab-to/surya#olmocr-bench)).

**Unverified:** CPU speed for any of these on the 7840HS. Measure it.

### Multi-column reading order

OmniDocBench reports Read Order Edit (lower is better) ([OmniDocBench](https://github.com/opendatalab/OmniDocBench)):

| System | Read Order Edit |
| --- | --- |
| MinerU2.5-Pro | 0.120 |
| PaddleOCR-VL-1.6 | 0.128 |
| MinerU pipeline | 0.153 |
| olmOCR | 0.216 |
| Marker | 0.243 |

Surya reports MultCol 82.4 on olmOCR-bench.

### Verdict

- **Fewest licensing questions:** Docling (all weights permissive, Windows, provenance) or PaddleOCR / MinerU-Pro (Apache).
- **Highest formula and reading-order quality locally:** MinerU 4 (VLM tier through llama.cpp Vulkan on the laptop, vLLM on NVIDIA) or PaddleOCR-VL-1.6.
- **Pure-CPU speed on born-digital text:** Marker `--disable_ocr` (equations skipped) or PyMuPDF (AGPL).
- **Bake-off:** Run Docling (with formula enrichment), MinerU 4 (standard tier) and PaddleOCR-VL-1.6 on 3–5 representative CST manuals and whitepapers. Use the NVIDIA box for the VLMs.

---

## 7. Equation image → LaTeX

### Specialist formula recognizers

**Pix2Text**

- Version: [1.1.7](https://pypi.org/project/pix2text/) (2026-08-23). MIT code ([repo](https://github.com/breezedeus/Pix2Text)).
- Models: [MFR-1.5](https://huggingface.co/breezedeus/pix2text-mfr-1.5) and [MFD-1.5](https://huggingface.co/breezedeus/pix2text-mfd-1.5), both MIT. MFR is TrOCR-based and ships ONNX.
- Evaluation: only a vendor CER chart on 485 user-upload images; no CDM ([model card](https://huggingface.co/breezedeus/pix2text-mfr-1.5)).
- Dependencies: **PyMuPDF (AGPL)** and torch ([PyPI requires_dist](https://pypi.org/project/pix2text/)).
- CPU-friendly.

**pix2tex / LaTeX-OCR**

- Version: [0.1.4](https://pypi.org/project/pix2tex/) (2025-01-18), MIT. Repo last pushed 2025-01-18 ([repo](https://github.com/lukas-blecher/LaTeX-OCR)).
- OmniDocBench formula subset (v1.0): CDM 73.9, against UniMERNet-B 85.0, Mathpix 86.6 and GPT-4o 86.8 ([OmniDocBench](https://github.com/opendatalab/OmniDocBench#formula-recognition-evaluation)).
- Effectively superseded.

**UniMERNet**

- Version: [0.2.3](https://pypi.org/project/unimernet/) (2024-12-26). Apache-2.0 code and [weights](https://huggingface.co/wanderkid/unimernet_base).
- Created the UniMER-Test sets (SPE/CPE/SCE/HWE) and the CDM metric, which was accepted at CVPR 2025 ([repo](https://github.com/opendatalab/UniMERNet)).
- About 8.3 s per formula on CPU (high-perf mode, per the PaddleX table below).

**PP-FormulaNet / PP-FormulaNet_plus** (PaddleX / PaddleOCR)

- Weights: [Apache-2.0](https://huggingface.co/PaddlePaddle/PP-FormulaNet_plus-L).
- Vendor table on a Xeon Gold 6271C in high-performance mode ([PaddleOCR docs](https://www.paddleocr.ai/latest/en/version3.x/module_usage/formula_recognition.html)):

  | Model | En-BLEU | CPU time per formula |
  | --- | --- | --- |
  | plus-L | 92.22 | 3.1 s |
  | plus-M | 91.45 | 1.6 s |
  | plus-S | 88.71 | 0.26 s |
  | UniMERNet | 85.91 | 8.3 s |
  | LaTeX_OCR | 74.55 | — |

  BLEU, not CDM.

**Texify**

- [Archived](https://github.com/VikParuchuri/texify), GPL-3.0, last release 2024-10-31.
- Its role moved into Surya 2, which does inline math during OCR (OpenRAIL-M weights) ([Surya](https://github.com/datalab-to/surya#math--equations)).

**TexTeller**

- Version: [1.0.2](https://pypi.org/project/texteller/) (2025-04-21). Apache-2.0 code and [weights](https://huggingface.co/OleehyO/TexTeller).

**Docling CodeFormulaV2**

- CDLA-Permissive-2.0. Formula enrichment inside Docling (see section 6).

### General VLMs vs. small document VLMs

Page-level formula CDM on OmniDocBench v1.6 ([OmniDocBench](https://github.com/opendatalab/OmniDocBench)):

| Model | Formula CDM |
| --- | --- |
| PaddleOCR-VL-1.6 | 97.53 |
| MinerU2.5-Pro | 97.45 |
| GLM-OCR | 97.18 |
| Gemini 3 Pro | 95.99 |
| Gemini 3 Flash | 95.16 |
| Qwen3-VL-235B | 92.55 |
| GPT-5.2 | 88.21 |

Claude models are not listed. So frontier cloud VLMs are no longer clearly better than specialist sub-2B models on printed formulas, and the specialists run locally. The benchmark maintainer (OpenDataLab) also develops MinerU.

**Unverified:** I found no current, independent UniMER-Test CDM comparison of Pix2Text MFR-1.5, PP-FormulaNet_plus and the small VLMs on *isolated* equation crops. That is our use case for CST GIF equations.

### Verdict

1. Mine the TeX that is already there first. 175 MathJax topics carry it **(local check)**, and PDFs with an embedded text layer may yield it too.
2. For equation images, benchmark PP-FormulaNet_plus-M/L (Apache), Pix2Text MFR-1.5 (MIT) and one small VLM such as GLM-OCR through llama.cpp on 50–100 hand-checked CST equations. Score them with CDM.
3. Keep the original images, as the brainstorm requires.

---

## 8. Search

### SQLite FTS5 in the python.org Windows builds (local check)

- **Build flags:** CPython's Windows build compiles SQLite with `SQLITE_ENABLE_FTS4;SQLITE_ENABLE_FTS5;SQLITE_ENABLE_RTREE;SQLITE_ENABLE_MATH_FUNCTIONS` ([PCbuild/sqlite3.vcxproj, 3.13](https://github.com/python/cpython/blob/3.13/PCbuild/sqlite3.vcxproj)). The 3.13 branch bundles `sqlite-3.50.4.0` ([get_externals.bat](https://github.com/python/cpython/blob/3.13/PCbuild/get_externals.bat)).
- **Tested interpreters:**
  - PSF-installed CPython 3.12.6 (SQLite 3.45.3)
  - PSF-installed CPython 3.13.7 (SQLite 3.50.4)
  - uv-managed CPython 3.13.2 (SQLite 3.47.1)
- **Results on all three:**
  - `PRAGMA compile_options` lists `ENABLE_FTS5`.
  - `tokenize='trigram'` works, and so does `bm25()`.
  - `enable_load_extension` exists, which sqlite-vec would need.
- **Trigram availability:** The trigram tokenizer arrived in SQLite 3.34.0 (2020-12-01) ([release log](https://sqlite.org/releaselog/3_34_0.html)).
  - It supports substring `MATCH` and indexed `LIKE` / `GLOB`.
  - "Substrings consisting of fewer than 3 unicode characters do not match any rows" ([FTS5 docs](https://sqlite.org/fts5.html)).
  - `tokenchars` and `separators` adjust what unicode61 treats as part of a token (same page).

### How FTS5 handles CST-style identifiers (local check, Python 3.13.7)

| Query | Tokenizer | Result |
| --- | --- | --- |
| `Solver.FrequencyRange`, unquoted | unicode61 | **Syntax error** (`fts5: syntax error near "."`) |
| `"Solver.FrequencyRange"`, quoted | unicode61 | Matches |
| `"Solver FrequencyRange"` | unicode61 | Also matches: punctuation is lost |
| `FrequencyRange` alone | unicode61 | Matches |
| `MeshProp` | unicode61 | Doesn't match; camelCase isn't split |
| `MeshProp` | trigram | Matches |
| `Fr` (2 characters) | trigram | No results |
| `"Solver.FrequencyRange"` | unicode61 with `tokenchars '._'` | Matches as a single token |

**Consequence:** Never pass raw user input to `MATCH`. Add a separate exact-symbol table: `symbol → section`, filled from `objects.inv` plus VBA signature regexes as in the MuziIsabel skill, and queried before FTS. Add a trigram FTS table for partial identifiers.

### How other tools handle identifiers

- **qmd:** porter unicode61, plus phrase-sanitizer fixes for dotted tokens ([CHANGELOG](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)).
- **docs-mcp-server:** "matches the whole input as a phrase or any of its terms" ([data-storage.md](https://github.com/arabold/docs-mcp-server/blob/main/docs/concepts/data-storage.md)).
- **MuziIsabel:** a symbol sidecar plus boosts ([reference.md](https://github.com/MuziIsabel/CST-Studio-Suite-Help/blob/main/reference.md)).
- **Code search engines:** use trigram indexes, for example [sourcegraph/zoekt](https://github.com/sourcegraph/zoekt) ("Fast trigram based code search", Apache-2.0).

### Alternatives (not needed for the first version)

- **[tantivy-py](https://github.com/quickwit-oss/tantivy-py)** 0.27.0 (2026-10-21, MIT): abi3 `win_amd64` wheel ([PyPI](https://pypi.org/project/tantivy/)). The Lucene-like Rust engine has a richer query parser. It adds a second store next to SQLite.
- **[bm25s](https://github.com/xhluca/bm25s)** 0.3.15 (2026-10-22, MIT): pure Python and NumPy, using "eager sparse scoring" ([README](https://github.com/xhluca/bm25s)). The README describes no positional or phrase index.
- **[sqlite-vec](https://github.com/asg017/sqlite-vec)** 0.1.9 (2026-03-31, MIT/Apache-2.0): has a `win_amd64` wheel. "`sqlite-vec` is a pre-v1, so expect breaking changes!" ([README](https://github.com/asg017/sqlite-vec)). It keeps vectors in the same `.sqlite` file, which suits hybrid search through RRF the way docs-mcp-server does it.
- **[LanceDB](https://github.com/lancedb/lancedb)** 0.40.0 (2026-10-07, Apache-2.0): has a `win_amd64` wheel. "Lance-native FTS" with BM25, `ngram` tokenizer, phrase queries (with `with_position=True`) and fuzzy search. New rows need `table.optimize()` before they are indexed ([FTS docs](https://docs.lancedb.com/search/full-text-search)). This is what haiku.rag uses.

---

## 9. MCP Python SDK and client behavior

### SDKs

**Official `mcp`**

- Version: [2.3.0](https://pypi.org/project/mcp/) (2026-10-02), MIT ([releases](https://github.com/modelcontextprotocol/python-sdk/releases)).
- **Rename:** v2.0.0 (Jul 28): "`FastMCP` is now `MCPServer`". Use `from mcp.server import MCPServer`. "everything under `mcp.server.fastmcp.*` now lives under `mcp.server.mcpserver.*`" ([what's new](https://py.sdk.modelcontextprotocol.io/whats-new/)).
- **Protocol:** v2 "implements the 2026-07-28 revision, and it serves both revisions at once". Types moved to `mcp-types`.
- **v1:** v1.x is in maintenance; latest 1.30.0 (Sep 7).
- **Windows:** depends on `pywin32` ([PyPI](https://pypi.org/project/mcp/)).

**Images and resources in the official SDK**

- **Images:** `from mcp.server.mcpserver import Image`. Pass `path=` (MIME type from the suffix: png/jpg/jpeg/gif/webp) or `data=` plus `format=`. The SDK emits `ImageContent` ([media docs](https://py.sdk.modelcontextprotocol.io/servers/media/)).
- **Embedded resources:** `EmbeddedResource` with `TextResourceContents` / `BlobResourceContents`, and `ResourceLink` for pointers.
- **Return shapes:** Since v2.1.0, tools annotated to return content blocks no longer advertise `outputSchema` / `structuredContent` unless `structured_output=True` ([releases](https://github.com/modelcontextprotocol/python-sdk/releases)).
- **Resources:** `@mcp.resource("scheme://{param}")` templates ([docs home](https://py.sdk.modelcontextprotocol.io/)).
- **Server instructions:** set on the server; the client exposes `client.instructions` ([what's new](https://py.sdk.modelcontextprotocol.io/whats-new/)).

**Standalone FastMCP**

- Version: [4.1.3](https://pypi.org/project/fastmcp/) (2026-10-20), Apache-2.0 ([repo](https://github.com/PrefectHQ/fastmcp)).
- "FastMCP 1.0 was incorporated into the official MCP Python SDK in 2024."
- v4 depends on `mcp-types` but **not** on `mcp` ([fastmcp-slim on PyPI](https://pypi.org/project/fastmcp-slim/)), so it is a separate implementation on shared types.
- It adds more framework surface (apps, clients). We don't need it for a read-only stdio server.

### Clients

| | Claude Code | Codex CLI | Cursor |
| --- | --- | --- | --- |
| **Images from MCP tools reach the model** | Yes: "When an MCP tool returns a PNG, JPEG, GIF, or WebP image, Claude sees the image inline … may be scaled down". The original bytes are also saved to `tool-results/` from v2.1.283 ([docs](https://code.claude.com/docs/en/mcp)). | Yes. A stdio MCP `image` result becomes `{"type":"input_image", "image_url": data-URL, "detail":"high"}`. Large images are resized and stripped for text-only models ([rmcp_client.rs tests](https://github.com/openai/codex/blob/main/codex-rs/core/tests/suite/rmcp_client.rs)). | "Cursor attaches returned images to the chat. If the model supports images, it analyzes them" ([docs](https://cursor.com/docs/mcp)). |
| **Output limits** | Warning at 10,000 tokens. Default maximum 25,000 (`MAX_MCP_OUTPUT_TOKENS`). Text results over 50,000 characters are saved to a file unless the tool sets `_meta["anthropic/maxResultSizeChars"]` (ceiling 500,000). Image results stay subject to `MAX_MCP_OUTPUT_TOKENS` ([docs](https://code.claude.com/docs/en/mcp)). | Per-model truncation policy: `{"mode":"tokens","limit":10000}` for the bundled models ([models.json](https://github.com/openai/codex/blob/main/codex-rs/models-manager/models.json)). Override globally with `tool_output_token_limit`, or per tool with `tools.<tool>.output_token_limit` ([Codex MCP docs](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [truncation tests](https://github.com/openai/codex/blob/main/codex-rs/core/tests/suite/truncation.rs)). Tool timeout 60 s by default, startup 10 s. | Not documented (**unverified**) |
| **Resources** | `@server:protocol://path` mentions, fuzzy autocomplete, plus automatic list/read resource tools ([docs](https://code.claude.com/docs/en/mcp)) | Built-in `list_mcp_resources`, `list_mcp_resource_templates` and `read_mcp_resource` tools ([mcp_resource_spec.rs](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/mcp_resource_spec.rs)) | "Resources … Supported" in the protocol table ([docs](https://cursor.com/docs/mcp)) |
| **Server instructions** | Used. Loaded at session start along with tool names under tool search. Truncated at 4,096 characters (2,048 before v2.1.296) ([docs](https://code.claude.com/docs/en/mcp)). | Used "as server-wide guidance alongside the server's tools". Keep the first 512 characters self-contained ([Codex MCP docs](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)). | Not mentioned in the docs. A forum question asking about it has no official answer ([forum](https://forum.cursor.com/t/developer-documentation-for-mcp/77281)). **Unverified.** |
| **Tool loading** | Tool search is on by default: tools are deferred, and descriptions loaded through search are capped at 16,384 characters. `alwaysLoad` overrides this per server or tool ([docs](https://code.claude.com/docs/en/mcp)). | `enabled_tools` / `disabled_tools` | — |
| **Current version** | — | rust-v0.164.0 (2026-10-23), Apache-2.0 ([releases](https://github.com/openai/codex/releases)) | — |

**Implications for our design:**

- Keep `search` results well under 10k tokens; that is Codex's default limit.
- Return images as PNG, JPEG, GIF or WebP; SVG is not accepted, so rasterize SVG assets.
- Put the routing guidance in the first 512 characters of the server instructions.
- Treat Cursor's use of server instructions as unknown until tested.

---

## 10. Plain files vs. a search MCP server

### Evidence

- **Anthropic (2025-09-29):** Claude Code uses a hybrid of CLAUDE.md "dropped into context up front" and "primitives like glob and grep" for just-in-time retrieval. "Folder hierarchies, naming conventions, and timestamps all provide important signals" ([post](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).
- **Claude Code's Read tool** already returns PNG/JPEG/GIF/WebP "as visual content that Claude can see". It also reads PDF page ranges (up to 20 pages per call, rendered with `pdftoppm`) ([tools reference](https://code.claude.com/docs/en/tools-reference)).
- **Codex** has a built-in `view_image` tool to "View a local image file from the filesystem" ([view_image_spec.rs](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/view_image_spec.rs)).

  So for these two clients, a Markdown tree with relative image paths already lets the model see images. MCP isn't strictly needed for that.
- **Cursor removed @Docs indexing** "on purpose starting in 3.14.2". It recommends keeping "the docs you need as local Markdown files in your workspace", and concedes that "a curated, indexed corpus is a different workflow" (forum reply by Dean Rie, 2026-08-20, [forum](https://forum.cursor.com/t/adding-docs-in-cursor-ide/168561); I did not independently confirm that he is Cursor staff, and the removal is not in Cursor's docs I read).
- **Cursor (2025-11-06):** adding semantic search to grep raised agent answer accuracy by 12.5% on average (6.5–23.5% depending on model), and "the combination produces the best outcomes" ([blog](https://cursor.com/blog/semsearch)). This was measured on code, not docs.
- **Vercel (2026-01-27):** In Next.js 16 evals, an 8 KB compressed docs index in AGENTS.md pointing at local doc files reached a 100% pass rate. A skill reached 53% by default and 79% with explicit instructions; it "was never invoked in 56% of eval cases". The suite was built by the authors themselves ([blog](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals)).
- **LlamaIndex (2026-01-13):** A filesystem agent beat hybrid RAG on correctness, 8.4 vs 6.4, on 5 long papers and 5 questions. At 100–1,000 documents, RAG was "substantially faster and slightly more correct". The benchmark is tiny and LLM-judged ([blog](https://www.llamaindex.ai/blog/did-filesystem-tools-kill-vector-search)).
- **arXiv 2605.15184 (2026-05-14):** "grep generally yields higher accuracy than vector retrieval", but results "depend strongly on which harness and tool-calling style is used". Tested on 116 LongMemEval questions across Claude Code, Codex and Gemini CLI ([paper](https://arxiv.org/abs/2605.15184)).
- **Conventions:**
  - `llms.txt` (Jeremy Howard, 2024-09-03; v2 page modified 2026-08-10): an H1 name, a blockquote summary, H2 sections of `[name](url): notes` links, and an "Optional" section. It also proposes `page.md` companions ([llmstxt.org](https://llmstxt.org/)).
  - Agent Skills is an open standard with three-stage progressive disclosure ([agentskills.io](https://agentskills.io)), supported by:
    - Claude Code: `SKILL.md` under 500 lines; description and `when_to_use` capped at 1,536 characters ([docs](https://code.claude.com/docs/en/skills)).
    - Codex: `.agents/skills`; the skill list gets about 2% of the context ([docs](https://learn.chatgpt.com/docs/build-skills)).
    - Cursor: also reads `.claude/skills` and `.codex/skills` ([docs](https://cursor.com/docs/skills)).
  - The MuziIsabel skill shows the skill-plus-CLI pattern on this exact corpus.

### Assessment

**What a Markdown tree plus grep and a skill does well:**

- Exact-identifier lookup. Grep is literal, which beats FTS tokenization for `Solver.FrequencyRange`.
- Following links.
- Viewing images and PDF pages in Claude Code and Codex.

**What it does poorly:**

- Ranked concept queries over about 97 MB of HTML-derived text and 11 large manuals. Grep returns unranked line hits, and the agent has to guess vocabulary.
- Bounded output.
- One provenance contract (file, anchor, PDF page) across clients.
- Clients or modes without shell or file access. Cursor's ability to view images from disk without MCP is **unverified**.

**What MCP adds:**

- One ranked call, including the routing to the exact-symbol table.
- Server instructions that Claude Code and Codex inject.
- Image and caption returned together.
- Resources for TOC browsing.

**Recommendation:** Build the Markdown tree and `index.md` / `llms.txt`-style entry points regardless, since they are needed for provenance and manual inspection anyway. Ship a skill and CLI and a thin MCP server over the same SQLite index. Then let the planned query benchmark decide whether MCP beats skill + CLI in each client.

---

## Unverified or open items

- Whether Cursor uses MCP server instructions, and what Cursor's tool-output size limits are.
- Whether haiku.rag runs in FTS-only mode without an embedder, and whether it works on Windows.
- Windows support for docs-mcp-server; it is Node-based and not documented.
- CPU and Vulkan throughput on the 7840HS for MinerU 4 (standard tier), PaddleOCR-VL-1.6, GLM-OCR GGUF and Docling with formula enrichment. No primary-source numbers exist for this hardware.
- An independent UniMER-Test or CDM comparison of current isolated-formula recognizers (Pix2Text MFR-1.5, PP-FormulaNet_plus, small VLMs).
- Whether html-to-markdown handles math.
- Whether PyMuPDF4LLM, now inside PyMuPDF 2.0, has any formula path.
- The Sphinx version in which `searchindex.js` became strict JSON.
- Whether PyPI `py4cst` and GitHub `JustArri/py4cst` are the same project.
- Cursor's removal of @Docs. The only source is a forum reply; Cursor's official docs don't confirm it.
- Benchmark independence. Most numbers are self-reported (Datalab for Marker/Surya/Chandra), or come from a benchmark run by a competitor's organization (OpenDataLab for OmniDocBench and MinerU). None has been measured on CST material.
