"""The benchmark runner: the machine-readable benchmark, scored against a built Knowledge Base."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
from kb_helpers import BENCHMARK, SOLVER_HF

from cst_help_mcp.benchmark import (
    Benchmark,
    Report,
    derived_probes,
    grid_search,
    load_benchmark,
    run_benchmark,
)
from cst_help_mcp.errors import BenchmarkError
from cst_help_mcp.retrieval import KnowledgeBase, Ranking


@pytest.fixture(scope="module")
def benchmark() -> Benchmark:
    return load_benchmark(BENCHMARK)


def test_the_benchmark_holds_every_draft_question_by_its_id(benchmark: Benchmark) -> None:
    ids = [q.id for q in benchmark.questions]

    assert len(ids) == 39
    assert ids[0] == "API-01" and ids[-1] == "NODOC-01"
    counts = Counter(q.category for q in benchmark.questions)
    assert counts == {
        "API": 10, "SOL": 4, "HOW": 4, "TERM": 3, "THEO": 2, "LINK": 2,
        "FIG": 3, "PDF": 2, "EXP": 2, "REL": 1, "LIB": 5, "NODOC": 1,
    }  # fmt: skip
    assert [q.id for q in benchmark.questions if q.scored_by_hand] == ["NODOC-01"]


def test_expected_sources_map_to_locators_mechanically(benchmark: Benchmark) -> None:
    def locators(question: str) -> list[str]:
        return [s.locator for s in next(q for q in benchmark.questions if q.id == question).sources]

    # A VBA method's heading gives its anchor; a source id is kept; a PDF page is a page anchor.
    assert locators("API-01") == [f"{SOLVER_HF}#frequencyrange"]
    assert (
        locators("FIG-01")[0]
        == "3d/special_overview/special_overview_waveguideover.htm.md#Port_Modes_Microstrips"
    )
    assert locators("PDF-01") == [
        "documentation/cst-studio-suite---high-frequency-simulation.pdf.md#page-102",
        "3d/special_overview/special_overview_waveguideover.htm.md",
    ]
    assert locators("LIB-02") == [
        "library/result-templates/farfield-and-antenna-properties/export-farfields-as-source^+mws+ds.rtp.md#define"
    ]


def test_a_benchmark_file_with_a_reused_id_is_refused(tmp_path: Path) -> None:
    question = '[[questions]]\nid = "API-01"\nquestion = "q"\nareas = []\nsources = [{ path = "a.htm" }]\n'
    path = tmp_path / "benchmark.toml"
    path.write_text('[categories]\nAPI = "Exact API lookup"\n' + question * 2, encoding="utf-8")

    with pytest.raises(BenchmarkError, match="API-01"):
        load_benchmark(path)


@pytest.fixture(scope="module")
def report(release_kb: KnowledgeBase, benchmark: Benchmark) -> Report:
    return run_benchmark(release_kb, benchmark)


def test_questions_whose_areas_are_not_built_are_skipped(report: Report) -> None:
    # The release build reads the 3D, General and VBA 3D Areas so far.
    assert report.skipped["API-04"] == ["vba-schematic"]
    assert report.skipped["LIB-05"] == ["result-templates"]
    assert "SOL-03" not in report.skipped
    assert report.rank("SOL-03", filtered=True) is not None


def test_questions_scored_by_hand_are_listed_not_scored(report: Report) -> None:
    assert report.by_hand == ["NODOC-01"]
    assert all(r.probe.id != "NODOC-01" for r in report.results)


def test_api_questions_also_check_that_lookup_returns_the_first_source(report: Report) -> None:
    assert report.lookups["API-01"] is not None
    assert set(report.lookups) == {"API-01", "API-02", "API-03"}


def test_scores_are_reported_per_category_and_overall_with_and_without_the_area_filter(
    report: Report,
) -> None:
    sol = [report.rank(q, filtered=False) for q in ("SOL-01", "SOL-02", "SOL-03", "SOL-04")]
    score = report.score("questions", filtered=False, category="SOL")

    assert score.n == 4
    assert score.hit_rate == sum(r is not None for r in sol) / 4
    assert score.mrr == pytest.approx(sum(1 / r for r in sol if r) / 4)
    overall = report.score("questions", filtered=True)
    assert overall.n == len(
        {r.probe.id for r in report.results if r.probe.set == "questions" and r.probe.filtered}
    )
    assert "SOL" in report.format() and "overall" in report.format()


def test_short_queries_are_scored_next_to_the_full_question(report: Report) -> None:
    short = [r for r in report.results if r.probe.set == "short" and r.probe.id == "HOW-04"]

    assert {r.probe.query for r in short} == {"disable history step", "history list hide"}
    assert report.score("short").n > report.score("questions").n


def test_every_set_is_split_once_into_a_tuning_and_a_held_out_half(report: Report) -> None:
    halves = {r.probe.id: r.probe.half for r in report.results if r.probe.set in ("questions", "short")}
    tuning = report.score("questions", half="tuning").n
    held_out = report.score("questions", half="held-out").n

    assert set(halves.values()) == {"tuning", "held-out"}
    # A question's short queries fall in the same half as the question itself.
    assert all(r.probe.half == halves[r.probe.id] for r in report.results if r.probe.set == "short")
    assert tuning + held_out == report.score("questions").n
    # The split is stratified by category.
    for category in ("SOL", "HOW"):
        assert report.score("questions", "tuning", filtered=False, category=category).n == 2


def test_the_split_of_a_question_does_not_depend_on_the_others(
    release_kb: KnowledgeBase, benchmark: Benchmark, report: Report
) -> None:
    fewer = run_benchmark(release_kb, Benchmark(benchmark.categories, benchmark.questions[10:20]))

    halves = {r.probe.id: r.probe.half for r in report.results}
    assert fewer.results
    assert all(r.probe.half == halves[r.probe.id] for r in fewer.results)


def test_derived_question_sets_come_from_the_built_knowledge_base(release_kb: KnowledgeBase) -> None:
    probes = derived_probes(release_kb, sample=40)

    by_set = {name: [p for p in probes if p.set == name] for name in ("keywords", "toc", "api")}
    assert {len(p) for p in by_set.values()} == {40}
    assert probes == derived_probes(release_kb, sample=40)
    # Each keyword finds the Documents it names, each table-of-contents entry its Document, each API Entry
    # name its own Section.
    keyword = next(p for p in by_set["keywords"] if len(p.expected) == 1)
    assert release_kb.document_of(next(iter(keyword.expected))) is not None
    assert all(p.exact and "#" in next(iter(p.expected)) for p in by_set["api"])
    assert all({p.half for p in set_probes} == {"tuning", "held-out"} for set_probes in by_set.values())


def test_derived_sets_are_scored_per_set(release_kb: KnowledgeBase, benchmark: Benchmark) -> None:
    report = run_benchmark(
        release_kb, Benchmark(benchmark.categories, []), derived=derived_probes(release_kb, sample=40)
    )

    assert report.score("toc").n == 40
    assert report.score("api").hit_rate > 0.9
    assert "## keywords" in report.format()


def test_a_grid_of_weights_reports_the_best_settings_and_the_plateau_around_them(
    release_kb: KnowledgeBase, benchmark: Benchmark
) -> None:
    result = grid_search(
        release_kb, benchmark, {"title": [5.0, 10.0, 20.0], "fusion": ["sum", "normalised", "rank"]}
    )

    assert len(result.points) == 9
    middle = next(p for p in result.points if p.ranking == Ranking(title=10.0))
    # The next weight either way, and any other fusion: fusions have no order.
    assert {(p.ranking.title, p.ranking.fusion) for p in result.neighbours(middle)} == {
        (5.0, "sum"), (20.0, "sum"), (10.0, "normalised"), (10.0, "rank")
    }  # fmt: skip
    assert result.base is middle
    assert result.best in result.points
    text = result.format()
    assert "best" in text and "plateau" in text and "held-out" in text


def test_a_weight_change_counts_as_better_only_if_the_held_out_half_improves_too(
    release_kb: KnowledgeBase, benchmark: Benchmark
) -> None:
    result = grid_search(release_kb, benchmark, {"body": [1.0]})

    assert result.best is result.base
    assert not result.better
    assert result.neighbours(result.best) == []
