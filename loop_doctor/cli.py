"""Command-line entrypoint for loop-doctor.

Provides the ``check`` subcommand: resolve the project, run the registered
checks (or a single named check with ``--check``), and render the report
(text by default, JSON with ``--json``). ``--list-checks`` prints the
registered check names and exits 0 without requiring a project dir or running
any check. Exit codes: 0 = go, 1 = no-go, 2 = usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loop_doctor import __version__
from loop_doctor import checks as checks_mod
from loop_doctor.report import Report, exit_code, render_json, render_text


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with a single ``check`` subcommand."""
    parser = argparse.ArgumentParser(prog="loop-doctor")
    parser.add_argument(
        "--version",
        action="version",
        version=f"loop-doctor {__version__}",
        help="print the loop-doctor version and exit",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run the pre-flight readiness check")
    check.add_argument(
        "project_dir",
        nargs="?",
        default=None,
        help="the proj dir or its parent (not required with --list-checks)",
    )
    check.add_argument("--json", action="store_true", help="emit JSON instead of text")
    check.add_argument(
        "--check",
        dest="check",
        metavar="NAME",
        help="run only the named check (e.g. foundation)",
    )
    check.add_argument(
        "--list-checks",
        action="store_true",
        help="print the registered check names (one per line) and exit 0; "
        "no project dir is required and no check is run",
    )
    return parser


def run_check(project_dir: Path, check: str | None = None) -> Report:
    """Build a Report from the check registry.

    When ``check`` is ``None``, every registered check is run (in stable
    registration order). When ``check`` names a registered check, only that
    check is run. The returned ``Report`` carries a single aggregate verdict.
    """
    project_dir = Path(project_dir)
    if check is None:
        result = checks_mod.run_all(project_dir)
    else:
        result = [checks_mod.run_one(check, project_dir)]
    return Report(checks=result)


def main(argv: list[str] | None = None) -> int:
    """Parse args, run the check, print the report, and return the exit code.

    A usage error (argparse, a non-existent project dir, or an unknown
    ``--check`` name) yields 2; a go report yields 0; a no-go report yields 1.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return 0 if code is None else int(code)

    if args.list_checks:
        for name in checks_mod.registered_names():
            sys.stdout.write(name + "\n")
        return 0

    if args.project_dir is None:
        sys.stderr.write("usage error: project dir is required\n")
        return 2

    project_dir = Path(args.project_dir)
    if not project_dir.is_dir():
        sys.stderr.write(f"usage error: project dir does not exist: {project_dir}\n")
        return 2

    if args.check is not None and args.check not in checks_mod.registered_names():
        sys.stderr.write(f"usage error: unknown check: {args.check}\n")
        return 2

    report = run_check(project_dir, args.check)
    if args.json:
        sys.stdout.write(render_json(report))
    else:
        sys.stdout.write(render_text(report))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
