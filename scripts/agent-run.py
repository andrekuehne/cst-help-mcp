"""Score the benchmark by running agents from the Knowledge Base folder (ADR 0014).

For each scorable question of the benchmark, run an agent command in a Release folder with the
question on stdin, read the tool calls from its output, and report how many calls it took to
the first read of an expected Document. The thresholds are those of docs/benchmark-draft.md:
every scorable question is a hit, and the median is at most 4 calls.

The agent must have file tools only, and its output must be Claude Code's stream-json, one
event per line. With Claude Code:

    uv run python scripts/agent-run.py --folder .kb/cst-2024 --transcripts runs/sonnet -- \
        claude -p --output-format stream-json --verbose --model sonnet \
        --allowedTools Read Grep Glob --disallowedTools Bash Edit Write WebFetch WebSearch Task

The transcripts are kept, so a run can be scored again with --rescore and no agent.

A question is scorable when it is not scored by hand and every Area it names is built in the
folder. A hit is a read of an expected Document or of a Document that lists it as an Alias. For a
PDF with a given page, the read must reach that page: a read of the text companion whose lines
include some of the page's text below its heading, or a read of the PDF whose pages include it.
A read that failed, such as one of a file too large to read whole, reaches nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cst_help_mcp.locator import locator_for

MEDIAN_LIMIT = 4
# What Claude Code's Read tool reads of a file when it is given no offset or limit.
READ_LIMIT = 2000
_PAGE_HEADING = re.compile(r"## page-(\d+)")
PROMPT = """\
Answer this question about CST Studio Suite from the files in the current folder, which is the
CST help converted to Markdown. Read AGENTS.md first. Use only your file tools (read, grep,
glob): no shell, no web, no other tools. Cite the files you rely on.

Question: {question}
"""


@dataclass(frozen=True)
class Question:
    id: str
    half: str
    text: str
    areas: tuple[str, ...]
    sources: tuple[tuple[str, int | None], ...]  # source paths, relative to the corpus root, and PDF pages


@dataclass(frozen=True)
class Target:
    """An expected Document as the folder holds it, and for a PDF the page a read must reach."""

    locator: str
    page: int | None = None
    lines: tuple[int, int] = (0, 0)  # for a page, the first and last line of its text in the companion

    def reached_by(self, folder: Path, arguments: dict[str, Any]) -> bool:
        """Whether a Read call with these arguments reads the Document, at its page if it has one."""
        path = arguments.get("file_path")
        if not isinstance(path, str):
            return False
        key = _key(folder / path)
        if key == _key(folder / self.locator):
            if self.page is None:
                return True
            first = int(arguments.get("offset") or 1)
            last = first + int(arguments.get("limit") or READ_LIMIT) - 1
            return first <= self.lines[1] and last >= self.lines[0]
        if self.page is not None and key == _key(folder / self.locator.removesuffix(".md")):
            pages = _pages(arguments.get("pages"))
            return pages is None or self.page in pages
        return False


@dataclass
class Folder:
    """A Release folder: which Areas it holds, and which file each source path became."""

    path: Path
    areas: set[str] = field(default_factory=set)
    documents: dict[str, str] = field(default_factory=dict)  # lowercased source path: Locator

    @classmethod
    def read(cls, path: Path) -> Folder:
        folder = cls(path)
        for page in path.rglob("*.md"):
            front = _frontmatter(page)
            if "source" not in front or "copy_of" in front:
                continue  # not a page, or a copy of the Document at its Locator
            locator = page.relative_to(path).as_posix()
            folder.areas.add(front["area"])
            folder.areas.update(front.get("alias_areas", []))
            for source in [front["source"], *front.get("aliases", [])]:
                folder.documents[source.lower()] = locator
        return folder

    def expected(self, question: Question) -> set[Target]:
        """The question's expected Documents that the folder holds."""
        targets = set()
        for source, page in question.sources:
            locator = self.documents.get(source.lower(), locator_for(source))
            if not (self.path / locator).is_file():
                continue
            if page is None:
                targets.add(Target(locator))
            elif lines := _page_lines(self.path / locator, page):
                targets.add(Target(locator, page, lines))
        return targets


