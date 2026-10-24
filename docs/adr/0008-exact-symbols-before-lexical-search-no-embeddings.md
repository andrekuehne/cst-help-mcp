# Exact API lookup before lexical search; no embeddings until the benchmark asks for them

Most queries come from agents writing VBA or Python, so identifiers such as `Solver.FrequencyRange` must resolve exactly. SQLite FTS5 cannot do that alone: an unquoted dotted name is a syntax error, punctuation is dropped, and camelCase is not split. Search therefore consults an exact table of API Entries first (from Sphinx `objects.inv` and the VBA signature headings), then an FTS5 word index weighted towards titles, author keywords and table-of-contents paths, plus a trigram index for partial names. Raw queries are never passed to FTS5. All of it lives in SQLite from the Python standard library, so serving needs no search engine or model. Embeddings, hybrid ranking and reranking are added only if the query benchmark shows lexical search missing relevant Sections.

## Considered Options

- Hybrid vector and lexical search from the start (as in haiku.rag or qmd): heavier to install and serve, and no evidence yet that it is needed for this vocabulary.
- tantivy or bm25s: richer query parsing or speed, but a second store next to SQLite for no measured gain.
