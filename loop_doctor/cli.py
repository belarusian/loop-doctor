"""Command-line entrypoint for loop-doctor.

Provides the ``check`` subcommand: resolve the project, run the
foundation check, and render the report (text by default, JSON with
``--json``). Exit codes: 0 = go, 1 = no-go, 2 = usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loop_doctor.project import resolve_project
from loop_doctor.report import Check, Report, Status, exit_code, render_json, render_text


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with a single ``check`` subcommand."""
    parser = argparse.ArgumentParser(prog="loop-doctor")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run the pre-flight readiness check")
    check.add_argument("project_dir", help="the proj dir or its parent")
    check.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser


def run_check(project_dir: Path) -> Report:
    """Build a Report with a single ``foundation`` check.

    The check passes when the ``ai`` dir resolves and both the gate log
    and the runner prompt are located; otherwise it fails with a detail.
    """
    ai_dir, three = resolve_project(Path(project_dir))
    if three.gate_log is not None and three.runner_prompt is not None:
        check = Check("foundation", Status.PASS, f"ai dir {ai_dir}")
    else:
        missing = []
        if three.gate_log is None:
            missing.append("gate log")
        if three.runner_prompt is None:
            missing.append("runner prompt")
        check = Check("foundation", Status.FAIL, "missing: " + ", ".join(missing))
    return Report(checks=[check])


def main(argv: list[str] | None = None) -> int:
    """Parse args, run the check, print the report, and return the exit code.

    A usage error (argparse) yields 2; a go report yields 0; a no-go
    report yields 1.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return 0 if code is None else int(code)
    report = run_check(Path(args.project_dir))
    if args.json:
        sys.stdout.write(render_json(report))
    else:
        sys.stdout.write(render_text(report))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
