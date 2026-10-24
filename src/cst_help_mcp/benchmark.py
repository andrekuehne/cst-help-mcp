"""The benchmark runner: scores the machine-readable benchmark (docs/benchmark.toml) against a built
Knowledge Base, and tunes search's weights on it.

Expected sources are mapped from source paths to Locators mechanically (ADR 0011).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal, get_args

from cst_help_mcp.errors import BenchmarkError
from cst_help_mcp.locator import anchor_for, document_part, is_usable_source_id, locator_for, page_anchor
from cst_help_mcp.retrieval import DEFAULT_RANKING, Fusion, KnowledgeBase, Ranking

DEFAULT_BENCHMARK = "docs/benchmark.toml"
TOP = 5  # a hit counts among the top 5
# Fixes the split of a question or derived item without a recorded half into the tuning or held-out
# half. Never change it, or the held-out half stops being held out.
SPLIT_SEED = "cst-help-benchmark-1"
QUESTION_SETS = ("questions", "short")  # the full questions and their short queries

Half = Literal["tuning", "held-out"]
HALVES: tuple[Half, ...] = ("tuning", "held-out")


@dataclass(frozen=True)
class ExpectedSource:
    path: str  # relative to the corpus root, as CST names the file
    anchor: str | None = None  # the literal HTML id or name
    headings: tuple[str, ...] = ()  # a VBA method or Library procedure within the anchor's Section
    page: int | None = None  # a PDF's physical page

    @property
    def document(self) -> str:
        return locator_for(self.path)

    @property
    def locator(self) -> str:
        """The Locator of the most specific part named: a heading, then the anchor, then the page."""
        if self.headings:
            fragment = anchor_for(self.headings[0])
        elif self.anchor:
            fragment = self.anchor if is_usable_source_id(self.anchor) else anchor_for(self.anchor)
        elif self.page is not None:
            fragment = page_anchor(self.page)
        else:
            return self.document
        return f"{self.document}#{fragment}"


Rank = int | None  # the rank (1 to 5) of the best expected source among the hits, None for a miss


@dataclass(frozen=True)
class Question:
    id: str
    category: str  # the id's prefix, such as API
    text: str
    areas: tuple[str, ...]  # the filter an agent would plausibly use
    sources: tuple[ExpectedSource, ...]  # best first
    half: Half
    short: tuple[str, ...] = ()  # queries as an agent types them
    api_entries: tuple[str, ...] = ()
    scored_by_hand: bool = False
    # Recorded ranks by name, such as "06": (unfiltered, filtered to the Areas).
    baseline: dict[str, tuple[Rank, Rank]] | None = None


@dataclass(frozen=True)
class Benchmark:
    categories: dict[str, str]  # id prefix: name
    questions: list[Question]


def load_benchmark(path: Path) -> Benchmark:
    """Read and check the benchmark file; rejected questions are left out."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BenchmarkError(f"Benchmark file not found: {path}") from None
    except tomllib.TOMLDecodeError as e:
        raise BenchmarkError(f"{path} is not valid TOML: {e}") from None
    categories: dict[str, str] = data.get("categories", {})
    questions: list[Question] = []
    seen: set[str] = set()
    for raw in data.get("questions", []):
        try:
            question = _question(raw, categories)
        except (KeyError, TypeError, ValueError) as e:
            raise BenchmarkError(f"{path}: question {raw.get('id', '?')} is malformed: {e}") from None
        if question.id in seen:
            raise BenchmarkError(f"{path}: question id {question.id} is used twice")
        seen.add(question.id)
        if raw.get("confidence") != "rejected":
            questions.append(question)
    return Benchmark(categories, questions)


def _question(raw: dict[str, Any], categories: dict[str, str]) -> Question:
    qid = str(raw["id"])
    category = qid.rpartition("-")[0]
    if category not in categories:
        raise ValueError(f"unknown category '{category}'")
    sources = tuple(
        ExpectedSource(s["path"], s.get("anchor"), tuple(s.get("headings", ())), s.get("page"))
        for s in raw["sources"]
    )
    if not sources:
        raise ValueError("no expected sources")
    baseline = {name: (_rank(ranks[0]), _rank(ranks[1])) for name, ranks in raw.get("baseline", {}).items()}
    half = raw.get("half", half_of("questions", qid))
    if half not in HALVES:
        raise ValueError(f"half is one of {', '.join(HALVES)}, not {half!r}")
    return Question(
        qid,
        category,
        str(raw["question"]),
        tuple(raw["areas"]),
        sources,
        half,
        tuple(raw.get("short", ())),
        tuple(raw.get("api_entries", ())),
        raw.get("scored") == "by hand",
        baseline or None,
    )


