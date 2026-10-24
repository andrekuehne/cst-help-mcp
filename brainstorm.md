# Local technical documentation knowledge base — brainstorm

Status: design input for the repository's `grilling-with-docs` workflow, not a final implementation specification. This document consolidates the discussion; no CST corpus or repository has been inspected. Library choices and format assumptions need validation against real samples and current dependency documentation.

## 1. Goal

Build a Python-based tool that processes an installed CST RoboHelp HTML help corpus and folders of technical PDF whitepapers into a portable, locally searchable knowledge base that coding agents such as Codex, Claude Code, and Cursor can consult.

The main workflow is batch-oriented: configure inputs, build once, use the output repeatedly, and replace the CST collection when a new release arrives. Assume the help format remains broadly stable between releases, but detect unsupported changes rather than silently producing incomplete output.

The user is a physicist working with electromagnetic simulation, antenna design, and technical software. Exact API identifiers, mathematical notation, solver limitations, and traceability matter more than polished summaries. Preserve original information rather than rewriting the documentation with an LLM.

## 2. Agreed direction

- Use Markdown as the readable corpus, accompanied by structured metadata and original assets.
- Keep original HTML/PDF sources as authoritative references.
- Ingest both RoboHelp HTML help and a separate folder of PDF whitepapers.
- Capture RoboHelp's existing author-defined keyword index, TOC, and other useful metadata automatically when available.
- Build our own retrieval layer. Do not depend on the RoboHelp browser UI or search runtime at query time.
- Preserve images, equations, code, tables, crosslinks, and source locations.
- Separate expensive conversion/OCR from lightweight lookup.
- Expose the resulting corpus through a local MCP server usable by multiple agents.
- Support repeatable rebuilds and collection replacement without leaving obsolete pages in search results.

Markdown alone is insufficient: an image link does not deliver image pixels to a model, and plain text cannot preserve all source provenance. The lookup interface must serve actual images when requested.

## 3. Proposed scope and exclusions

Initial scope: one known CST help format, general PDF ingestion, section-level lexical search, source citations, image retrieval, and a reproducible CLI build.

Initially exclude model training, a hosted service, automatic web crawling, a GUI, live RoboHelp search reuse, a vector database, and automatic semantic linking of every bibliography reference. These can be revisited if specific needs justify them.

All extraction and indexing should be possible locally after dependencies/models have been obtained. Cloud OCR should not be required. Local retrieval does not imply local inference: cloud-backed agents send retrieved text/images to their model provider.

## 4. Proposed architecture

Two input adapters feed a common structured representation:

1. RoboHelp adapter: topic HTML, navigation/keyword metadata, assets, links.
2. PDF adapter: document structure, page references, tables, figures, formulas.
3. Shared normalization: identities, sections, blocks, assets, provenance.
4. Asset enrichment: equation transcription and optional screenshot/diagram OCR.
5. Link resolution and validation.
6. Export: Markdown, metadata, assets, manifest, build report.
7. Index construction: SQLite FTS5 over sections and metadata.
8. Read-only MCP server and a CLI using the same retrieval implementation.

Persist the normalized representation so formatting/index changes do not require OCR again. Avoid maintaining two independent interpretations of document content: Markdown and search records should be generated from the same structured data.

## 5. Candidate Python stack

These are proposed defaults, not committed dependencies. Verify compatibility and model licensing before locking versions.

