# Generated Guides are allowed, but authored outside the build and checked against the documentation

**Amended by ADR 0014.** The authoring session works from the folder with file tools; Guides are Markdown in the workspace's `guides/` folder, listed in `AGENTS.md`, and `validate` checks their Locator links. There is no Guides Collection.

The brainstorm ruled out LLM-written content so that agents receive vendor evidence, not paraphrase. But the patterns agents most need for VBA and Python (history-command anatomy, Result Template structure, `cst.interface` sessions) are spread over hundreds of pages and Library files, and no single page states them. We therefore allow Guides: generated Documents that summarise such patterns, always marked as generated and citing the Locators they draw on.

To keep builds local and deterministic, the tool contains no LLM client. Guides are written once per Release by an agent session working inside the Knowledge Base workspace (ADR 0013) through its own MCP server. Skills shipped in this repo guide that session, one per Guide topic family, and every assembly copies them into the workspace's `.claude/skills/` and `.agents/skills/`. The session saves drafts as Markdown under `work/guides/<release>/`, which a build ingests like any other Source. Each Guide set forms its own Collection tied to its Release (for example `cst-2024-guides`). On ingestion, every cited Locator must exist, and every identifier in a Guide's code must resolve to an API Entry or a known Undocumented Member, or the Guide is flagged. Guides get no ranking boost, and agents are told to verify details in the cited sources. Because they derive from licensed material, Guides stay private like the Knowledge Base (ADR 0001); only the skills are committed.

## Considered Options

- No generated content at all: keeps purity, but leaves agents to rediscover the same idioms in every session.
- Generating summaries inside `cst-help build` through an LLM API: makes builds cloud-dependent, non-deterministic and costly to repeat.
