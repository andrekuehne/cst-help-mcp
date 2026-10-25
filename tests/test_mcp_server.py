"""The `cst-help` MCP server's contract, checked through the SDK's in-memory client."""

from __future__ import annotations

import base64
import io
import json
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from kb_helpers import SOLVER_HF
from mcp import Client, StdioServerParameters
from PIL import Image

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


async def test_exposes_its_tools_with_their_parameters(client: Client) -> None:
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == {
        "cst_help_lookup",
        "cst_help_search",
        "cst_help_browse",
        "cst_help_read",
        "cst_help_images",
    }
    images: dict[str, Any] = tools["cst_help_images"].input_schema
    assert set(images["properties"]) == {"locator", "assets", "neighbours", "include_icons"}
    assert images.get("required", []) == []
    lookup: dict[str, Any] = tools["cst_help_lookup"].input_schema
    assert set(lookup["properties"]) == {"name", "area"}
    assert lookup["required"] == ["name"]
    search: dict[str, Any] = tools["cst_help_search"].input_schema
    assert set(search["properties"]) == {"query", "areas", "kind", "limit"}
    assert search["required"] == ["query"]
    assert search["properties"]["limit"]["maximum"] == 10
    browse: dict[str, Any] = tools["cst_help_browse"].input_schema
    assert set(browse["properties"]) == {"path", "tree"}
    assert browse.get("required", []) == []
    read: dict[str, Any] = tools["cst_help_read"].input_schema
    assert set(read["properties"]) == {"locator", "cursor"}
    assert read["required"] == ["locator"]


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


async def test_search_names_each_hits_area_and_kind_and_narrows_by_kind(client: Client) -> None:
    text, is_error = await _call(
        client, "cst_help_search", {"query": "Solver.FrequencyRange", "kind": "prose"}
    )
    nothing, _ = await _call(client, "cst_help_search", {"query": "Solver.FrequencyRange", "kind": "code"})

    assert not is_error
    assert "## Solver Object  [vba-3d, topic, Release 2024]" in text
    assert nothing.startswith("No hits")


SOLVER_BOOK = "Automation and Scripting > Visual Basic (VBA) > 3D Simulation VBA > VBA Objects > Solver"


async def test_browse_lists_the_entries_of_a_book_with_their_locators(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_browse", {"path": f"{SOLVER_BOOK} > high frequency"})

    assert not is_error
    assert text.startswith(f"Table of contents > {SOLVER_BOOK} > High Frequency, Release 2024:")
    assert f"- Solver (HF)\n  Locator: {SOLVER_HF}\n" in text


async def test_browse_shows_books_with_the_number_of_entries_below_them(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_browse", {"path": SOLVER_BOOK})

    assert not is_error
    assert "\n- High Frequency (5 entries below)\n" in text


async def test_browsing_the_whole_keyword_index_stays_within_budget(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_browse", {"tree": "keywords"})

    assert not is_error
    assert text.startswith("Keyword index, Release 2024:")
    assert "more not shown" in text
    assert _max_tokens(text) < 10_000


async def test_browsing_a_keyword_lists_its_topics(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_browse", {"path": "Solver Object", "tree": "keywords"})

    assert not is_error
    assert f"- Solver Object\n  Locator: {SOLVER_HF}" in text


async def test_browsing_an_unknown_entry_is_a_clear_error(client: Client) -> None:
    text, is_error = await _call(client, "cst_help_browse", {"path": "Automation and Scriptin"})

    assert is_error
    assert "No entry 'Automation and Scriptin' at the top level" in text
    assert "nearest: Automation and Scripting" in text


async def test_read_returns_a_sections_markdown_exactly_with_its_links(
    client: Client, kb: KnowledgeBase
) -> None:
    text, is_error = await _call(client, "cst_help_read", {"locator": f"{SOLVER_HF}#solver"})

    assert not is_error
    assert text.startswith(
        f"Solver Object  [vba-3d, Release 2024, page 1 of 1]\nLocator: {SOLVER_HF}#solver\n"
    )
    assert kb.read(f"{SOLVER_HF}#solver").text in text
    assert (
        "- FDSolver Object -> vba_3d/special_vbasolver/special_vbasolver_fdsolver_object.htm.md (resolved)"
        in text
    )
    assert "cursor" not in text


async def test_read_pages_a_long_document_within_budget_and_gives_the_cursor(client: Client) -> None:
    first, _ = await _call(client, "cst_help_read", {"locator": SOLVER_HF})
    second, is_error = await _call(client, "cst_help_read", {"locator": SOLVER_HF, "cursor": "2"})

    assert not is_error
    assert "page 1 of " in first and "page 2 of " in second
    assert 'call cst_help_read again with cursor "2"' in first
    assert _max_tokens(first) < 10_000 and _max_tokens(second) < 10_000


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"locator": "vba_3d/invented.md"}, "No Document 'vba_3d/invented.md' in Release 2024"),
        ({"locator": SOLVER_HF, "cursor": "99"}, "Cursor '99' is no page of"),
        ({"locator": "../../active.json"}, "No Document '../../active.json'"),
    ],
)
async def test_reading_an_unknown_locator_or_cursor_is_a_clear_error(
    client: Client, arguments: dict[str, Any], message: str
) -> None:
    text, is_error = await _call(client, "cst_help_read", arguments)

    assert is_error
    assert message in text


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
    assert "cst_help_read" in instructions
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


