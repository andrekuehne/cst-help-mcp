"""The `cst-help` command line."""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Sequence
from pathlib import Path

from cst_help_mcp.errors import CstHelpError
from cst_help_mcp.retrieval import KnowledgeBase

DEFAULT_CONFIG = "cst-help.toml"


def main(argv: Sequence[str] | None = None) -> int:
    # Help text is UTF-8; a Windows console may not be able to show every character.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(errors="replace")
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result: int = args.run(args)
        return result
    except CstHelpError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cst-help", description=__doc__)
    commands = parser.add_subparsers(required=True, metavar="command")

    build = commands.add_parser("build", help="build one Collection into the Knowledge Base")
    build.add_argument("collection")
    build.add_argument("--config", type=Path, default=Path(DEFAULT_CONFIG))
    build.set_defaults(run=_build)

    lookup = commands.add_parser("lookup", help="look up an API Entry by name, such as Solver.FrequencyRange")
    lookup.add_argument("name")
    _add_kb_arguments(lookup)
    lookup.add_argument("--area")
    lookup.set_defaults(run=_lookup)

    search = commands.add_parser("search", help="search the Knowledge Base by plain words")
    search.add_argument("query", nargs="+")
    _add_kb_arguments(search)
    search.add_argument("--area", action="append", dest="areas")
    search.add_argument("--limit", type=int, default=10)
    search.set_defaults(run=_search)
    return parser


def _add_kb_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kb", type=Path, required=True, help="the Knowledge Base folder")
    parser.add_argument("--release", help="the Release to query (default: the newest)")


def _build(args: argparse.Namespace) -> int:
    from cst_help_mcp.build import build_collection

    docs = build_collection(args.config, args.collection)
    entries = sum(len(d.api_entries) for d in docs)
    print(f"Built {args.collection}: {len(docs)} Documents, {entries} API Entries")
    return 0


def _lookup(args: argparse.Namespace) -> int:
    with KnowledgeBase.open(args.kb, args.release) as kb:
        hits = kb.lookup(args.name, area=args.area)
    if not hits:
        print(f"{args.name}: not documented in Release {kb.release}")
        return 1
    for hit in hits:
        print(f"{hit.qualified_name}  [{hit.area}, {hit.release}]")
        print(f"  {hit.signature}")
        if hit.description:
            print(f"  {hit.description}")
        print(f"  Locator: {hit.locator}")
        print(f"  Source: {hit.source_path}")
        print()
    return 0


def _search(args: argparse.Namespace) -> int:
    with KnowledgeBase.open(args.kb, args.release) as kb:
        hits = kb.search(" ".join(args.query), areas=args.areas, limit=args.limit)
    if not hits:
        print("No hits.")
        return 1
    for hit in hits:
        print(f"{hit.locator}  [{hit.area}, {hit.release}]")
        print(f"  {hit.heading_path}")
        print(f"  {hit.snippet}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
