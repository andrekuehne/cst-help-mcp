"""The `cst-help` MCP server's contract, checked through the SDK's in-memory client."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from kb_helpers import SOLVER_HF
from mcp import Client, StdioServerParameters

from cst_help_mcp.build import build_collection
from cst_help_mcp.retrieval import KnowledgeBase
from cst_help_mcp.server import create_server

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _call(client: Client, tool: str, arguments: dict[str, Any]) -> tuple[str, bool]:
    result = await client.call_tool(tool, arguments)
    text = "\n".join(block.text for block in result.content if block.type == "text")
    return text, result.is_error


def _max_tokens(text: str) -> float:
    """A pessimistic token count: English help text runs nearer four characters per token."""
    return len(text) / 3


@pytest.fixture
async def client(kb: KnowledgeBase) -> AsyncIterator[Client]:
    async with Client(create_server(kb)) as connected:
        yield connected


async def test_exposes_lookup_and_search_with_their_parameters(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == {"cst_help_lookup", "cst_help_search"}
    lookup: dict[str, Any] = tools["cst_help_lookup"].input_schema
    assert set(lookup["properties"]) == {"name", "area"}
    assert lookup["required"] == ["name"]
    search: dict[str, Any] = tools["cst_help_search"].input_schema
    assert set(search["properties"]) == {"query", "areas", "limit"}
    assert search["required"] == ["query"]
    assert search["properties"]["limit"]["maximum"] == 10


async def test_lookup_returns_signature_description_locator_and_release(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_lookup", {"name": "solver.frequencyrange"})

    assert not is_error
    assert "Release 2024" in text
    assert "Solver.FrequencyRange" in text
    assert "FrequencyRange ( double fmin, double fmax )" in text
    assert "Sets the frequency range for the simulation." in text
    assert f"{SOLVER_HF}#frequencyrange" in text


async def test_lookup_of_an_unknown_name_says_not_documented(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_lookup", {"name": "Solver.InventedMethod"})

    assert not is_error
    assert text.startswith("Solver.InventedMethod: not documented in Release 2024")


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("cst_help_lookup", {"name": "Solver", "area": "no-such-area"}),
        ("cst_help_search", {"query": "solver", "areas": ["no-such-area"]}),
    ],
)
async def test_an_unknown_area_is_a_clear_error(client: Client, tool: str, arguments: dict[str, Any]) -> None:
    text, is_error = await _call(client, tool, arguments)

    assert is_error
    assert "Unknown Area 'no-such-area'" in text
    assert "vba-3d" in text


async def test_an_unknown_tool_is_a_clear_error(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_invented", {})

    assert is_error
    assert "cst_help_invented" in text


async def test_search_returns_at_most_ten_hits_naming_locator_and_release(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_search", {"query": "frequency range for the simulation"})

    assert not is_error
    assert f"{SOLVER_HF}#frequencyrange" in text
    assert text.count("Locator: ") == 10
    assert text.count("Release 2024") >= 10
    assert _max_tokens(text) <= 3_000


async def test_search_limit_above_ten_is_refused(client: Client) -> None:
    _, is_error = await _call(client, "cst_help_search", {"query": "solver", "limit": 50})

    assert is_error


async def test_a_lookup_with_hundreds_of_hits_stays_within_budget_and_says_what_was_left_out(
    client: Client,
) -> None:
    text, is_error = await _call(client, "cst_help_lookup", {"name": "Reset"})

    assert not is_error
    assert _max_tokens(text) < 10_000
    assert "249 API Entries for Reset" in text
    assert "more not shown" in text
    assert "Object.Member" in text


async def test_the_first_512_characters_of_the_instructions_route_and_cite(client: Client) -> None:
    head = (client.instructions or "")[:512]

    assert "cst_help_lookup" in head
    assert "Display Name" in head
    assert "cst_help_search" in head
    assert "Locator" in head
    assert "Release 2024" in head


async def test_the_instructions_give_the_not_documented_rule_and_the_knowledge_base_path(
    client: Client, kb: KnowledgeBase
) -> None:
    instructions = client.instructions or ""

    assert "not documented" in instructions
    assert str(kb.path.resolve()) in instructions


async def test_cst_help_serve_answers_over_stdio(vba_kb: Path) -> None:
    command = "import sys; from cst_help_mcp.cli import main; sys.exit(main())"
    params = StdioServerParameters(
        command=sys.executable, args=["-c", command, "serve", "--kb", str(vba_kb), "--release", "2024"]
    )

    async with Client(params) as stdio_client:
        text, is_error = await _call(stdio_client, "cst_help_lookup", {"name": "Solver.FrequencyRange"})

    assert not is_error
    assert f"{SOLVER_HF}#frequencyrange" in text


@pytest.fixture(scope="module")
def two_release_kb(corpus_2024: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A Knowledge Base holding the VBA solver pages twice, as Release 2024 and as Release 2025."""
    root = tmp_path_factory.mktemp("two-releases")
    collections = "".join(
        f"""
[collections.cst-{release}]
release = "{release}"

[[collections.cst-{release}.sources]]
type = "cst-release"
path = '{corpus_2024}'
include = ["Online Help/mergedProjects/VBA_3D/special_vbasolver/*"]
"""
        for release in ("2024", "2025")
    )
    config = root / "cst-help.toml"
    config.write_text(f"[knowledge_base]\npath = '{root / 'kb'}'\n{collections}", encoding="utf-8")
    build_collection(config, "cst-2024")
    build_collection(config, "cst-2025")
    return root / "kb"


@pytest.mark.parametrize(("release", "served"), [(None, "2025"), ("2024", "2024")])
async def test_a_server_answers_from_the_one_release_fixed_at_start(
    two_release_kb: Path, release: str | None, served: str
) -> None:
    with KnowledgeBase.open(two_release_kb, release) as kb:
        async with Client(create_server(kb)) as connected:
            text, _ = await _call(connected, "cst_help_lookup", {"name": "Solver.FrequencyRange"})
            hits, _ = await _call(connected, "cst_help_search", {"query": "frequency range"})

    other = "2024" if served == "2025" else "2025"
    assert text.startswith(f"1 API Entries for Solver.FrequencyRange in Release {served}:")
    assert f"Release {other}" not in text
    assert f"Release {served}" in hits
    assert f"Release {other}" not in hits