def _rank(value: object) -> Rank:
    if value == "miss":
        return None
    if isinstance(value, int) and 1 <= value <= TOP:
        return value
    raise ValueError(f'a rank is 1 to {TOP} or "miss", not {value!r}')


@dataclass(frozen=True)
class Probe:
    """One query the runner sends to search, and the Locators that count as a hit."""

    set: str  # one of QUESTION_SETS, or a derived set such as "keywords"
    id: str  # the question's id, or the derived item's name
    category: str
    query: str
    areas: tuple[str, ...]  # the filter; () for none
    expected: frozenset[str]  # Locators of Documents, or of Sections when exact
    half: Half  # a question's short queries fall in the question's half
    exact: bool = False  # a hit must be the Section itself, not just its Document

    @property
    def filtered(self) -> bool:
        return bool(self.areas)


def half_of(question_set: str, item: str) -> Half:
    """The half an item of a set falls in, by a hash of its name, so adding items never moves others."""
    return HALVES[int(_digest(f"{question_set}:{item}")[0], 16) % 2]


@dataclass(frozen=True)
class Result:
    probe: Probe
    rank: Rank


@dataclass(frozen=True)
class Score:
    n: int
    hit_rate: float  # the share of probes with an expected source among the top 5
    mrr: float  # the mean reciprocal rank, a miss counting 0

    @classmethod
    def of(cls, ranks: Sequence[Rank]) -> Score:
        if not ranks:
            return cls(0, 0.0, 0.0)
        hits = sum(r is not None for r in ranks)
        return cls(len(ranks), hits / len(ranks), sum(1 / r for r in ranks if r) / len(ranks))


@dataclass
class Report:
    results: list[Result] = field(default_factory=list)
    skipped: dict[str, list[str]] = field(default_factory=dict)  # question id: its Areas not built
    by_hand: list[str] = field(default_factory=list)
    # API question id: the rank of its first source among lookup's hits; None if lookup misses it.
    lookups: dict[str, Rank] = field(default_factory=dict)
    # Question id: its expected Documents that the Knowledge Base doesn't hold.
    missing: dict[str, list[str]] = field(default_factory=dict)
    baselines: dict[str, dict[str, tuple[Rank, Rank]]] = field(default_factory=dict)

    def rank(self, question: str, filtered: bool, question_set: str = "questions") -> Rank:
        for r in self.results:
            if r.probe.set == question_set and r.probe.id == question and r.probe.filtered == filtered:
                return r.rank
        raise KeyError(f"{question} has no {'filtered' if filtered else 'unfiltered'} {question_set} result")

    def score(
        self,
        question_set: str,
        half: Half | None = None,
        filtered: bool | None = None,
        category: str | None = None,
    ) -> Score:
        return Score.of(
            [
                r.rank
                for r in self.results
                if r.probe.set == question_set
                and (half is None or r.probe.half == half)
                and (filtered is None or r.probe.filtered == filtered)
                and (category is None or r.probe.category == category)
            ]
        )

    def format(self) -> str:
        """The report as text: scores per set, filter, half and category, then what wasn't scored."""
        lines: list[str] = []
        for question_set in dict.fromkeys(r.probe.set for r in self.results):
            results = [r for r in self.results if r.probe.set == question_set]
            filters = list(dict.fromkeys(r.probe.filtered for r in results))
            lines.append(f"## {question_set}: hit at {TOP}, mean reciprocal rank")
            lines.append(_row("", [f"{'Area' if f else 'all'} {h}" for f in filters for h in HALVES]))
            for category in [*dict.fromkeys(r.probe.category for r in results), None]:
                scores = [self.score(question_set, h, f, category) for f in filters for h in HALVES]
                lines.append(_row(category or "overall", [_cell(s) for s in scores]))
            lines.append("")
        if self.lookups:
            found = ", ".join(f"{q} {_rank_text(r)}" for q, r in self.lookups.items())
            lines.append(f"Lookup returns the first source: {found}")
        for question, baseline in self.baselines.items():
            now = (self.rank(question, False), self.rank(question, True))
            recorded = "; ".join(f"{name} {_ranks_text(ranks)}" for name, ranks in baseline.items())
            lines.append(f"Baseline {question} (all, Area): now {_ranks_text(now)}; {recorded}")
        if self.by_hand:
            lines.append(f"Scored by hand, not here: {', '.join(self.by_hand)}")
        if self.skipped:
            skipped = ", ".join(f"{q} ({', '.join(a)})" for q, a in self.skipped.items())
            lines.append(f"Skipped, Areas not built: {skipped}")
        for question, documents in self.missing.items():
            lines.append(f"{question}: expected sources not in the Knowledge Base: {', '.join(documents)}")
        return "\n".join(lines)


