"""Search ranking (ADR 0008): exact API Entries first, then weighted words, then partial identifiers."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from kb_helpers import SOLVER_HF

from cst_help_mcp.locator import locator_for
from cst_help_mcp.retrieval import KnowledgeBase

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


@dataclass(frozen=True)
class Question:
    """A solver or how-to question of the benchmark (docs/benchmark-draft.md), until ticket 07 makes
    the whole benchmark machine-readable."""

    id: str
    text: str
    area: str
    sources: tuple[str, ...]  # the expected Documents' source paths
    # The rank (1 to 5) of the best expected source among the hits, unfiltered and filtered to the
    # Area, or None for a miss: before ticket 06, and as search must keep it now.
    before: tuple[int | None, int | None]
    now: tuple[int | None, int | None]


_3D = "Online Help/mergedProjects/3D"
_VBA = "Online Help/mergedProjects/VBA_3D"
QUESTIONS = [
    Question(
        "SOL-01",
        "What does the time domain solver's Accuracy of -40 dB actually control, and how do I set it to "
        "-50 dB in VBA?",
        "3d",
        (
            f"{_3D}/special_solvopt/special_solvopt_solver.htm",
            f"{_VBA}/special_vbasolver/special_vbasolver_solver_object.htm",
        ),
        before=(2, None),
        now=(2, None),
    ),
    Question(
        "SOL-02",
        "How do I run the integral equation solver from a macro? Is there an IESolver.Start, or does it go "
        "through FDSolver?",
        "vba-3d",
        (
            f"{_VBA}/special_vbasolver/special_vbasolver_fdsolver_object.htm",
            f"{_VBA}/special_vbasolver/special_vbasolver_iesolver_object.htm",
            f"{_VBA}/common_vbaapp/common_vbaappapplication_object.htm",
        ),
        before=(1, 1),
        now=(1, 1),
    ),
    Question(
        "SOL-03",
        "Can the eigenmode solver handle open boundaries and lossy, dispersive materials, or only closed, "
        "lossless cavities?",
        "3d",
        (f"{_3D}/special_overview/special_overview_eigenmodesolverover.htm",),
        before=(4, 3),
        now=(3, 2),
    ),
    Question(
        "SOL-04",
        "My high-Q filter takes forever in the time domain solver. How do I switch on the AR filter from VBA?",
        "vba-3d",
        (
            f"{_VBA}/special_vbasolver/special_vbasolver_solver_object.htm",
            f"{_3D}/special_overview/special_overview_arfilterover.htm",
            f"{_3D}/common_overview/common_overview_problems_transient_solver.htm",
        ),
        before=(1, 1),
        now=(3, 1),
    ),
    Question(
        "HOW-01",
        "In the discrete port dialog, what's the difference between the S-parameter, voltage and current port "
        "types, and what does the impedance field do?",
        "3d",
        (
            f"{_3D}/special_solvopt/special_solvopt_discreteports.htm",
            f"{_3D}/special_overview/special_overview_discrete_port_overview.htm",
        ),
        before=(1, 1),
        now=(1, 1),
    ),
    Question(
        "HOW-02",
        "For an antenna model, which boundary setting adds free space for the farfield, and how does it "
        "combine with the extra space in the background settings?",
        "3d",
        (
            f"{_3D}/special_solvopt/special_solvopt_boundary_conditions_boundaries.htm",
            f"{_3D}/common_general/common_general_background.htm",
        ),
        before=(5, 5),
        now=(4, 4),
    ),
    Question(
        "HOW-03",
        "If I put two parameters into one sequence of the Parameter Sweep dialog, do I get every combination? "
        "How do I sweep them one after the other instead?",
        "3d",
        (
            f"{_3D}/special_process/special_solvopt_parametersweep.htm",
            f"{_3D}/special_process/special_solvopt_parametersweeppar.htm",
        ),
        before=(1, 1),
        now=(1, 1),
    ),
    Question(
        "HOW-04",
        "How do I temporarily switch off a step in the history list without deleting it?",
        "3d",
        (f"{_3D}/common_macro/common_macro_history_list.htm",),
        before=(3, 3),
        now=(1, 1),
    ),
]


def _rank(kb: KnowledgeBase, question: Question, areas: list[str] | None) -> int | None:
    expected = {locator_for(source) for source in question.sources}
    hits = kb.search(question.text, areas=areas)
    return next((i for i, h in enumerate(hits[:5], 1) if h.locator.partition("#")[0] in expected), None)


@pytest.mark.parametrize("question", QUESTIONS, ids=lambda q: q.id)
def test_benchmark_questions_keep_their_ranks(release_kb: KnowledgeBase, question: Question) -> None:
    ranks = (_rank(release_kb, question, None), _rank(release_kb, question, [question.area]))

    worse = [got for got, kept in zip(ranks, question.now, strict=True) if (got or 6) > (kept or 6)]
    assert not worse, (
        f"{question.id} ranks {ranks} (unfiltered, {question.area}); now {question.now}, before 06 {question.before}"
    )
