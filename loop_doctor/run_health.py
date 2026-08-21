"""Run health check for loop-doctor.

The run health check inspects a project's run artifacts (the ``ai`` dir's
``cycles*.out`` logs and ``trajectories/`` dir) for internal consistency, using
the optional ``fourseer`` library. It reuses
:func:`loop_doctor.project.resolve_ai_dir` to locate the ``ai`` dir (it does not
re-implement resolution).

The check is dependency-free except for the optional ``fourseer`` import, which
is guarded with ``try/except ImportError``: when ``fourseer`` is not installed
the check returns ``Status.SKIP`` (non-blocking) rather than failing. A project
that has no run artifacts yet (no ``ai`` dir, or no ``cycles*.out``) is not
broken, so it also SKIPs.

Consistency means: the cycle numbers are contiguous (no missing cycle number)
and every ``trajectory_path`` referenced in the ``cycles*.out`` logs names a
trajectory that exists on disk. The contiguity check is computed over the
**union** of the cycle markers found in *every* ``cycles*.out`` artifact in the
``ai`` dir (a rotated / segmented history such as ``cycles.out`` +
``cycles-15.out`` is one logical run, not a gap). The cross-source
orphan-trajectory check is delegated to :func:`fourseer.validate_run` (filtered
to the ``orphan_trajectory_path`` code, which is the only code that is
meaningful when the gate log / build order are absent); the contiguity check is
done here directly, since ``fourseer`` does not check it. A cycle number that
is genuinely absent from *all* ``cycles*.out`` artifacts is reported honestly
as a FAIL (naming the missing number) — coverage is never invented.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from loop_doctor.project import resolve_ai_dir
from loop_doctor.report import Check, Status

if TYPE_CHECKING:
    from fourseer.models import CycleRecord

# The only ``fourseer.validate_run`` code that is meaningful when the gate log
# and Build Order are absent. The other codes (``cycle_not_in_gate_log``,
# ``gate_cycle_not_in_cycles_out``, ``build_order_range_gap``) fire whenever the
# gate log / build order are missing and are not a run-artifact join gap.
_ORPHAN_CODE = "orphan_trajectory_path"


def _missing_cycle_numbers(cycle_nos: list[int]) -> list[int]:
    """Return the cycle numbers missing from a contiguous 1..max run.

    Given the sorted cycle numbers present in the ``cycles*.out`` logs, returns
    the numbers in ``1..max(cycle_nos)`` that are absent (a contiguity / join
    gap). Returns ``[]`` when the numbers are contiguous.
    """
    if not cycle_nos:
        return []
    present = set(cycle_nos)
    top = max(present)
    return [n for n in range(1, top + 1) if n not in present]


def _union_cycles(ai_dir: Path) -> list[CycleRecord]:
    """Return the union of cycle records across all ``cycles*.out`` files.

    Globs ``cycles*.out`` in ``ai_dir`` (sorted, deterministic), parses each
    with ``fourseer.parse_cycles_out``, and dedupes by ``cycle_no`` (the first
    occurrence wins). Returns ``[]`` when no file parses to a cycle. This is
    what makes a rotated / segmented history (``cycles.out`` + ``cycles-15.out``)
    read as one logical run rather than a contiguity gap.
    """
    import fourseer

    seen: dict[int, CycleRecord] = {}
    for path in sorted(ai_dir.glob("cycles*.out")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for rec in fourseer.parse_cycles_out(text):
            seen.setdefault(rec.cycle_no, rec)
    return list(seen.values())


def run_health_check(project_dir: Path) -> Check:
    """The run health check: the run artifacts are internally consistent.

    Reuses :func:`loop_doctor.project.resolve_ai_dir` (does not re-implement
    resolution). SKIP (non-blocking) with "fourseer not installed" when
    ``fourseer`` is not importable. SKIP with "no cycles.out" when the ``ai``
    dir is missing or no ``cycles*.out`` artifact parses to a cycle (a project
    with no run artifacts yet is not broken). Otherwise PASS when the run is
    consistent; FAIL with a detail naming the inconsistency (a missing cycle
    number, or a referenced trajectory path that does not exist on disk).

    Contiguity is computed over the union of the cycle markers in *every*
    ``cycles*.out`` artifact in the ``ai`` dir, so a rotated / segmented
    history does not produce a false gap. A cycle number genuinely absent from
    all artifacts is reported honestly (FAIL, naming the number).
    """
    ai_dir = resolve_ai_dir(project_dir)

    try:
        import fourseer
    except ImportError:
        return Check("run_health", Status.SKIP, "fourseer not installed")

    if not ai_dir.is_dir():
        return Check("run_health", Status.SKIP, "no cycles.out")

    # Load the trajectories (and the rest of the run) once; the contiguity and
    # orphan checks below operate on the union of cycle markers across all
    # cycles*.out artifacts.
    run = fourseer.load_run(ai_dir)
    cycles = _union_cycles(ai_dir)
    if not cycles:
        return Check("run_health", Status.SKIP, "no cycles.out")

    # Rebuild the run with the unioned cycles so the orphan-trajectory check
    # validates every referenced trajectory (including those named in a
    # rotated segment) against the loaded trajectories.
    combined = replace(run, cycles=cycles)

    problems: list[str] = []

    # (1) Contiguity: the unioned cycle numbers must be contiguous.
    missing = _missing_cycle_numbers([c.cycle_no for c in cycles])
    if missing:
        problems.append("missing cycle " + ", ".join(str(n) for n in missing))

    # (2) Orphan trajectory: every referenced trajectory_path must exist on disk.
    for issue in fourseer.validate_run(combined):
        if issue.code == _ORPHAN_CODE:
            problems.append(issue.detail)

    if problems:
        return Check("run_health", Status.FAIL, "; ".join(problems))
    return Check("run_health", Status.PASS, f"{len(cycles)} cycle(s) consistent")
