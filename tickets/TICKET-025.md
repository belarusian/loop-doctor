# TICKET-025 — No run health check: run artifacts (cycles.out + trajectories) are not inspected

## Title
There is no RUN HEALTH check. The Cycle 6 target `loop_doctor/run_health.py` does
not exist. Nothing inspects the project's run artifacts (the `ai` dir's
`cycles.out` log and `trajectories/` dir) for consistency. The `foundation`,
`protocol`, `prompt`, and `bash` checks only confirm the 3-file set is located and
well-formed, that the runner prompt's spoke invocations are valid, and that the
root `.sh` drivers parse; they never check that the recorded run is internally
consistent (contiguous cycle numbers, every referenced trajectory present on disk).

## Evidence
- `ls loop_doctor/` — contains `__init__.py`, `bash_check.py`, `checks.py`,
  `cli.py`, `project.py`, `prompt.py`, `protocol.py`, `report.py`. No
  `run_health.py`.
- `loop_doctor/checks.py` registers `foundation`, `protocol`, `prompt`, `bash`.
  `run_all` returns `[foundation, protocol, prompt, bash]`.
- `loop_doctor/project.py` provides `resolve_ai_dir(project_dir) -> Path` (accepts
  the `proj` dir or its parent and returns the sibling `ai` dir). This is the
  anchor the run health check uses to find `cycles.out` and `trajectories/`.
- The `fourseer` library (optional `full` extra, importable as `fourseer`) exposes
  `load_run(ai_dir, repo_path=None) -> Run` (discovers `trajectories/`, the gate
  log, and `cycles.out` by pattern; missing optional files yield empty results),
  `parse_cycles_out(text) -> list[CycleRecord]` (each `CycleRecord` has
  `cycle_no`, `timestamp`, `outcome`, `trajectory_path`), and
  `validate_run(run) -> list[ConsistencyIssue]` (each `ConsistencyIssue` has
  `code`, `cycle_no`, `detail`).
- Cycle 6 briefing "What to Build" row `loop_doctor/run_health.py` (NEW): "a
  `run_health_check(project_dir) -> Check` named `run_health`. Reuse
  `project.resolve_ai_dir` (do NOT re-implement resolution) to locate the `ai`
  dir, then use the `fourseer` library to analyze the run artifacts there. The
  `ai` dir holds `cycles.out` (the per-cycle driver log) and a `trajectories/`
  dir. Graceful degradation: if `fourseer` is not importable, return
  `Status.SKIP` (non-blocking) with a detail like 'fourseer not installed'
  (guard the import with try/except ImportError); if the `ai` dir is missing or
  has no `cycles.out`, SKIP with a detail like 'no cycles.out' (a project with no
  run artifacts yet is not broken). Otherwise PASS when the run is consistent;
  FAIL with a detail naming the inconsistency."

## Impact
- The fourth of the five real capabilities (Cycles 3-8) is absent. A run whose
  `cycles.out` has a missing cycle number, or that references a `trajectory_path`
  that does not exist on disk, would still be reported GO, masking an inconsistent
  or truncated run.

## Suggestion
Create `loop_doctor/run_health.py` with:
- `run_health_check(project_dir: Path) -> Check` named `run_health`.
- Resolve the `ai` dir via `loop_doctor.project.resolve_ai_dir` (do NOT
  re-implement resolution).
- Guard `import fourseer` with `try/except ImportError`; on failure return
  `Check("run_health", Status.SKIP, "fourseer not installed")`.
- If the `ai` dir is missing or has no `cycles.out`, return
  `Check("run_health", Status.SKIP, "no cycles.out")`.
- Otherwise use `fourseer` to analyze the run: prefer `fourseer.load_run(ai_dir)`
  + `fourseer.validate_run(run)` for cross-source consistency, and additionally
  check that the `cycles.out` cycle numbers are contiguous (a missing cycle number
  is a join gap) and that every referenced `trajectory_path` exists on disk.
- PASS when the run is consistent; FAIL with a detail naming the inconsistency
  (e.g. the missing cycle number, or the missing trajectory path).
- Keep the check dependency-free except for the optional `fourseer` import.