| Responsibility | Candidate | Notes |
| --- | --- | --- |
| Environment | Python 3.12 + uv | Lock dependencies; choose Python version based on OCR compatibility. |
| HTML parsing | Beautiful Soup + lxml | Parse topics and XML; handle legacy encodings explicitly. |
| HTML to Markdown | markdownify with custom converters | Preserve anchors, inline images, code, and equations. |
| RoboHelp metadata | Custom adapter | Parse the actual exported XML/JS data format after inspection. |
| PDF extraction | Docling | Evaluate layout, OCR, tables, formulas, and provenance on representative PDFs. |
| Equation image recognition | Pix2Text | Benchmark isolated equation images; retain originals. |
| Image handling | Pillow, pathlib, hashlib | Inspect raster assets, preserve original bytes, deduplicate. |
| Structured records | Pydantic + JSON/JSONL | Schema validation and persisted intermediate representation. |
| Search | Standard-library sqlite3 with FTS5 | Confirm FTS5 availability in the selected runtime. |
| MCP | Official MCP Python SDK | Local stdio transport; pin a supported API version. |
| CLI/config | Typer + TOML | Build, validate, search, inspect, serve. |
| Reporting/testing | logging, optionally Rich; pytest | Focus on extraction fidelity and representative lookup tasks. |

Keep OCR/PDF dependencies separate from the lightweight serving installation if practical. The MCP server should not import or load OCR models. CPU ingestion should be possible; GPU acceleration is a build optimization. Hardware/backend support must be tested rather than assumed.

## 6. RoboHelp ingestion

First inspect a real corpus: top-level help, merged modules, a theory page, a dialog reference, a VBA/API page, images, navigation data, and any independently generated Python/API docs.

Extract topic bodies while removing navigation boilerplate. Retain headings, lists, code, tables, warnings, captions, anchors, image references, and outgoing links. Expand or recover dropdown/pop-up content instead of dropping it because it is hidden. Identify content requiring special handling and report unsupported constructs.

Capture, when available:

- Author-defined keyword/subkeyword entries and their topic/anchor targets.
- TOC hierarchy and topic membership, including multiple TOC placements.
- Synonyms and glossary definitions, keeping their distinct meanings.
- Topic-ID mappings and source paths.
- Full-text vocabulary/postings only if straightforward and useful.

The author-defined alphabetical index is distinct from the generated full-text search index. Editorial keyword associations are valuable even when the phrase never appears in the topic body. Full-text postings are lower priority because the text can be reindexed.

RoboHelp formats vary. Implement a format-specific adapter based on observed files; do not assume all exports use one filename or schema. Prefer parsing data to executing bundled JavaScript. Missing optional metadata may be acceptable; unrecognized required structure must be visible in the report.

## 7. PDF ingestion

Accept recursive folders of technical PDFs as separately named collections. Support born-digital PDFs and scans, multi-column layouts, tables, figures, captions, mathematical notation, and code where feasible.

Preserve document title, supplied metadata, source-relative path, page index, printed page label when available, and block bounding boxes where supported. Allow a small override file for incorrect titles/authors and other extraction mistakes.

Retain the original PDF so the agent can inspect a page or region when extraction is ambiguous. Decide whether page previews are generated at build time or rendered on demand; this is separate from OCR.

Keep PDF hyperlinks where available. Bibliography entries are text unless an actual link exists; automatic reference-to-local-paper matching is optional future work. Do not invent links or DOIs.

Whitepapers and CST documentation can share an index but must remain distinguishable. A paper's proposed method is not evidence that CST implements it.

## 8. Equations and images

Preserve existing LaTeX/MathML or textual equations before resorting to OCR. For HTML equation images, identify candidates from markup/context and evaluate detection rules on real examples; dimensions alone are insufficient.

For every recognized equation, store the original asset reference, extracted LaTeX, surrounding context, extraction method/model, and review status. Preserve inline versus display placement, equation numbers, and nearby variable definitions.

Machine transcription is unverified unless actually reviewed. OCR confidence, if available, is diagnostic rather than proof of correctness. Bold vectors, Greek letters, subscripts, primes, complex conjugation, and signs require particular attention. Do not silently replace an unreadable equation with a guessed expression.

For diagrams and screenshots, preserve originals and captions. OCR of dialog labels or diagram text is optional enrichment. Generated descriptions must be identifiable as generated and must not replace source captions.

Deduplicate assets by byte hash. Preserve originals; create derived PNG previews only when needed for client compatibility. Support relative Markdown asset links. Keep durable manual corrections outside generated output, keyed to source content and invalidated when that source changes.

