# TICKET-068: run_health must union cycle markers across ALL `cycles*.out` artifacts

## Capability
The run_health check (check 5) must compute contiguity over the **union** of
cycle markers found in every `cycles*.out` artifact in the `ai` dir, so a
rotated/segmented history (e.g. `cycles.out` + `cycles-15.out`) does not
produce a false contiguity gap. It must still honestly FAIL when cycles are
genuinely absent from disk, and SKIP when there are no run artifacts at all.

## Evidence
- `loop_doctor/run_health.py:70-81` — the check reads only `ai/cycles.out`
  (via `fourseer.load_run(ai_dir)`) and computes
  `_missing_cycle_numbers([c.cycle_no for c in run.cycles])`.
- `fourseer/load.py:64-76` (`_find_cycles_out`) returns the **first**
  `cycles*.out` only: exact `cycles.out` if present, else the first sorted
  `cycles*.out` glob match. A second segment (`cycles-15.out`) is never read.
- Verified on this machine (segmented history):
  - `ai/cycles.out` (symlink → `../cycles.out`) contains CYCLE 13 and CYCLE 14.
  - `cycles-15.out` (project root) contains CYCLE 15.
  - Union of markers = {13, 14, 15} → contiguous, no gap.
  - But `load_run` sees only {13, 14}, so
    `_missing_cycle_numbers([13, 14])` = `[1, 2, ..., 12]` → the check FAILs
    with "missing cycle 1, 2, ..., 12" — a false contiguity gap.

## Impact
Any project whose driver rotates or segments its `cycles.out` (a real,
documented pattern — see `JUNIOR.md`: `cycles-v5.out`, the `ai/cycles.out`
symlink convention) is reported as broken by run_health even when the run is
fully contiguous. The check produces false FAILs on healthy runs, eroding
trust in the go/no-go verdict.

## Suggestion
- In `run_health_check`, gather cycle markers from **all** `cycles*.out`
  files in `ai_dir` (glob `cycles*.out`, sorted, dedupe by `cycle_no`), not
  just the single file `load_run` picks. Parse each with
  `fourseer.parse_cycles_out` (already exported at `fourseer/__init__.py:48`)
  and union the `cycle_no` set before calling `_missing_cycle_numbers`.
- Keep the SKIP semantics honest: SKIP "no cycles.out" when there are no
  `cycles*.out` files at all (or none parse to a cycle); do NOT SKIP when
  markers exist but are genuinely gapped.
- Keep the orphan-trajectory check correct under the union: build the
  `Run.cycles` list from the union (or run the orphan check per-segment and
  merge), so a trajectory referenced in `cycles-15.out` is still validated
  against the loaded trajectories.
- Update the `run_health.py` module docstring (lines 1-22) and
  `docs/architecture.md` capability 5 to state contiguity is computed over
  the union of all `cycles*.out` artifacts.
- Add tests in `tests/test_run_health.py`:
  - a segmented history (`cycles.out` = 13,14; `cycles-15.out` = 15) → PASS
    (no false gap);
  - a genuinely gapped union (e.g. 13,15 across two files, 14 absent) → FAIL
    naming cycle 14;
  - no `cycles*.out` at all → SKIP.

## Acceptance
- A segmented-but-contiguous run PASSES run_health (no false "missing cycle").
- A genuinely missing cycle number across the union still FAILs and names it.
- No `cycles*.out` artifacts → SKIP (unchanged).
- Gate green: `pytest tests/ -x -q`, `ruff check loop_doctor/`,
  `mypy loop_doctor/ --ignore-missing-imports`.