async def test_an_opt_in_query_log_records_each_search_and_lookup(kb: KnowledgeBase, tmp_path: Path) -> None:
    log = tmp_path / "logs" / "queries.jsonl"

    async with Client(create_server(kb, query_log=log)) as logged:
        found, _ = await _call(
            logged, "cst_help_search", {"query": "frequency range", "areas": ["vba-3d"], "limit": 3}
        )
        looked_up, _ = await _call(logged, "cst_help_lookup", {"name": "Solver.FrequencyRange"})

    search, lookup = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert (search["tool"], search["query"], search["areas"], search["kind"]) == (
        "cst_help_search",
        "frequency range",
        ["vba-3d"],
        "all",
    )
    assert search["locators"] == _locators(found) and len(search["locators"]) == 3
    assert (lookup["tool"], lookup["name"], lookup["area"]) == (
        "cst_help_lookup",
        "Solver.FrequencyRange",
        None,
    )
    assert lookup["locators"] == _locators(looked_up)
    assert search["release"] == "2024" and "time" in search


async def test_cst_help_serve_writes_the_query_log_it_is_given(vba_kb: Path, tmp_path: Path) -> None:
    log = tmp_path / "queries.jsonl"
    command = "import sys; from cst_help_mcp.cli import main; sys.exit(main())"
    params = StdioServerParameters(
        command=sys.executable, args=["-c", command, "serve", "--kb", str(vba_kb), "--query-log", str(log)]
    )

    async with Client(params) as stdio_client:
        _, is_error = await _call(stdio_client, "cst_help_search", {"query": "MeshProp"})

    assert not is_error
    assert json.loads(log.read_text(encoding="utf-8"))["query"] == "MeshProp"


def _locators(text: str) -> list[str]:
    return [line.removeprefix("Locator: ") for line in text.splitlines() if line.startswith("Locator: ")]


WHICH_SOLVER = "3d/special_overview/special_overview_whichsolver.htm.md#CST_MICROWAVE_STUDIO_"


@pytest.fixture
async def prose_client(prose_kb: KnowledgeBase) -> AsyncIterator[Client]:
    async with Client(create_server(prose_kb)) as connected:
        yield connected


async def test_images_returns_a_sections_figures_as_png_image_content_with_captions(
    prose_client: Client,
) -> None:
    result = await prose_client.call_tool("cst_help_images", {"locator": WHICH_SOLVER})

    assert not result.is_error
    [text] = [block.text for block in result.content if block.type == "text"]
    [image] = [block for block in result.content if block.type == "image"]
    assert image.mime_type == "image/png"
    with Image.open(io.BytesIO(base64.b64decode(image.data))) as png:
        assert (png.format, png.size) == ("PNG", (502, 314))
    assert "(figure, 502x314)" in text
    assert WHICH_SOLVER in text


async def test_images_returns_at_most_four_and_names_the_ones_left_out(prose_client: Client) -> None:
    result = await prose_client.call_tool("cst_help_images", {"locator": WHICH_SOLVER, "include_icons": True})

    text = "\n".join(block.text for block in result.content if block.type == "text")
    assert [block.type for block in result.content].count("image") == 4
    assert "solver transient icon" in text
    assert "more not shown" in text and "(figure, 502x314)" in text


async def test_images_of_an_unknown_asset_is_a_clear_error(prose_client: Client) -> None:
    text, is_error = await _call(prose_client, "cst_help_images", {"assets": ["0123456789ab"]})

    assert is_error
    assert "No Asset '0123456789ab' in Release 2024" in text
