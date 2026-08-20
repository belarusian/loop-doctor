# TICKET-027 — CLI: --check run_health works and the aggregate verdict reflects all five checks

## Title
The CLI must support `--check run_health` (running only that check) and the
aggregate verdict must reflect all five checks. The existing exit-code contract
(0 go / 1 no-go / 2 usage error) must still hold. No API change is expected.

## Evidence
- `loop_doctor/cli.py` `main` maps a non-existent `project_dir` and an unknown
  `--check` name to exit 2, and otherwise returns `exit_code(report)` (0 go /
  1 no-go). `run_check(project_dir, check)` composes a `Report` from the registry
  (all checks, or a single named check via `--check NAME`).
- Once `run_health` is registered (TICKET-026), `--check run_health` resolves via
  `checks_mod.run_one("run_health", project_dir)` and the full run composes all
  five checks.
- Cycle 6 briefing "What to Build" row `loop_doctor/cli.py`: "No API change
  expected; `--check run_health` must now work and the aggregate verdict must
  reflect all five checks. Verify the existing exit-code contract still holds."

## Impact
- If the CLI is not verified, `--check run_health` could silently 404 (exit 2)
  or the aggregate verdict could miss the run health check.

## Suggestion
- No code change to `cli.py` is expected (the registry-driven `run_check` picks
  up the new check automatically). Verify:
  - `--check run_health` runs only that check (JSON `checks` list is
    `["run_health"]`).
  - a full `check` run composes all five checks in stable order.
  - the exit-code contract (0 go / 1 no-go / 2 usage error) is preserved.
