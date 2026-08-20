"""Bash syntax check for loop-doctor.

The bash check validates the syntax of the ``*.sh`` driver scripts that live
directly in a project's ``proj`` dir. It reuses
:func:`loop_doctor.project.resolve_proj_dir` to locate the ``proj`` dir (it does
not re-implement resolution) and shells out to ``bash -n`` (parse-only, no
execution) on each script. It is dependency-free (no spoke-lint / fourseer).

The check is a pure syntax gate: it never runs the scripts, so a driver that
parses cleanly but would fail at runtime still passes here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loop_doctor.project import resolve_proj_dir
from loop_doctor.report import Check, Status


def _first_stderr_line(stderr: str) -> str:
    """Return the first non-empty line of ``stderr``, or ``""`` if none."""
    for line in stderr.splitlines():
        if line.strip():
            return line.strip()
    return ""


def bash_check(project_dir: Path) -> Check:
    """The bash check: every ``*.sh`` driver in the ``proj`` dir parses cleanly.

    Reuses :func:`loop_doctor.project.resolve_proj_dir` (does not re-implement
    resolution). Finds the ``*.sh`` files directly in the ``proj`` dir (sorted,
    deterministic) and runs ``bash -n`` on each. PASS with detail
    ``"no .sh drivers"`` when there are none. PASS when every script parses
    cleanly. FAIL with a detail naming the offending script(s) and the first
    ``bash -n`` stderr line.
    """
    proj_dir = resolve_proj_dir(project_dir)
    scripts = sorted(
        p for p in proj_dir.glob("*.sh") if p.is_file()
    ) if proj_dir.is_dir() else []

    if not scripts:
        return Check("bash", Status.PASS, "no .sh drivers")

    offenders: list[str] = []
    first_error = ""
    for script in scripts:
        result = subprocess.run(
            ["bash", "-n", str(script)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            offenders.append(script.name)
            if not first_error:
                first_error = _first_stderr_line(result.stderr)

    if not offenders:
        return Check("bash", Status.PASS, f"{len(scripts)} driver(s) parse cleanly")
    detail = "syntax error in: " + ", ".join(offenders)
    if first_error:
        detail += f" — {first_error}"
    return Check("bash", Status.FAIL, detail)