## 9. Identities, links, and structured records

Use two passes: inventory documents/anchors first, then resolve and rewrite links after the complete mapping exists.

Maintain collection identity, collection version, document identity, section identity, original path/anchor or PDF page, output path, source hash, and extraction provenance. Separate stable logical identity from content hashes and build IDs.

Normalize relative URLs carefully, including fragments, URL encoding, Windows path conventions, and filename case. Preserve external URLs. Distinguish broken internal links, unsupported links, and links to files intentionally outside the collection.

Do not rely exclusively on renderer-generated Markdown heading slugs. Preserve explicit anchors and an authoritative section map for MCP retrieval. Preserve complex tables as structured data and/or HTML when flattening to Markdown would lose associations.

Suggested document/block fields:

```text
collection_id, collection_version, document_id, title
source_type, source_relative_path, source_hash
toc_paths, index_terms, supplied_metadata
sections: section_id, heading_path, ordered_blocks
blocks: type, text/content, source_locator, extraction_status
assets: asset_id, original_path, mime_type, hash, caption, derivatives
links: source_section, label, original_target, resolved_target, status
```

## 10. Retrieval and agent integration

Start with SQLite FTS5 and BM25-based ranking over titles, index terms, heading/TOC paths, body text, captions, and extracted formula text. Weight titles and editorial keywords above ordinary body matches. Treat raw LaTeX search as limited lexical retrieval, not mathematical equivalence matching.

Preserve exact API identifiers and punctuation-sensitive queries through an appropriate supplementary exact-match path. Test tokenization on actual CST methods, error messages, and symbols. Offer collection/version filters and bounded result counts.

Index meaningful sections, splitting oversized sections conservatively. Keep equations with definitions, tables with headings, and method signatures with parameter descriptions. A tentative 500–1,500-token range is only a starting heuristic, not a requirement.

Proposed MCP tools:

```text
search(query, collections?, versions?, limit?)
  -> ranked snippets, source titles, document/section IDs, locators
read_section(document_id, section_id?)
  -> source content, provenance, image references, outgoing links
read_image(asset_id)
  -> actual image content plus caption/transcription status
```

Optional: bounded whole-topic reading, TOC/index browsing, and PDF page/region rendering. Validate image delivery in each target client; a filesystem path alone is not sufficient. Keep server reads confined to configured output/source roots.

Provide brief client instructions to consult these tools for source-specific questions, follow links as necessary, cite version/page/section, and flag uncertain equation transcriptions. Agents should receive retrieved evidence, not an automatically synthesized answer from the server.

Add semantic embeddings only if evaluation exposes lexical retrieval gaps. If added, combine semantic and lexical results; preserve exact lookup and local build capability.

## 11. Build lifecycle and output

Illustrative CLI, to be designed rather than assumed to exist:

```bash
uv run kb build --config corpus.toml
uv run kb validate --output ./output
uv run kb search --output ./output "query"
uv run kb serve --output ./output
```

Suggested output components: collection Markdown trees, assets, structured metadata, search.sqlite, manifest.json, and build-report.json. Keep original source files accessible; decide whether to bundle them or reference managed source copies. Portability must be explicit.

Build into a fresh staging directory, validate, then switch the active output. Do not overlay a new release onto an old Markdown tree. Handle active readers safely and avoid mixing a database from one build with assets from another.

Cache expensive conversion using source content hash plus adapter/converter version, model version, and relevant settings. Consider dependent assets in cache invalidation. Preserve unchanged PDF/equation results across releases. Support resumable failed builds and per-document failures without silently advertising an incomplete build as complete.

Use bounded CPU workers for independent documents and controlled model workers/batches for OCR; do not load a large model in every process. No live watcher or continuous reindexing is required initially.

## 12. Validation and proof of concept

Choose a small representative corpus before full conversion: CST theory, dialog documentation, API/code, linked/merged topics, equation-heavy pages, plus a born-digital paper, a multi-column paper, and a scanned or difficult PDF.

