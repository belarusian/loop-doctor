"""Tests for loop_doctor.run_health: the run health check SKIP/PASS/FAIL cases.

All tests are deterministic and network-free. The ``ai`` dir, ``cycles.out``,
and ``trajectories/`` are built under ``tmp_path``. The ``fourseer`` import is
patched to simulate absence for the SKIP-when-uninstalled case. The real-dep
PASS/FAIL tests are guarded with ``pytest.importorskip("fourseer")`` so the
suite is green with or without the ``full`` extra.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from loop_doctor.report import Status
from loop_doctor.run_health import _missing_cycle_numbers, run_health_check

NL = chr(10)


def _write_trajectory(traj_dir: Path, name: str) -> None:
    """Write a minimal trajectory JSON file with the given basename."""
    payload = {"outcome": "exit:task_complete", "messages": [{"role": "user", "content": "x"}]}
    (traj_dir / name).write_text(json.dumps(payload), encoding="utf-8")


def _cycles_out_text(ai_dir: Path, cycle_nos: list[int]) -> str:
    """Build cycles.out text referencing one trajectory per cycle number.

    Each cycle references ``ai/trajectories/trajectory_<NNNN>.json`` (the
    basename is what fourseer correlates against the loaded trajectories).
    """
    lines: list[str] = []
    for n in cycle_nos:
        lines.append(f"========== CYCLE {n}  10:00:{n:02d}Z ==========")
        traj = ai_dir / "trajectories" / f"trajectory_{n:04d}.json"
        lines.append(f"OUTER trajectory saved to: {traj}")
        lines.append("OUTER outcome: exit:task_complete")
    return NL.join(lines) + NL


def _make_ai_dir(
    ai_dir: Path,
    cycle_nos: list[int],
    trajectory_basenames: list[str],
) -> None:
    """Build ``ai_dir`` with a ``cycles.out`` and the given trajectories."""
    ai_dir.mkdir(parents=True, exist_ok=True)
    traj_dir = ai_dir / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)
    for name in trajectory_basenames:
        _write_trajectory(traj_dir, name)
    (ai_dir / "cycles.out").write_text(_cycles_out_text(ai_dir, cycle_nos), encoding="utf-8")


def test_run_health_skips_when_fourseer_not_importable(tmp_path: Path) -> None:
    # A consistent run, but fourseer is not importable -> SKIP.
    _make_ai_dir(tmp_path / "ai", [1, 2, 3], [f"trajectory_{n:04d}.json" for n in (1, 2, 3)])
    with mock.patch.dict(sys.modules, {"fourseer": None}):
        check = run_health_check(tmp_path)
    assert check.name == "run_health"
    assert check.status is Status.SKIP
    assert "fourseer" in check.detail


def test_run_health_skips_when_no_ai_dir(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # No ai dir at all -> no cycles.out -> SKIP.
    check = run_health_check(tmp_path)
    assert check.status is Status.SKIP
    assert "cycles.out" in check.detail


def test_run_health_skips_when_no_cycles_out(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # An ai dir with trajectories but no cycles.out -> SKIP.
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "trajectories").mkdir()
    check = run_health_check(tmp_path)
    assert check.status is Status.SKIP
    assert "cycles.out" in check.detail


def test_run_health_skips_when_cycles_out_is_empty(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # A cycles.out that parses to zero cycles -> SKIP (no cycles.out).
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "trajectories").mkdir()
    (ai_dir / "cycles.out").write_text("", encoding="utf-8")
    check = run_health_check(tmp_path)
    assert check.status is Status.SKIP
    assert "cycles.out" in check.detail


def test_run_health_passes_on_consistent_run(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # Contiguous cycle numbers and every referenced trajectory exists on disk.
    _make_ai_dir(tmp_path / "ai", [1, 2, 3], [f"trajectory_{n:04d}.json" for n in (1, 2, 3)])
    check = run_health_check(tmp_path)
    assert check.name == "run_health"
    assert check.status is Status.PASS
    assert "consistent" in check.detail


def test_run_health_pass_detail_is_exact(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # The PASS detail is pinned exactly: "<n> cycle(s) consistent".
    _make_ai_dir(tmp_path / "ai", [1, 2, 3], [f"trajectory_{n:04d}.json" for n in (1, 2, 3)])
    check = run_health_check(tmp_path)
    assert check.detail == "3 cycle(s) consistent"


def test_run_health_fails_on_missing_cycle_number(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # Cycles 1 and 3 exist but 2 is missing -> contiguity gap -> FAIL.
    _make_ai_dir(tmp_path / "ai", [1, 3], [f"trajectory_{n:04d}.json" for n in (1, 3)])
    check = run_health_check(tmp_path)
    assert check.status is Status.FAIL
    assert "2" in check.detail
    assert "missing cycle" in check.detail


def test_run_health_fails_on_two_missing_cycle_numbers(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # Cycles 1 and 4 exist but 2 and 3 are missing -> both are named.
    _make_ai_dir(tmp_path / "ai", [1, 4], [f"trajectory_{n:04d}.json" for n in (1, 4)])
    check = run_health_check(tmp_path)
    assert check.status is Status.FAIL
    assert "missing cycle 2, 3" in check.detail


def test_run_health_fails_on_missing_trajectory_path(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # Cycles 1, 2, 3 are contiguous but trajectory_0002.json is absent on disk.
    _make_ai_dir(tmp_path / "ai", [1, 2, 3], [f"trajectory_{n:04d}.json" for n in (1, 3)])
    check = run_health_check(tmp_path)
    assert check.status is Status.FAIL
    assert "trajectory_0002.json" in check.detail


def test_run_health_fails_on_join_gap_orphan_trajectory(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # A join gap: cycles.out references a trajectory fourseer cannot see among
    # the loaded trajectories. The orphan detail is surfaced in the FAIL detail.
    _make_ai_dir(tmp_path / "ai", [1, 2, 3], [f"trajectory_{n:04d}.json" for n in (1, 3)])
    check = run_health_check(tmp_path)
    assert check.status is Status.FAIL
    assert "cycle 2 references trajectory" in check.detail
    assert "trajectory_0002.json" in check.detail


def test_run_health_fails_combines_missing_cycle_and_orphan(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # Both a contiguity gap (cycle 2 missing) and an orphan trajectory
    # (trajectory_0003 absent) -> the detail joins both problems with "; ".
    _make_ai_dir(tmp_path / "ai", [1, 3], [f"trajectory_{n:04d}.json" for n in (1,)])
    check = run_health_check(tmp_path)
    assert check.status is Status.FAIL
    assert "missing cycle 2" in check.detail
    assert "trajectory_0003.json" in check.detail
    assert "; " in check.detail


def test_missing_cycle_numbers_empty_list() -> None:
    assert _missing_cycle_numbers([]) == []


def test_missing_cycle_numbers_contiguous() -> None:
    assert _missing_cycle_numbers([1, 2, 3]) == []


def test_missing_cycle_numbers_single_gap() -> None:
    assert _missing_cycle_numbers([1, 3]) == [2]


def test_missing_cycle_numbers_multiple_gaps() -> None:
    assert _missing_cycle_numbers([1, 4]) == [2, 3]


def test_missing_cycle_numbers_unsorted_input() -> None:
    # The helper is order-independent: it works from the set of present numbers.
    assert _missing_cycle_numbers([3, 1]) == [2]
    assert _missing_cycle_numbers([4, 1, 3]) == [2]
