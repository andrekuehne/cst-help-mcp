"""The `cst-help` command line."""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Sequence
from pathlib import Path

from cst_help_mcp.errors import CstHelpError

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

    instructions = commands.add_parser(
        "instructions", help="print the Release folder and the AGENTS.md section to add to a project"
    )
    instructions.add_argument("--kb", type=Path, required=True, help="the Knowledge Base folder")
    instructions.add_argument("--release", help="the Release to consult (default: the newest)")
    instructions.set_defaults(run=_instructions)
    return parser


def _build(args: argparse.Namespace) -> int:
    from cst_help_mcp.build import build_collection

    result = build_collection(args.config, args.collection, strict=args.strict)
    report = result.report
    print(
        f"Built {args.collection}: {report.documents} Documents,"
        f" {report.api_entries} API Entries, {report.assets} Assets (Build {result.build_id})"
    )
    print(
        f"  Documents: discovered {report.discovered}, converted {report.converted},"
        f" skipped {report.skipped}, failed {report.failed}; {report.aliases} were Aliases"
    )
    print(
        f"  unresolved links {report.unresolved_links}, missing anchors {report.missing_anchors},"
        f" missing Assets {len(report.missing_assets)},"
        f" unsupported items {sum(report.unsupported.values())},"
        f" unpaired math delimiters {len(report.unpaired_math)}"
    )
    for failure in report.failures:
        print(f"  failed: {failure.source}: {failure.error}")
    if not report.complete:
        print(f"The Knowledge Base is incomplete; see {result.report_path}, or rebuild with --strict.")
    return 0


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


def _instructions(args: argparse.Namespace) -> int:
    from cst_help_mcp.instructions import agents_section, release_folders

    folders = release_folders(args.kb.resolve(), args.release)
    print(f"The Knowledge Base of Release {folders[0].release}:")
    for folder in folders:
        print(f"  {folder.path}")
    print()
    print("Add this section to the project's AGENTS.md:")
    print()
    print("## CST help")
    print()
    print(agents_section(folders), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