def _rank_text(rank: Rank) -> str:
    return str(rank) if rank else "miss"


def _ranks_text(ranks: tuple[Rank, Rank]) -> str:
    return ", ".join(_rank_text(r) for r in ranks)


def _cell(score: Score) -> str:
    return f"{score.hit_rate:.0%} {score.mrr:.2f} n={score.n}" if score.n else "-"


def _row(label: str, cells: list[str]) -> str:
    return f"{label:<10}" + "".join(f"{c:>22}" for c in cells)


def question_probes(question: Question) -> list[Probe]:
    """The full question and its short queries, each unfiltered and filtered to the question's Areas."""
    expected = frozenset(s.document for s in question.sources)
    filters = [(), question.areas] if question.areas else [()]
    queries = [("questions", question.text), *(("short", q) for q in question.short)]
    return [
        Probe(question_set, question.id, question.category, query, areas, expected, question.half)
        for question_set, query in queries
        for areas in filters
    ]


def run_benchmark(
    kb: KnowledgeBase,
    benchmark: Benchmark,
    ranking: Ranking = DEFAULT_RANKING,
    derived: Iterable[Probe] = (),
) -> Report:
    """Score every question whose Areas are built, and the derived probes, against the Knowledge Base."""
    report = Report()
    probes: list[Probe] = []
    for question in benchmark.questions:
        if question.scored_by_hand:
            report.by_hand.append(question.id)
            continue
        unbuilt = [a for a in question.areas if a not in kb.areas]
        if unbuilt:
            report.skipped[question.id] = unbuilt
            continue
        probes += question_probes(question)
        missing = [s.document for s in question.sources if kb.document_of(s.document) is None]
        if missing:
            report.missing[question.id] = list(dict.fromkeys(missing))
        if question.category == "API" and question.api_entries:
            report.lookups[question.id] = _lookup_rank(kb, question)
        if question.baseline:
            report.baselines[question.id] = question.baseline
    report.results = [Result(p, rank_probe(kb, p, ranking)) for p in [*probes, *derived]]
    return report


def rank_probe(kb: KnowledgeBase, probe: Probe, ranking: Ranking = DEFAULT_RANKING) -> Rank:
    """The rank of the best expected source among the top 5 hits, or None for a miss.

    A hit counts when it belongs to an expected Document or an Alias of it, or for an exact probe,
    when it is the expected Section.
    """
    expected = probe.expected if probe.exact else {kb.document_of(e) or e for e in probe.expected}
    hits = kb.search(probe.query, areas=list(probe.areas) or None, limit=TOP, ranking=ranking)
    for rank, hit in enumerate(hits, 1):
        if (hit.locator if probe.exact else document_part(hit.locator)) in expected:
            return rank
    return None


def _lookup_rank(kb: KnowledgeBase, question: Question) -> Rank:
    first = kb.document_of(question.sources[0].document)
    hits = kb.lookup(question.api_entries[0])
    return next((i for i, h in enumerate(hits, 1) if document_part(h.locator) == first), None)


DERIVED_SETS = ("keywords", "toc", "api")


