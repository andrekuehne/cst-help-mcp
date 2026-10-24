# 04: RoboHelp prose topics for 3D Simulation and General

**What to build:** The `cst-release` Source also reads the 3D Simulation project and the root project's own subtrees (general features, user interface, ribbons, advanced, license, simulation acceleration) into Areas `3d` and `general`. Content comes through faithfully, without the navigation boilerplate, and links between topics work as Locators.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Topic content is taken from between the logo header and the footer. WebHelp shell pages, breadcrumb scripts, footers, logos and spacer paragraphs are dropped.
- [ ] The per-project map from CSS class to block role turns prose held in `<h3>` into paragraphs, dialog field lists into field definitions, and "Note:" paragraphs into notes.
- [ ] Simple tables render as Markdown tables. Tables with merged cells stay as HTML.
- [ ] Popup links become ordinary links, and commented-out content is dropped.
- [ ] Topics that appear in no table of contents are included.
- [ ] Topics published identically in several places become one Document, with the other paths as Aliases.
- [ ] Links are resolved in two passes, without regard to case, and rewritten as Locators. Each link is marked resolved, unresolved, external or outside the corpus, and the report lists the unresolved ones.
- [ ] Corpus tests check representative pages, such as the Brick dialog page and the polarization theory page, by their rendered Markdown and by search.