@dataclass(frozen=True)
class Score:
    question: Question
    calls: int  # every tool call the agent made
    first_hit: int | None  # the call that first read an expected Document; None for a miss
    note: str = ""


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    folder = Folder.read(args.folder.resolve())
    questions = _scorable(_load(args.questions), folder, args.only)
    if not questions:
        print("No scorable question: none of their Areas is built in the folder.", file=sys.stderr)
        return 2
    if not args.rescore and not args.command:
        print("Give the agent command after --, or --rescore a folder of transcripts.", file=sys.stderr)
        return 2
    transcripts: Path | None = args.rescore or args.transcripts
    if transcripts:
        transcripts.mkdir(parents=True, exist_ok=True)
    scores = []
    for question in questions:
        expected = folder.expected(question)
        if not expected:
            scores.append(Score(question, 0, None, "no expected Document is in the folder"))
            continue
        if args.rescore:
            file = args.rescore / f"{question.id}.jsonl"
            if not file.is_file():
                scores.append(Score(question, 0, None, f"no transcript {file.name}"))
                continue
            output = file.read_text(encoding="utf-8")
        else:
            output = _run(args.command, folder.path, question, args.timeout)
            if transcripts:
                (transcripts / f"{question.id}.jsonl").write_text(output, encoding="utf-8")
        scores.append(score(question, output, folder.path, expected))
        print(_line(scores[-1]), flush=True)
    print()
    report, passed = summary(scores)
    print(report)
    return 0 if passed else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--folder", type=Path, required=True, help="the Release folder, such as .kb/cst-2024")
    parser.add_argument("--questions", type=Path, default=Path("docs/benchmark.toml"))
    parser.add_argument("--only", help="comma-separated question ids")
    parser.add_argument("--transcripts", type=Path, help="keep each agent's output in this folder")
    parser.add_argument(
        "--rescore", type=Path, help="score the transcripts in this folder instead of running"
    )
    parser.add_argument("--timeout", type=float, default=600, help="seconds per question")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- and the agent command")
    return parser


def _load(path: Path) -> list[Question]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return [
        Question(
            q["id"],
            q["half"],
            q["question"],
            tuple(q["areas"]),
            tuple((s["path"], s.get("page")) for s in q["sources"]),
        )
        for q in data["questions"]
        if q.get("confidence") != "rejected" and q.get("scored") != "by hand"
    ]


def _scorable(questions: list[Question], folder: Folder, only: str | None) -> list[Question]:
    wanted = set(only.split(",")) if only else None
    return [q for q in questions if set(q.areas) <= folder.areas and (wanted is None or q.id in wanted)]


def _run(command: list[str], folder: Path, question: Question, timeout: float) -> str:
    command = command[1:] if command[:1] == ["--"] else command
    try:
        done = subprocess.run(
            command,
            check=False,  # a failed agent is scored by what it printed
            cwd=folder,
            input=PROMPT.format(question=question.text),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        out = e.stdout
        return out.decode("utf-8", "replace") if isinstance(out, bytes) else out or ""
    return done.stdout


def tool_calls(output: str) -> list[tuple[str, dict[str, Any]]]:
    """The tool calls in a Claude Code stream-json transcript, in order, as (name, input)."""
    return [(name, arguments) for name, arguments, _ in _calls(output)]


def _calls(output: str) -> list[tuple[str, dict[str, Any], bool]]:
    """The tool calls in a transcript as (name, input, failed): failed when its result is an error,
    such as a Read of a file too large to read whole."""
    calls = []
    failed = set()
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict) or event.get("type") not in ("assistant", "user"):
            continue
        content = event.get("message", {}).get("content", [])
        for item in content if isinstance(content, list) else []:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use":
                calls.append((item.get("id"), str(item.get("name")), item.get("input") or {}))
            elif item.get("type") == "tool_result" and item.get("is_error"):
                failed.add(item.get("tool_use_id"))
    return [(name, arguments, call_id in failed) for call_id, name, arguments in calls]