def derived_probes(kb: KnowledgeBase, sample: int = 200) -> list[Probe]:
    """Question sets the Knowledge Base labels itself, a fixed sample of each.

    Each author keyword finds the Documents it names, each table-of-contents entry its Document, and each
    API Entry's name its own Section. They hold only names and Locators, never vendor prose. A
    keyword query naturally favours the keyword field, so these sets guard against regressions and
    calibrate the scales of the weights; they aren't for choosing between fields.
    """
    targets: dict[str, set[str]] = {}
    for entry in kb.nav_entries("keywords"):
        # A keyword's Documents are its leaves; its sub-keywords have entries of their own.
        if entry.locator and not entry.children and len(entry.path) > 1:
            targets.setdefault(" ".join(entry.path[:-1]), set()).add(document_part(entry.locator))
    keywords = [("keywords", query, frozenset(found), False) for query, found in targets.items()]
    documents: dict[str, set[str]] = {}
    for entry in kb.nav_entries("toc"):
        if entry.locator:
            documents.setdefault(entry.path[-1], set()).add(document_part(entry.locator))
    toc = [("toc", name, frozenset(found), False) for name, found in documents.items()]
    api = [("api", e.qualified_name, frozenset([e.locator]), True) for e in kb.api_entries()]
    probes = []
    for items in (keywords, toc, api):
        chosen = sorted(items, key=lambda item: _digest(f"sample:{item[0]}:{item[1]}"))[:sample]
        for name, query, expected, exact in sorted(chosen, key=lambda item: item[1]):
            probes.append(Probe(name, query, name, query, (), expected, half_of(name, query), exact))
    return probes


def _digest(text: str) -> str:
    return hashlib.sha256(f"{SPLIT_SEED}:{text}".encode()).hexdigest()


GridValue = float | str
WEIGHTS = ("title", "headings", "body", "keywords", "toc_paths")  # the Ranking fields a grid can vary


@dataclass(frozen=True)
class GridPoint:
    ranking: Ranking
    index: tuple[int, ...]  # the position of each grid dimension's value
    report: Report

    def objective(self, half: Half) -> float:
        """The mean reciprocal rank of the full questions and of the short queries, averaged."""
        return sum(self.report.score(s, half).mrr for s in QUESTION_SETS) / len(QUESTION_SETS)


@dataclass(frozen=True)
class GridResult:
    dimensions: list[str]  # the Ranking field each position of a point's index varies
    points: list[GridPoint]
    base: GridPoint  # the settings search uses without overrides

    def neighbours(self, point: GridPoint) -> list[GridPoint]:
        """The points one step away along one dimension: the next weight, or any other fusion."""

        def steps(p: GridPoint) -> int:
            return sum(
                (a != b) if name == "fusion" else abs(a - b)
                for name, a, b in zip(self.dimensions, p.index, point.index, strict=True)
            )

        return [p for p in self.points if len(p.index) == len(point.index) and steps(p) == 1]

    def plateau(self, point: GridPoint) -> float:
        """The tuning objective averaged over the point and its neighbours: a broad plateau beats a peak."""
        around = [point, *self.neighbours(point)]
        return sum(p.objective("tuning") for p in around) / len(around)

    @property
    def best(self) -> GridPoint:
        return max(self.points, key=lambda p: (self.plateau(p), p.objective("tuning"), p is self.base))

    @property
    def better(self) -> bool:
        """Whether the best settings beat the base on the tuning half and on the held-out half."""
        best, base = self.best, self.base
        return all(best.objective(h) > base.objective(h) for h in HALVES)

    def format(self) -> str:
        lines = [
            f"Grid: {len(self.points)} settings, objective = mean reciprocal rank of questions and short queries"
        ]
        lines.append(f"{'tuning':>8}{'held-out':>10}{'plateau':>9}  settings")
        for p in sorted(self.points, key=lambda p: -self.plateau(p)):
            marks = "".join(m for m, on in ((" best", p is self.best), (" base", p is self.base)) if on)
            lines.append(
                f"{p.objective('tuning'):8.3f}{p.objective('held-out'):10.3f}{self.plateau(p):9.3f}  {describe(p.ranking)}{marks}"
            )
        best = self.best
        around = [p.objective("tuning") for p in self.neighbours(best)]
        spread = f"{min(around):.3f} to {max(around):.3f}" if around else "none in the grid"
        lines += [
            "",
            f"best: {describe(best.ranking)}",
            f"  plateau: its {len(around)} neighbours score {spread} on the tuning half",
            f"  held-out: {best.objective('held-out'):.3f}, base {self.base.objective('held-out'):.3f}",
            "  better than the base on both halves"
            if self.better
            else "  not better than the base on both halves",
        ]
        for name in dict.fromkeys(
            r.probe.set for r in best.report.results if r.probe.set not in QUESTION_SETS
        ):
            lines.append(
                f"  {name}: mean reciprocal rank {best.report.score(name).mrr:.3f}, base {self.base.report.score(name).mrr:.3f}"
            )
        return "\n".join(lines)


