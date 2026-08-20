# TICKET-048 — Exhaustive edge-case tests for loop_doctor/run_health.py

## Title
Add exhaustive edge-case and branch-coverage tests to tests/test_run_health.py
so every branch of loop_doctor/run_health.py is pinned, without changing any
source behavior. Cover: PASS on a consistent cycles.out + trajectories (exact
detail "{n} cycle(s) consistent"); FAIL on a missing cycle number (existing);
SKIP when fourseer is absent (guard the real-dep cases with
pytest.importorskip and keep the mocked-absence case); SKIP when cycles.out is
absent (existing); the join-gap detection (cycles.out references a cycle
fourseer cannot see via an orphan trajectory); the exact detail-string format;
and the _missing_cycle_numbers helper (empty list, contiguous, single gap,
multiple gaps, unsorted input).

## Evidence
- loop_doctor/run_health.py has _ORPHAN_CODE = "orphan_trajectory_path",
  _missing_cycle_numbers(cycle_nos), and run_health_check.
- run_health_check SKIPs "fourseer not installed" when fourseer is not
  importable; SKIPs "no cycles.out" when the ai dir is missing, has no
  cycles.out, or run.cycles is empty; FAILs with "; ".join(problems) where
  problems may include "missing cycle " + ", ".join(...) and the
  orphan_trajectory_path issue details; else PASSes
  f"{len(run.cycles)} cycle(s) consistent".
- tests/test_run_health.py has 6 tests; it does not pin the PASS detail, the
  join-gap (orphan) case, the empty-cycles SKIP, the multi-gap detail, or the
  _missing_cycle_numbers helper.

## Impact
- The PASS detail, the orphan-trajectory join-gap branch, the empty-cycles SKIP,
  the multi-gap detail, and the helper are not pinned.

## Suggestion
- Add a PASS test asserting the exact detail f"{n} cycle(s) consistent".
- Add a FAIL test for a join gap: cycles.out references a trajectory that is
  not among the loaded trajectories (assert the orphan detail is present).
- Add a SKIP test for an ai dir whose cycles.out parses to zero cycles.
- Add a FAIL test with two missing cycle numbers (assert both are named).
- Add unit tests for _missing_cycle_numbers: [] -> [], [1,2,3] -> [],
  [1,3] -> [2], [1,4] -> [2,3], unsorted [3,1] -> [2].
- Guard the real-dep tests with pytest.importorskip("fourseer").
