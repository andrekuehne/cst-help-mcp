"""The read-only `cst-help` MCP server: its tools wrap the retrieval core one to one."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from cst_help_mcp.errors import CstHelpError
from cst_help_mcp.model import NavTree
from cst_help_mcp.retrieval import MAX_HITS, BrowseEntry, KnowledgeBase, SearchKind

# Budgets are counted in characters at a pessimistic three characters per token.
CHARS_PER_TOKEN = 3
RESPONSE_BUDGET = 9_000 * CHARS_PER_TOKEN  # under the 10,000-token limit for every response
SEARCH_BUDGET = 3_000 * CHARS_PER_TOKEN  # about 3,000 tokens for a page of ten hits


def server_instructions(kb: KnowledgeBase) -> str:
    """The server's instructions, also printed as the AGENTS.md section for a project.

    The first 512 characters stand on their own, since a client may show no more.
    """
    routing = (
        f"CST Studio Suite help, Release {kb.release}. "
        "For an identifier (VBA Object.Member, a bare method or object name) or a Display Name, "
        "call cst_help_lookup first. For a concept or a how-to question, call cst_help_search. "
        f"Cite the Locator and Release {kb.release} of every result you rely on."
    )
    return (
        f"{routing}\n\n"
        "If cst_help_lookup says an identifier is not documented and cst_help_search finds nothing "
        "either, tell the user so and do not invent the method, its arguments or its behaviour.\n\n"
        "To explore a subject systematically, call cst_help_browse on the table of contents "
        "or the author keyword index.\n\n"
        f"{_incompleteness(kb)}"
        f"Every Locator is a path relative to the Knowledge Base folder {kb.path.resolve()}, "
        "so an agent with file access can open or grep the same Markdown there."
    )


def _incompleteness(kb: KnowledgeBase) -> str:
    if not kb.incomplete:
        return ""
    lost = "; ".join(
        f"{n} Document{'s' if n != 1 else ''} of Collection {c} failed to build"
        for c, n in kb.incomplete.items()
    )
    return (
        f"This Knowledge Base is incomplete: {lost}. A 'not documented' answer may come from a Document "
        "that failed, so tell the user when you rely on one.\n\n"
    )


def create_server(kb: KnowledgeBase) -> MCPServer:
    server = MCPServer("cst-help", instructions=server_instructions(kb))

    @server.tool(name="cst_help_lookup", structured_output=False)
    async def lookup(
        name: Annotated[str, Field(description="Object.Member, a bare member or an object name")],
        area: Annotated[str | None, Field(description="limit to one Area, such as vba-3d")] = None,
    ) -> str:
        """Look up documented API Entries by exact name; case is ignored."""
        with _reported_as_tool_errors():
            hits = kb.lookup(name, area=area)
        if not hits:
            return f"{name}: not documented in Release {kb.release}."
        return _within_budget(
            f"{len(hits)} API Entries for {name} in Release {kb.release}:",
            (
                _item(
                    f"{hit.qualified_name}  [{hit.area}, Release {hit.release}]",
                    [hit.signature, hit.description],
                    hit.locator,
                )
                for hit in hits
            ),
            RESPONSE_BUDGET,
            "narrow the lookup with Object.Member or an Area",
        )

    @server.tool(name="cst_help_search", structured_output=False)
    async def search(
        query: Annotated[str, Field(description="plain words")],
        areas: Annotated[list[str] | None, Field(description="limit to these Areas")] = None,
        kind: Annotated[SearchKind, Field(description="explanations (prose), working code, or all")] = "all",
        limit: Annotated[int, Field(ge=1, le=MAX_HITS)] = MAX_HITS,
    ) -> str:
        """Search the help by plain words or partial names; returns ranked Sections with their Locators.

        API Entries named in the query come first.
        """
        with _reported_as_tool_errors():
            hits = kb.search(query, areas=areas, kind=kind, limit=limit)
        if not hits:
            return f"No hits for '{query}' in Release {kb.release}."
        return _within_budget(
            f"{len(hits)} hits for '{query}' in Release {kb.release}:",
            (
                _item(
                    f"{hit.title}  [{', '.join(hit.labels)}, Release {hit.release}]",
                    [hit.heading_path, hit.snippet],
                    hit.locator,
                )
                for hit in hits
            ),
            SEARCH_BUDGET,
            "use more specific words",
        )

    @server.tool(name="cst_help_browse", structured_output=False)
    async def browse(
        path: Annotated[
            str,
            Field(
                description='entry names joined by ">", such as "3D Simulation > Solvers"; empty for the top level'
            ),
        ] = "",
        tree: Annotated[
            NavTree, Field(description="the table of contents or the author keyword index")
        ] = "toc",
    ) -> str:
        """Browse the table of contents or the keyword index: the entries below a book or keyword."""
        with _reported_as_tool_errors():
            result = kb.browse(path, tree=tree)
        return _within_budget(
            f"{result.title}, Release {result.release}: {len(result.entries)} entries",
            (_entry(e) for e in result.entries),
            RESPONSE_BUDGET,
            "browse an entry by its path",
            separator="\n",
        )

    return server


@contextmanager
def _reported_as_tool_errors() -> Iterator[None]:
    """Turn a problem the agent can fix, such as an unknown Area, into a tool error with its message."""
    try:
        yield
    except CstHelpError as e:
        raise ToolError(str(e)) from e


def _item(heading: str, lines: list[str], locator: str) -> str:
    return "\n".join([f"## {heading}", *(line for line in lines if line), f"Locator: {locator}"])


def _entry(entry: BrowseEntry) -> str:
    locator = f"\n  Locator: {entry.locator}" if entry.locator else ""
    return f"- {entry}{locator}"


def _within_budget(
    header: str, items: Iterable[str], budget: int, advice: str, separator: str = "\n\n"
) -> str:
    """Join items under a header, leaving out whole items once the budget is reached."""
    parts = [header]
    size = len(header)
    left_out = 0
    for item in items:
        if left_out or size + len(item) + len(separator) > budget:
            left_out += 1
            continue
        parts.append(item)
        size += len(item) + len(separator)
    if left_out:
        parts.append(f"... {left_out} more not shown; {advice}.")
    return separator.join(parts)
