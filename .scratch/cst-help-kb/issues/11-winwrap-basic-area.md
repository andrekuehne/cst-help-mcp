# 11: WinWrap Basic Area

**What to build:** The WinWrap Basic language reference becomes Area `winwrap-basic`. Its keywords and built-in functions become API Entries under their names as written, such as `Left$`, so the macro language can be checked as well as the CST objects.

**Blocked by:** 01

**Status:** done

- [x] Every language reference page becomes a Document, with its syntax, group and description as structured blocks.
- [x] Code examples whose keywords are hyperlinks render as code without losing their line breaks.
- [x] Keywords are API Entries, listed in `api.md` as written.
- [x] API-06 and API-07 reach their pages in the agent run.

## Comments

**2026-10-25.** Implemented in `cfa10a3`: a reader of its own, `winwrap.py`, since the pages have no class markup for a Profile. All 315 pages build, 246 of them with an API Entry named from the heading without its kind (`Dir$ Function` → `Dir$`). Group pages and the definitions of syntax terms (`str definition`) get none. Covered by `tests/test_winwrap_basic.py` (103 tests pass in all).

Agent run from a fresh build of the development `.kb` (1,829 Documents, `validate` clean), Claude Code 2.1.310 with `--model sonnet`, Read/Grep/Glob only, scored by `scripts/agent-run.py --only API-06,API-07`: API-06 first expected read at call 4 of 7, API-07 at call 2 of 2; PASS. On Windows the agent command needs its full path (`C:/nvm4w/nodejs/claude.cmd`); `subprocess` does not find `claude` by name.

Decisions for later tickets:

- **List residue.** Word's import turned lines starting with `v`, `q` or `*` into bullets, eating that character, and a leading number into an `<ol start>`. The reader reads list items back as lines and restores the character (`vbOK 1 OK button`); a bare constant and the numbered value split from it are rejoined. Some values stay lossy in the source (`vbDefaultButton2 100`, which is `&H100`).
- **Operators.** `ww_00179` documents every operator on one page and gets no API Entry; `AGENTS.md` says so. Only `Is` and `Like` have pages and entries of their own.
- **`Print #`.** The benchmark's `api_entries` for API-06 names `Print #`; the entry is `Print`, whose signature `Print #StreamNum, ...` holds the text.
- **Rendering.** A paragraph line that Markdown would read as a list, heading or quote marker is now escaped in every Area (WinWrap's unary minus `- n1`).
- **validate** ignores inline code spans when it collects link targets.
- **GLOSSARY.md**: API Entry now covers WinWrap Basic keywords and built-ins.
