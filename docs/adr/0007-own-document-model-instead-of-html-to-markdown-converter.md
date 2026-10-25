# Readers build our own Document model; no generic HTML-to-Markdown converter

**Amended by ADR 0014.** The model is no longer persisted beside the pages; a build re-parses. The reader decisions stand.

CST's help markup cannot be trusted structurally: `<h3>` holds prose, VBA headings exist only as CSS classes, code is one `<p>` per line, notes have no markup, and each generator (RoboHelp, Sphinx, PDF) delimits content differently. A generic converter such as markdownify or pandoc would need so many overrides that we would own the conversion anyway (and pandoc's executable is GPL). Instead, a reader per source format parses into our own Document model of typed blocks (heading, paragraph, list, field definition, code, table, equation, figure, API signature), using a per-project map from CSS class to meaning. The Markdown files and the search records are both rendered from that model and never from the raw HTML, so the two views cannot disagree (ADR 0003). The parsed model is persisted so rendering can change without re-parsing. Tables with merged cells stay as HTML inside the Markdown.

## Considered Options

- markdownify with custom converters: workable for clean HTML, but most of CST's semantics would live in overrides anyway.
- pandoc: the best MathJax handling, but an external GPL binary, and its Lua filters would be a second place where structure is interpreted.