def grid_search(
    kb: KnowledgeBase,
    benchmark: Benchmark,
    grid: Mapping[str, Sequence[GridValue]],
    base: Ranking = DEFAULT_RANKING,
    derived: Sequence[Probe] = (),
) -> GridResult:
    """Score every combination of the grid's values, each dimension a Ranking field; the others
    keep the base's values. The base is scored too, inside the grid or not."""
    names = list(grid)
    points = [
        GridPoint(ranking, index, run_benchmark(kb, benchmark, ranking, derived))
        for index in itertools.product(*(range(len(grid[n])) for n in names))
        for ranking in [ranking_with(base, {n: grid[n][i] for n, i in zip(names, index, strict=True)})]
    ]
    found = next((p for p in points if p.ranking == base), None)
    return GridResult(
        names, points, found or GridPoint(base, (), run_benchmark(kb, benchmark, base, derived))
    )


def ranking_with(base: Ranking, values: dict[str, GridValue]) -> Ranking:
    """The base Ranking with some of its weights, or its fusion, replaced."""
    changes: dict[str, Any] = {}
    for name, value in values.items():
        if name in WEIGHTS and isinstance(value, int | float):
            changes[name] = float(value)
        elif name == "fusion" and value in get_args(Fusion):
            changes[name] = value
        elif name in (*WEIGHTS, "fusion"):
            raise BenchmarkError(f"'{value}' is no value for {name}")
        else:
            raise BenchmarkError(f"Unknown weight '{name}'; available: {', '.join(WEIGHTS)}, fusion")
    return replace(base, **changes)


def describe(ranking: Ranking) -> str:
    """The settings of a Ranking, as reports show them."""
    weights = ", ".join(f"{name} {getattr(ranking, name):g}" for name in WEIGHTS)
    return f"{weights}; fusion {ranking.fusion}"


def draft_questions(records: Iterable[dict[str, Any]], benchmark: Benchmark) -> str:
    """Draft benchmark entries, as TOML, for logged queries the benchmark doesn't ask yet.

    Each is held out, and has no expected sources until a human gives them; the Locators the query
    returned are listed as a comment to start from.
    """
    asked = {q.text for q in benchmark.questions} | {s for q in benchmark.questions for s in q.short}
    numbers = [int(q.id.rpartition("-")[2]) for q in benchmark.questions if q.category == "LOG"]
    drafts: dict[tuple[str, tuple[str, ...]], list[str]] = {}
    api: set[str] = set()
    for record in records:
        if record.get("tool") == "cst_help_lookup":
            query, areas = str(record["name"]), [record["area"]] if record.get("area") else []
            api.add(query)
        else:
            query, areas = str(record["query"]), record.get("areas") or []
        if query not in asked:
            drafts.setdefault((query, tuple(areas)), list(record.get("locators", [])))
    blocks = []
    for n, ((query, filters), locators) in enumerate(drafts.items(), max(numbers, default=0) + 1):
        lines = [
            "[[questions]]",
            f'id = "LOG-{n:02d}"  # give it the next free id of its category',
            'half = "held-out"',
            f"question = {_toml_string(query)}",
            f"areas = [{', '.join(_toml_string(a) for a in filters)}]",
        ]
        if query in api:
            lines.append(f"api_entries = [{_toml_string(query)}]")
        lines += [f"# returned: {', '.join(locators) or 'nothing'}", "sources = []", ""]
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def _toml_string(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)  # a JSON string is a valid TOML basic string