Validate code preservation, table structure, equation references, image presence, anchor resolution, source citations, and PDF reading order. Compare output against the originals, not merely against a second automated conversion.

Build a benchmark of real queries: exact API lookup, solver limitation, UI option, terminology mismatch, theory equation, crosslink-following, and whitepaper lookup. Assess retrieval rank and whether the returned context supports a correct answer. Set numerical targets after measuring the baseline.

The report should count discovered/converted/skipped/failed documents, metadata extraction coverage, unresolved links, missing assets, OCR successes/failures, unverified formulas, and extraction anomalies. Define which errors block activation and which are explicit warnings.

POC success means an agent can find a relevant source, read it with provenance, follow a crosslink, and inspect an equation image or PDF page; rerunning the build reuses unchanged expensive work; replacing a collection removes obsolete content.

## 13. Questions for grilling-with-docs

Use the actual skill instructions in the repository. These questions are preparation, not a replacement for that workflow.

1. What is the real CST corpus layout and version? Are all modules RoboHelp, or are there Sphinx/other HTML systems too?
2. Which representative files demonstrate the hardest extraction cases, including JS-backed hidden content?
3. Which RoboHelp metadata files exist, and what useful author-supplied information do they contain?
4. What corpus size, PDF count, build time, storage budget, OS, and GPU environment should be supported?
5. Is a portable output bundle required, or may it depend on the installed CST directory and original PDF folder?
6. How should source/version identity work when files move or topics are renamed between releases?
7. Should multiple CST versions coexist, and what is the default version filter?
8. Is Docling sufficiently accurate on these PDFs? How does Pix2Text perform on actual CST formula images?
9. Which mathematical mistakes are unacceptable, and how much manual review is realistic?
10. Should all images be enriched at build time, only equation candidates, or only a selected subset?
11. How are manual corrections represented and carried forward without applying stale fixes?
12. What exact-identifier search behavior is required beyond FTS5 tokenization?
13. What client-specific constraints exist for MCP images, response lengths, and local path access?
14. Which dependencies/models have compatible installation, licenses, and offline behavior for the intended use?
15. What constitutes a failed build, and how are partial results distinguished from validated output?
16. What evidence would justify semantic retrieval, reranking, or more sophisticated document linking?

## 14. Suggested implementation sequence

1. Inspect corpus samples and repository conventions; settle identity/provenance schema.
2. Prototype HTML extraction, RoboHelp metadata, and two-pass link resolution.
3. Prototype PDF extraction and equation OCR; compare fidelity on hard cases.
4. Produce a unified Markdown/metadata/assets output with a validation report.
5. Add SQLite search and a CLI; evaluate representative queries.
6. Add the thin MCP server and verify text/image retrieval in target agents.
7. Add cache/resume behavior and safe collection replacement; run the full corpus.
8. Revisit optional enhancements based on observed failures.

## 15. Starting documentation references

These support candidate choices, not evidence that they work on the unseen CST corpus. Recheck current APIs and versions during implementation.

- markdownify: https://github.com/matthewwithanm/python-markdownify
- Docling pipeline options, including formula enrichment: https://docling-project.github.io/docling/reference/pipeline_options/
- Pix2Text: https://github.com/breezedeus/Pix2Text
- SQLite FTS5: https://sqlite.org/fts5.html
- Official MCP Python SDK: https://py.sdk.modelcontextprotocol.io/
- Adobe RoboHelp author-defined index: https://helpx.adobe.com/robohelp/using/index.html
- Adobe older WebHelp search data example: https://helpx.adobe.com/be_en/robohelp/kb/controlling-which-topics-appear-search.html
- Claude Code MCP: https://code.claude.com/docs/en/mcp
- Cursor MCP: https://cursor.com/docs/mcp

The RoboHelp search-runtime wrapper was considered and deliberately set aside in favor of an independent Markdown corpus. Its exported metadata remains valuable input.
