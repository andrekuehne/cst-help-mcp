"""Reading a Section or a Document by its Locator, through the retrieval core."""

from __future__ import annotations

from pathlib import Path

import pytest
from kb_helpers import SOLVER_HF, topic, write_config, write_release

from cst_help_mcp.build import build_collection
from cst_help_mcp.errors import KnowledgeBaseError
from cst_help_mcp.reading import PageLink
from cst_help_mcp.retrieval import KnowledgeBase

IMPORT_DATA = "vba_3d/common_vbacablestudio/data_import/import_data.htm.md"
NFS = "vba_3d/common_vbaimpexp/common_vbaimpexp_nfs.htm.md"


def _file(kb: KnowledgeBase, locator: str) -> str:
    """The Markdown file of a Document of the VBA test Collection, exactly as written."""
    return (kb.path / "cst-2024" / locator).read_text(encoding="utf-8", newline="")


def test_reading_a_locator_with_an_anchor_returns_that_section(kb: KnowledgeBase) -> None:
    page = kb.read(f"{SOLVER_HF}#frequencyrange")

    assert page.text.startswith('<a id="frequencyrange"></a>\n### FrequencyRange\n')
    assert "FrequencyRange ( double fmin, double fmax )" in page.text
    assert "Sets the frequency range for the simulation." in page.text
    assert "CalculateZandYMatrices" not in page.text
    assert page.text in _file(kb, SOLVER_HF)
    assert (page.locator, page.release, page.title) == (
        f"{SOLVER_HF}#frequencyrange",
        "2024",
        "Solver Object",
    )
    assert page.next_cursor is None


def test_reading_a_locator_without_an_anchor_returns_the_document_in_pages(kb: KnowledgeBase) -> None:
    pages = [kb.read(SOLVER_HF)]
    while (cursor := pages[-1].next_cursor) is not None:
        pages.append(kb.read(SOLVER_HF, cursor=cursor))

    assert "".join(page.text for page in pages) == _file(kb, SOLVER_HF)
    assert pages[0].text.startswith('---\nrelease: "2024"\n')
    assert [(page.page, page.pages) for page in pages] == [(n, len(pages)) for n in range(1, len(pages) + 1)]
    assert len(pages) >= 3  # the file holds about 68,000 characters
    # About 8,000 tokens, at a pessimistic three characters per token, with the list of links.
    assert all(len(page.text) + sum(len(str(link)) for link in page.links) <= 24_000 for page in pages)
    assert all(page.text.endswith("\n") for page in pages)


def test_a_page_lists_the_outgoing_links_its_text_shows_with_their_status(kb: KnowledgeBase) -> None:
    section = kb.read(f"{SOLVER_HF}#solver")
    external = kb.read(IMPORT_DATA)
    outside = kb.read(NFS)

    assert section.links == [
        PageLink(
            "FDSolver Object", "resolved", "vba_3d/special_vbasolver/special_vbasolver_fdsolver_object.htm.md"
        ),
        PageLink(
            "EigenmodeSolver Object",
            "resolved",
            "vba_3d/special_vbasolver/special_vbasolver_eigenmodesolver_object.htm.md",
        ),
    ]
    assert external.links[0] == PageLink(
        "Harness Description List", "external", "https://ecad-wiki.prostep.org/specifications/kbl/"
    )
    assert (
        PageLink("here", "outside", "Online Help/mergedProjects/3D/example_files/nfs_example_files.zip")
        in outside.links
    )


def test_a_link_to_a_file_the_release_folder_lacks_is_listed_as_unresolved(tmp_path: Path) -> None:
    page = topic("Widget", "Spin", 'Spins it; see <a href="../videos/spin.htm">the [spin] video</a>.')
    release = write_release(tmp_path / "release", {"widgets/widget.htm": page})
    build_collection(write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, []), "cst-2024")

    with KnowledgeBase.open(tmp_path / "kb") as kb:
        read = kb.read("vba_3d/widgets/widget.htm.md")

    assert read.links == [
        PageLink("the [spin] video", "unresolved", "Online Help/mergedProjects/VBA_3D/videos/spin.htm")
    ]


def test_an_alias_locator_reads_the_document_it_is_an_alias_of(prose_kb: KnowledgeBase) -> None:
    page = prose_kb.read("3d/common_ribbons/3d/common_ribbons_modeling.htm.md")

    assert page.locator == "ribbons/3d/common_ribbons_modeling.htm.md"
    assert page.source_path == "Online Help/ribbons/3d/common_ribbons_modeling.htm"


def test_an_unknown_locator_is_a_clear_error(kb: KnowledgeBase) -> None:
    with pytest.raises(KnowledgeBaseError, match=r"No Document 'vba_3d/invented\.md' in Release 2024"):
        kb.read("vba_3d/invented.md")
    with pytest.raises(
        KnowledgeBaseError, match=rf"{SOLVER_HF} has no Section 'frequencyrang'.*#frequencyrange"
    ):
        kb.read(f"{SOLVER_HF}#frequencyrang")
    with pytest.raises(KnowledgeBaseError, match=r"Cursor '9' is no page of .*, which has 1 page"):
        kb.read(f"{SOLVER_HF}#frequencyrange", cursor="9")


def test_a_block_longer_than_a_page_is_split_across_pages_with_room_for_its_links(tmp_path: Path) -> None:
    lines = "<br/>".join(
        f'Line {n} of a very long description, see <a href="https://example.com/{n}">note {n}</a>.'
        if n % 10 == 0
        else f"Line {n} of a very long description."
        for n in range(3_000)
    )
    release = write_release(tmp_path / "release", {"widgets/widget.htm": topic("Widget", "Spin", lines)})
    build_collection(write_config(tmp_path / "cst-help.toml", tmp_path / "kb", release, []), "cst-2024")
    locator = "vba_3d/widgets/widget.htm.md"

    with KnowledgeBase.open(tmp_path / "kb") as kb:
        pages = [kb.read(locator)]
        while (cursor := pages[-1].next_cursor) is not None:
            pages.append(kb.read(locator, cursor=cursor))
        file = (kb.path / "cst-2024" / locator).read_text(encoding="utf-8", newline="")

    assert len(file) > 100_000
    assert "".join(page.text for page in pages) == file
    assert max(len(page.links) for page in pages) > 100
    assert all(len(page.text) + sum(len(str(link)) for link in page.links) <= 24_000 for page in pages)
