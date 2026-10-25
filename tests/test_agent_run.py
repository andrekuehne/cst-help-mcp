"""The agent run (scripts/agent-run.py) counts tool calls to the first expected Document.

A fake agent stands in for a real one: it prints Claude Code stream-json for a fixed route
that reads AGENTS.md, greps, and reads the Solver page.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
from kb_helpers import BENCHMARK, SOLVER_HF

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "agent-run.py"


def _agent_run() -> ModuleType:
    spec = importlib.util.spec_from_file_location("agent_run", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look their module up there
    spec.loader.exec_module(module)
    return module


def _fake_agent(tmp_path: Path) -> list[str]:
    calls = [
        ("Read", {"file_path": "AGENTS.md"}),
        ("Grep", {"pattern": "^### FrequencyRange", "path": "vba_3d"}),
        ("Read", {"file_path": SOLVER_HF}),
        ("Read", {"file_path": "toc.md"}),
    ]
    events = [{"type": "system", "subtype": "init"}] + [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": n, "input": i}]}}
        for n, i in calls
    ]
    agent = tmp_path / "fake_agent.py"
    agent.write_text(
        "import sys\nsys.stdin.read()\n" + "".join(f"print({json.dumps(json.dumps(e))})\n" for e in events),
        encoding="utf-8",
    )
    return [sys.executable, str(agent)]


def test_a_question_whose_expected_page_is_read_is_a_hit_and_a_missed_one_fails_the_run(
    vba_kb: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = vba_kb / "cst-2024"
    args = ["--folder", str(folder), "--questions", str(BENCHMARK), "--transcripts", str(tmp_path / "runs")]

    code = _agent_run().main([*args, "--only", "API-01,API-02", "--", *_fake_agent(tmp_path)])

    out = capsys.readouterr().out
    assert code == 1
    assert "API-01    tuning    first expected read at call 3, 4 calls" in out
    assert "API-02    tuning    MISS, 4 calls" in out
    assert "1 of 2 scorable questions reached an expected Document." in out
    assert "Missed: API-02" in out
    assert (tmp_path / "runs" / "API-01.jsonl").is_file()


def test_saved_transcripts_are_scored_again_without_an_agent(
    vba_kb: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = vba_kb / "cst-2024"
    args = ["--folder", str(folder), "--questions", str(BENCHMARK), "--only", "API-01"]
    _agent_run().main([*args, "--transcripts", str(tmp_path / "runs"), "--", *_fake_agent(tmp_path)])
    capsys.readouterr()

    code = _agent_run().main([*args, "--rescore", str(tmp_path / "runs")])

    out = capsys.readouterr().out
    assert code == 0
    assert "Median 3 calls to the first expected read, maximum 3." in out
    assert out.rstrip().endswith("PASS")


def test_only_questions_whose_areas_are_built_are_scored(
    vba_kb: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = vba_kb / "cst-2024"

    _agent_run().main(["--folder", str(folder), "--questions", str(BENCHMARK), "--", *_fake_agent(tmp_path)])

    ids = [line.split()[0] for line in capsys.readouterr().out.splitlines() if line[:4] in ("API-", "SOL-")]
    # API-04 needs vba-schematic, NODOC-01 is scored by hand, and SOL-01 needs 3d.
    assert ids[:3] == ["API-01", "API-02", "API-03"]
    assert "API-04" not in ids
    assert "SOL-01" not in ids
