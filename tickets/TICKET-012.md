# TICKET-012 — CLI must run --check protocol and reflect both checks in the aggregate verdict

## Title
The CLI must support `--check protocol` and its aggregate verdict must reflect both
the `foundation` and `protocol` checks. No API change is expected, but the
existing exit-code contract (0 go / 1 no-go / 2 usage error) must still hold now that
`run_all` composes two checks.

## Evidence
- `loop_doctor/cli.py` `run_check(project_dir, check=None)` already composes the
  `Report` from `checks_mod.run_all` (or `run_one` when `check` is set),
  so once `protocol` is registered, `--check protocol` and the full run pick it
  up automatically.
- `main` maps a non-existent `project_dir` and an unknown `--check` name to
  exit 2, and `exit_code(report)` maps go->0 / no-go->1.
- Cycle 3 briefing "What to Build" row `loop_doctor/cli.py`: "No API change expected;
  `--check protocol` must now work and the aggregate verdict must reflect both
  checks. Verify the existing exit-code contract still holds."

## Impact
- If the protocol check is not registered, `--check protocol` is a usage error
  (exit 2) and the full run's verdict ignores gate-log structure.
- The exit-code contract must be re-verified: a well-formed project is GO (0), a
  malformed project is NO-GO (1), and a non-existent dir / unknown check is still 2.

## Suggestion
In `loop_doctor/cli.py`:
- No code change is strictly required if the registry is updated; verify
  `--check protocol` runs only that check and the full run composes both.
- Verify the exit-code contract: well-formed -> 0, malformed -> 1, non-existent dir ->
  2, unknown check -> 2.
Add deterministic, network-free tests: `--check protocol` runs only the protocol
check; the composed verdict is NO-GO when `protocol` FAILs; the exit-code contract
still holds.