def score(question: Question, output: str, folder: Path, expected: set[Target]) -> Score:
    calls = _calls(output)
    # The arguments of each call that read a file, and {} for every other call and failed read.
    read_arguments = [arguments if name == "Read" and not failed else {} for name, arguments, failed in calls]
    # Counts compare with the recorded runs only if call 1 was the AGENTS.md read.
    agents_md = Target("AGENTS.md")
    first = read_arguments[:1]
    note = "" if first and agents_md.reached_by(folder, first[0]) else "call 1 was not the AGENTS.md read"
    if not calls:
        note = "no tool calls in the output"
    for n, arguments in enumerate(read_arguments, start=1):
        if any(target.reached_by(folder, arguments) for target in expected):
            return Score(question, len(calls), n, note)
    return Score(question, len(calls), None, note)


def _page_lines(companion: Path, page: int) -> tuple[int, int] | None:
    """The first and last line of a page's text in a PDF's text companion, after its heading."""
    lines = companion.read_text(encoding="utf-8").splitlines()
    headings = [
        (n, int(m[1])) for n, line in enumerate(lines, start=1) if (m := _PAGE_HEADING.fullmatch(line))
    ]
    for i, (first, number) in enumerate(headings):
        if number == page:
            # The section ends before the next page's anchor line, which precedes its heading.
            last = headings[i + 1][0] - 2 if i + 1 < len(headings) else len(lines)
            return first + 1, last
    return None


def _pages(pages: object) -> set[int] | None:
    """The pages a Read of a PDF reads: a range such as "11-13", a page, or a list of them; None,
    for all of them, when none are given."""
    if not isinstance(pages, str) or not pages.strip():
        return None
    read: set[int] = set()
    for part in pages.split(","):
        first, _, last = part.strip().partition("-")
        try:
            read.update(range(int(first), int(last or first) + 1))
        except ValueError:
            continue
    return read


def _key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(path))


def _line(s: Score) -> str:
    hit = f"first expected read at call {s.first_hit}" if s.first_hit else "MISS"
    note = f" ({s.note})" if s.note else ""
    return f"{s.question.id:9} {s.question.half:9} {hit}, {s.calls} calls{note}"


def summary(scores: list[Score]) -> tuple[str, bool]:
    """The distribution of calls to the first expected read, and whether the thresholds hold."""
    hits = [s.first_hit for s in scores if s.first_hit is not None]
    misses = [s.question.id for s in scores if s.first_hit is None]
    median = statistics.median(hits) if hits else None
    lines = [f"{len(hits)} of {len(scores)} scorable questions reached an expected Document."]
    if median is not None:
        lines.append(f"Median {median:g} calls to the first expected read, maximum {max(hits)}.")
    for half in ("tuning", "held-out"):
        own = [s.first_hit for s in scores if s.question.half == half and s.first_hit is not None]
        total = sum(1 for s in scores if s.question.half == half)
        if total:
            lines.append(
                f"  {half}: {len(own)} of {total}" + (f", median {statistics.median(own):g}" if own else "")
            )
    lines.append("Calls to the first expected read:")
    lines.extend(f"  {calls:3}: {count}" for calls, count in sorted(Counter(hits).items()))
    if misses:
        lines.append(f"Missed: {', '.join(misses)}")
    passed = not misses and median is not None and median <= MEDIAN_LIMIT
    lines.append(
        "PASS" if passed else f"FAIL: every question must be a hit, with a median of at most {MEDIAN_LIMIT}"
    )
    return "\n".join(lines), passed


def _frontmatter(page: Path) -> dict[str, Any]:
    text = page.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    head = text[4:].partition("\n---\n")[0]
    front = {}
    for line in head.splitlines():
        key, _, value = line.partition(": ")
        try:
            front[key] = json.loads(value)
        except ValueError:
            continue
    return front


if __name__ == "__main__":
    sys.exit(main())
