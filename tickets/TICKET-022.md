# TICKET-022 — CLI: --check bash must work and the aggregate verdict must reflect all four checks

## Title
The CLI must expose the new `bash` check. `loop_doctor/cli.py` already composes the
full `Report` from the registry (or a single named check via `--check NAME`) and
maps a non-existent `project_dir` / unknown `--check` name to exit 2. No API change
is expected: once `bash` is registered (TICKET-021), `--check bash` must run only
that check and the aggregate verdict must reflect all four checks. The existing
exit-code contract (0 go / 1 no-go / 2 usage error) must still hold.

## Evidence
- `loop_doctor/cli.py` `run_check(project_dir, check=None)` calls
  `checks_mod.run_all(project_dir)` when `check is None` and
  `[checks_mod.run_one(check, project_dir)]` otherwise. `main` returns 2 for a
  non-existent `project_dir` and for an unknown `--check` name, and
  `exit_code(report)` (0 go / 1 no-go) otherwise.
- `checks_mod.registered_names()` is used to validate the `--check` name; once
  `bash` is registered it is a valid name.
- Cycle 5 briefing "What to Build" row `loop_doctor/cli.py`: "No API change
  expected; `--check bash` must now work and the aggregate verdict must reflect all
  four checks. Verify the existing exit-code contract still holds."

## Impact
- If the CLI were changed incorrectly, `--check bash` could break or the exit-code
  contract could regress.

## Suggestion
- Make no API change to `loop_doctor/cli.py`.
- Verify (via tests) that `--check bash` runs only the bash check, that a full run
  composes all four checks, and that the exit-code contract (0 go / 1 no-go / 2
  usage error) still holds.
