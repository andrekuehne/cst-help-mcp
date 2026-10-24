"""Search ranking (ADR 0008): exact API Entries first, then weighted words, then partial identifiers."""

from __future__ import annotations

from typing import get_args

import pytest
from kb_helpers import BENCHMARK, SOLVER_HF

from cst_help_mcp.benchmark import Benchmark, Question, Report, load_benchmark, run_benchmark
from cst_help_mcp.retrieval import Fusion, KnowledgeBase, Ranking

SOLID = "vba_3d/common_vbasolido/common_vbasolido_solid_object.htm.md"


def test_a_partial_identifier_matches_through_the_trigram_index(kb: KnowledgeBase) -> None:
    hits = kb.search("MeshProp")

    assert f"{SOLID}#setmeshproperties" in [h.locator for h in hits[:5]]


def test_an_identifier_in_the_query_puts_its_api_entries_first(kb: KnowledgeBase) -> None:
    hits = kb.search("set the solver frequency range with Solver.FrequencyRange to 1-10 GHz")

    assert hits[0].locator == f"{SOLVER_HF}#frequencyrange"


def test_a_bare_member_name_puts_every_api_entry_of_that_name_first(kb: KnowledgeBase) -> None:
    entries = {h.locator for h in kb.lookup("FrequencyRange")}

    hits = kb.search("which monitor settings take a FrequencyRange")

    assert len(entries) > 1
    assert {h.locator for h in hits[: len(entries)]} == entries


def test_an_author_keyword_finds_the_topic_it_names(prose_kb: KnowledgeBase) -> None:
    hits = prose_kb.search("advancing front mesher")

    # The topic's title, "Special Mesh Properties - Legacy Tetrahedral - Volume", says none of it.
    assert hits[0].locator.startswith("3d/common_mesh/common_mesh_tetvolume.htm.md")


def test_hits_can_be_narrowed_to_prose_or_code(kb: KnowledgeBase) -> None:
    every = kb.search("frequency range", kind="all")

    assert [h.locator for h in kb.search("frequency range", kind="prose")] == [h.locator for h in every]
    # Every help topic is prose; code comes with the Library.
    assert kb.search("frequency range", kind="code") == []


def test_each_hit_names_its_kind_and_whether_it_is_generated_or_heuristic(kb: KnowledgeBase) -> None:
    hit = kb.search("Solver.FrequencyRange")[0]

    assert (hit.locator, hit.release, hit.area, hit.kind) == (
        f"{SOLVER_HF}#frequencyrange",
        "2024",
        "vba-3d",
        "topic",
    )
    assert hit.title == "Solver Object"
    assert hit.heading_path.endswith("FrequencyRange")
    assert hit.snippet.startswith("FrequencyRange ( double fmin, double fmax )")
    assert (hit.generated, hit.heuristic) == (False, False)


@pytest.mark.parametrize(
    "query",
    [
        'Left$("a.b", 2)',
        "Solver.FrequencyRange(",
        '\'#include "lib.bas"',
        "a.b.c.",
        'NEAR(Mesh*Prop) "',
        "^-+:",
    ],
)
def test_punctuation_in_a_query_never_causes_an_error(kb: KnowledgeBase, query: str) -> None:
    assert isinstance(kb.search(query), list)


# The benchmark questions with recorded ranks: ticket 06's solver and how-to questions.
TRACKED = [q for q in load_benchmark(BENCHMARK).questions if q.baseline]


@pytest.fixture(scope="module")
def tracked_report(release_kb: KnowledgeBase) -> Report:
    return run_benchmark(release_kb, Benchmark(load_benchmark(BENCHMARK).categories, TRACKED))


@pytest.mark.parametrize("question", TRACKED, ids=lambda q: q.id)
def test_benchmark_questions_keep_their_newest_recorded_ranks(
    tracked_report: Report, question: Question
) -> None:
    assert question.baseline
    newest, kept = list(question.baseline.items())[-1]
    ranks = (
        tracked_report.rank(question.id, filtered=False),
        tracked_report.rank(question.id, filtered=True),
    )

    worse = [got for got, rank in zip(ranks, kept, strict=True) if (got or 6) > (rank or 6)]
    assert not worse, f"{question.id} ranks {ranks} (all, {', '.join(question.areas)}); {newest} {kept}"


def test_field_weights_can_be_overridden_without_editing_code(prose_kb: KnowledgeBase) -> None:
    without_keywords = Ranking(keywords=0.0, toc_paths=0.0)

    hits = prose_kb.search("advancing front mesher", ranking=without_keywords)

    # Only the author keyword names the topic (test_an_author_keyword_finds_the_topic_it_names).
    assert not hits or not hits[0].locator.startswith("3d/common_mesh/common_mesh_tetvolume.htm.md")


@pytest.mark.parametrize("fusion", get_args(Fusion))
def test_section_and_document_scores_can_be_put_on_one_scale(prose_kb: KnowledgeBase, fusion: Fusion) -> None:
    hits = prose_kb.search("advancing front mesher", ranking=Ranking(fusion=fusion))

    assert "3d/common_mesh/common_mesh_tetvolume.htm.md" in [h.locator.partition("#")[0] for h in hits[:5]]
