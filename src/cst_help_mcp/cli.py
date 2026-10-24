"""The `cst-help` command line."""

from __future__ import annotations

import argparse
import io
import json
import logging
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from cst_help_mcp.errors import CstHelpError
from cst_help_mcp.retrieval import NAV_TREES, KnowledgeBase

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
    build.add_argument("--strict", action="store_true", help="fail the build if any Document fails")
    build.set_defaults(run=_build)

    assemble = commands.add_parser(
        "assemble", help="assemble the newest Build of every Collection into the Knowledge Base"
    )
    assemble.add_argument("--kb", type=Path, required=True, help="the Knowledge Base folder")
    assemble.set_defaults(run=_assemble)

    validate = commands.add_parser("validate", help="check the integrity of a Knowledge Base")
    validate.add_argument("--kb", type=Path, required=True, help="the Knowledge Base folder")
    validate.set_defaults(run=_validate)

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

    browse = commands.add_parser(
        "browse", help="list the entries below a table-of-contents book or a keyword"
    )
    browse.add_argument(
        "path", nargs="?", default="", help='entry names joined by ">", such as "3D Simulation > Solvers"'
    )
    _add_kb_arguments(browse)
    browse.add_argument("--tree", choices=list(NAV_TREES), default="toc")
    browse.set_defaults(run=_browse)

    serve = commands.add_parser(
        "serve", help="serve one Release of the Knowledge Base as an MCP server over stdio"
    )
    _add_kb_arguments(serve)
    serve.set_defaults(run=_serve)

    instructions = commands.add_parser(
        "instructions", help="print the MCP entry and AGENTS.md section to add to a project"
    )
    _add_kb_arguments(instructions)
    instructions.set_defaults(run=_instructions)
    return parser


def _add_kb_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kb", type=Path, required=True, help="the Knowledge Base folder")
    parser.add_argument("--release", help="the Release to query (default: the newest)")


def _build(args: argparse.Namespace) -> int:
    from cst_help_mcp.build import build_collection

    result = build_collection(args.config, args.collection, strict=args.strict)
    report = result.report
    print(
        f"Built {args.collection}: {report.documents} Documents,"
        f" {report.api_entries} API Entries (Build {result.build_id})"
    )
    print(
        f"  Documents: discovered {report.discovered}, converted {report.converted},"
        f" skipped {report.skipped}, failed {report.failed}; {report.aliases} were Aliases"
    )
    print(
        f"  unresolved links {report.unresolved_links}, missing anchors {report.missing_anchors},"
        f" missing Assets {_count(report.missing_assets)},"
        f" unsupported items {sum(report.unsupported.values())}"
    )
    for failure in report.failures:
        print(f"  failed: {failure.source}: {failure.error}")
    if not report.complete:
        print(f"The Knowledge Base is incomplete; see {result.report_path}, or rebuild with --strict.")
    return 0


def _count(n: int | None) -> str:
    return "not checked yet" if n is None else str(n)


def _assemble(args: argparse.Namespace) -> int:
    from cst_help_mcp.assembly import assemble

    assembly = assemble(args.kb)
    for collection, build in assembly.builds.items():
        print(f"Assembled {collection} (Build {build})")
    return 0


def _validate(args: argparse.Namespace) -> int:
    from cst_help_mcp.validate import validate

    result = validate(args.kb)
    for problem in result.problems:
        print(f"problem: {problem}")
    if result.problems:
        print(f"The Knowledge Base at {args.kb} is not valid: {len(result.problems)} problems")
        return 1
    print(f"The Knowledge Base at {args.kb} is valid")
    for c in result.collections:
        state = "complete" if not c.failed else f"incomplete, {c.failed} failed"
        print(f"  {c.name}: Build {c.build}, {c.documents} Documents, {state}")
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


def _browse(args: argparse.Namespace) -> int:
    with KnowledgeBase.open(args.kb, args.release) as kb:
        result = kb.browse(args.path, tree=args.tree)
    print(f"{result.title}, Release {result.release}: {len(result.entries)} entries")
    for entry in result.entries:
        locator = f"  [{entry.locator}]" if entry.locator else ""
        print(f"- {entry}{locator}")
    return 0


def _serve(args: argparse.Namespace) -> int:
    from cst_help_mcp.server import create_server

    # stdout carries the MCP protocol, so every log line goes to stderr.
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    with KnowledgeBase.open(args.kb, args.release) as kb:
        create_server(kb).run("stdio")
    return 0


def _instructions(args: argparse.Namespace) -> int:
    from cst_help_mcp.server import server_instructions

    kb_path = args.kb.resolve()
    with KnowledgeBase.open(kb_path, args.release) as kb:
        section = server_instructions(kb)
    server_args = ["serve", "--kb", str(kb_path)]
    if args.release:
        server_args += ["--release", args.release]
    # An absolute path, because the client may not have this environment's scripts on its PATH.
    command = shutil.which("cst-help") or "cst-help"
    entry = {"mcpServers": {"cst-help": {"type": "stdio", "command": command, "args": server_args}}}
    print("Add this server to the project's .mcp.json (Claude Code) or the client's MCP configuration:")
    print()
    print(json.dumps(entry, indent=2))
    print()
    print("Add this section to the project's AGENTS.md:")
    print()
    print("## CST help")
    print()
    print(section)
    return 0


if __name__ == "__main__":
    sys.exit(main())
