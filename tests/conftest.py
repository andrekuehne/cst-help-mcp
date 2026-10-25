"""Shared test setup: finding the licensed CST corpus and building test Knowledge Bases.

Corpus tests run against the real CST 2024 release folder. It is found, in this order:

1. the environment variable ``CST_HELP_CORPUS_2024`` naming the release folder
   (which may be the installation itself);
2. ``.ingestion/2024/`` in the current checkout;
3. ``.ingestion/2024/`` in the repository's main checkout, found through git's
   common directory, so git worktrees use it automatically.

A configured location that is missing fails the run. Finding nothing fails too,
unless ``CST_HELP_SKIP_CORPUS=1`` is set. The header of every run says which
corpus was used, or why the corpus tier was skipped.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from kb_helpers import (
    PROJECTS,
    PYTHON_OVERVIEW,
    SPHINX,
    VBA_3D,
    VBA_OVERVIEW,
    WINWRAP,
    ProseBuild,
    write_config,
)

from cst_help_mcp.build import build_collection

RELEASE = "2024"
CORPUS_ENV = f"CST_HELP_CORPUS_{RELEASE}"
SKIP_ENV = "CST_HELP_SKIP_CORPUS"
CHECKOUT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CorpusResolution:
    path: Path | None
    how: str
    error: str | None = None


def _main_checkout() -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=CHECKOUT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(out).parent


def _is_release_folder(path: Path) -> bool:
    return (path / "Online Help").is_dir()


def resolve_corpus() -> CorpusResolution:
    configured = os.environ.get(CORPUS_ENV)
    if configured:
        path = Path(configured)
        if not _is_release_folder(path):
            return CorpusResolution(
                None,
                f"${CORPUS_ENV}",
                f"${CORPUS_ENV} names {path}, which is missing or has no 'Online Help' folder",
            )
        return CorpusResolution(path, f"${CORPUS_ENV}")

    searched = [f"${CORPUS_ENV} (not set)"]
    candidates = [("this checkout", CHECKOUT / ".ingestion" / RELEASE)]
    main = _main_checkout()
    if main is not None and main.resolve() != CHECKOUT:
        candidates.append(("main checkout", main / ".ingestion" / RELEASE))
    for how, path in candidates:
        if _is_release_folder(path):
            return CorpusResolution(path, how)
        searched.append(str(path))

    places = "; ".join(searched)
    if os.environ.get(SKIP_ENV) == "1":
        return CorpusResolution(None, "skipped", f"{SKIP_ENV}=1 and no corpus found (searched {places})")
    return CorpusResolution(
        None,
        "not found",
        f"No CST {RELEASE} corpus found. Searched: {places}. "
        f"Set {CORPUS_ENV}, or set {SKIP_ENV}=1 to skip the corpus tier.",
    )


_RESOLUTION = resolve_corpus()


def pytest_report_header() -> str:
    if _RESOLUTION.path is not None:
        return f"CST {RELEASE} corpus: {_RESOLUTION.path} (via {_RESOLUTION.how})"
    if _RESOLUTION.how == "skipped":
        return f"CST {RELEASE} corpus tier SKIPPED: {_RESOLUTION.error}"
    return f"CST {RELEASE} corpus MISSING: {_RESOLUTION.error}"


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    terminalreporter.write_line(pytest_report_header())


@pytest.fixture(scope="session")
def corpus_2024() -> Path:
    if _RESOLUTION.path is not None:
        return _RESOLUTION.path
    if _RESOLUTION.how == "skipped":
        pytest.skip(_RESOLUTION.error or "corpus tier skipped")
    pytest.fail(_RESOLUTION.error or "corpus not found", pytrace=False)


@pytest.fixture(scope="session")
def vba_kb(corpus_2024: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A Knowledge Base holding the VBA 3D Area, built once per test session in a temporary folder."""
    root = tmp_path_factory.mktemp("vba-kb")
    config = write_config(
        root / "cst-help.toml",
        root / "kb",
        corpus_2024,
        ["Online Help/mergedProjects/VBA_3D/*", "Online Help/vba/*"],
    )
    build_collection(config, "cst-2024")
    return root / "kb"


@pytest.fixture(scope="session")
def prose_build(corpus_2024: Path, tmp_path_factory: pytest.TempPathFactory) -> ProseBuild:
    """The 3D Simulation and General Areas, built once per test session in a temporary folder."""
    root = tmp_path_factory.mktemp("prose-kb")
    projects = [p for p in PROJECTS if p not in (VBA_3D, VBA_OVERVIEW, WINWRAP, SPHINX, PYTHON_OVERVIEW)]
    include = [f"{p}/*" for p in projects]
    config = write_config(root / "cst-help.toml", root / "kb", corpus_2024, include)
    result = build_collection(config, "cst-2024")
    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    return ProseBuild(root / "kb", root / "kb" / "cst-2024", report)


@pytest.fixture(scope="session")
def python_build(corpus_2024: Path, tmp_path_factory: pytest.TempPathFactory) -> ProseBuild:
    """The Python Area with the RoboHelp topics its pages link to, built once per test session."""
    root = tmp_path_factory.mktemp("python-kb")
    include = [
        f"{SPHINX}/*",
        f"{PYTHON_OVERVIEW}/*",
        "Online Help/menu.htm",
        "Online Help/user_scipts.htm",
        "Online Help/userinterface/*",
    ]
    config = write_config(root / "cst-help.toml", root / "kb", corpus_2024, include)
    result = build_collection(config, "cst-2024")
    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    return ProseBuild(root / "kb", root / "kb" / "cst-2024", report)


@pytest.fixture(scope="session")
def winwrap_kb(corpus_2024: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A Knowledge Base holding the WinWrap Basic Area, built once per test session in a temporary folder."""
    root = tmp_path_factory.mktemp("winwrap-kb")
    config = write_config(root / "cst-help.toml", root / "kb", corpus_2024, [f"{WINWRAP}/*"])
    build_collection(config, "cst-2024")
    return root / "kb"
