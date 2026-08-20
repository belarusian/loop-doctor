"""Run health check for loop-doctor.

The run health check inspects a project's run artifacts (the ``ai`` dir's
``cycles.out`` log and ``trajectories/`` dir) for internal consistency, using
the optional ``fourseer`` library. It reuses
:func:`loop_doctor.project.resolve_ai_dir` to locate the ``ai`` dir (it does not
re-implement resolution).

The check is dependency-free except for the optional ``fourseer`` import, which
is guarded with ``try/except ImportError``: when ``fourseer`` is not installed
the check returns ``Status.SKIP`` (non-blocking) rather than failing. A project
that has no run artifacts yet (no ``ai`` dir, or no ``cycles.out``) is not
broken, so it also SKIPs.

Consistency means: the ``cycles.out`` cycle numbers are contiguous (no missing
cycle number) and every ``trajectory_path`` referenced in ``cycles.out`` names a
trajectory that exists on disk. The cross-source orphan-trajectory check is
delegated to :func:`fourseer.validate_run` (filtered to the
``orphan_trajectory_path`` code, which is the only code that is meaningful when
the gate log / build order are absent); the contiguity check is done here
directly, since ``fourseer`` does not check it.
"""

from __future__ import annotations

from pathlib import Path

from loop_doctor.project import resolve_ai_dir
from loop_doctor.report import Check, Status

# The only ``fourseer.validate_run`` code that is meaningful when the gate log
# and Build Order are absent. The other codes (``cycle_not_in_gate_log``,
# ``gate_cycle_not_in_cycles_out``, ``build_order_range_gap``) fire whenever the
# gate log / build order are missing and are not a run-artifact join gap.
_ORPHAN_CODE = "orphan_trajectory_path"


def _missing_cycle_numbers(cycle_nos: list[int]) -> list[int]:
    """Return the cycle numbers missing from a contiguous 1..max run.

    Given the sorted cycle numbers present in ``cycles.out``, returns the
    numbers in ``1..max(cycle_nos)`` that are absent (a contiguity / join gap).
    Returns ``[]`` when the numbers are contiguous.
    """
    if not cycle_nos:
        return []
    present = set(cycle_nos)
    top = max(present)
    return [n for n in range(1, top + 1) if n not in present]


def run_health_check(project_dir: Path) -> Check:
    """The run health check: the run artifacts are internally consistent.

    Reuses :func:`loop_doctor.project.resolve_ai_dir` (does not re-implement
    resolution). SKIP (non-blocking) with "fourseer not installed" when
    ``fourseer`` is not importable. SKIP with "no cycles.out" when the ``ai``
    dir is missing or has no ``cycles.out`` (a project with no run artifacts yet
    is not broken). Otherwise PASS when the run is consistent; FAIL with a
    detail naming the inconsistency (a missing cycle number, or a referenced
    trajectory path that does not exist on disk).
    """
    ai_dir = resolve_ai_dir(project_dir)

    try:
        import fourseer
    except ImportError:
        return Check("run_health", Status.SKIP, "fourseer not installed")

    cycles_out = ai_dir / "cycles.out"
    if not ai_dir.is_dir() or not cycles_out.is_file():
        return Check("run_health", Status.SKIP, "no cycles.out")

    run = fourseer.load_run(ai_dir)
    if not run.cycles:
        return Check("run_health", Status.SKIP, "no cycles.out")

    problems: list[str] = []

    # (1) Contiguity: the cycles.out cycle numbers must be contiguous.
    missing = _missing_cycle_numbers([c.cycle_no for c in run.cycles])
    if missing:
        problems.append("missing cycle " + ", ".join(str(n) for n in missing))

    # (2) Orphan trajectory: every referenced trajectory_path must exist on disk.
    for issue in fourseer.validate_run(run):
        if issue.code == _ORPHAN_CODE:
            problems.append(issue.detail)

    if problems:
        return Check("run_health", Status.FAIL, "; ".join(problems))
    return Check("run_health", Status.PASS, f"{len(run.cycles)} cycle(s) consistent")
