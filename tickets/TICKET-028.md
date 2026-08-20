# TICKET-028 — Tests: run_health SKIP (no fourseer / no cycles.out), PASS (consistent), FAIL (join gap)

## Title
Deterministic, network-free tests for `loop_doctor.run_health.run_health_check`
must cover the SKIP, PASS, and FAIL paths. The `ai` dir, `cycles.out`, and
`trajectories/` are built under `tmp_path`.

## Evidence
- The Cycle 6 briefing "What to Build" row `tests/`: "Deterministic, network-free
  tests: `run_health` SKIPs when `fourseer` is not importable (patch the import
  to simulate absence); SKIPs when there is no `cycles.out`; PASSes on a
  consistent run (a `cycles.out` whose cycle numbers are contiguous and whose
  trajectory paths exist); FAILs (with a detail naming the gap) when there is a
  cycle-count / cycles.out join gap (e.g. a missing cycle number, or a
  `trajectory_path` referenced in `cycles.out` that does not exist on disk).
  Build the `ai` dir, `cycles.out`, and `trajectories/` under `tmp_path`."
- The `fourseer` import is guarded with `try/except ImportError` inside
  `run_health_check`, so the SKIP-when-absent case is tested by patching
  `sys.modules["fourseer"]` to `None` (mirroring the `spoke_lint` SKIP test in
  `tests/test_prompt.py`).
- The `cycles.out` header format is `========== CYCLE <N>  <HH:MM:SSZ> ==========`
  (an optional project-name prefix is allowed), followed by `OUTER trajectory
  saved to: <path>` and `OUTER outcome: <outcome>` lines (see
  `fourseer.parse.cycles_out`).

## Impact
- Without these tests the run health check is untested; a regression in the
  graceful-degradation or join-gap logic would not be caught.

## Suggestion
Create `tests/test_run_health.py` with:
- SKIP when `fourseer` is not importable (patch `sys.modules["fourseer"]` to
  `None`); detail mentions `fourseer`.
- SKIP when the `ai` dir is missing or has no `cycles.out`; detail mentions
  `cycles.out`.
- PASS on a consistent run: a `cycles.out` with contiguous cycle numbers (e.g.
  1, 2, 3) whose `trajectory_path` basenames exist under `trajectories/`.
- FAIL (detail names the gap) when a cycle number is missing (e.g. 1, 3 — a
  contiguity gap).
- FAIL (detail names the gap) when a `trajectory_path` referenced in
  `cycles.out` does not exist on disk.
- Build the `ai` dir, `cycles.out`, and `trajectories/` under `tmp_path`.
