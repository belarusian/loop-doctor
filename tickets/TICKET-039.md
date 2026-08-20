# TICKET-039 — Verify the CLI exit-code contract holds with all six checks registered

## Title
`loop_doctor/cli.py` must be verified (no API change expected) to still honor the
exit-code contract (0 go / 1 no-go / 2 usage error) with all six checks
registered, and that the JSON `verdict` field is consistent with the exit code.
This is a verification ticket: confirm `main` maps a GO report to 0, a NO-GO
report to 1, and a usage error (non-existent dir / unknown `--check`) to 2, and
that `render_json`'s `verdict` field matches.

## Evidence
- `loop_doctor/cli.py::main` returns `exit_code(report)` (0 go / 1 no-go) and 2
  for a non-existent dir or unknown `--check`.
- `loop_doctor/report.py::exit_code` maps `report.verdict` to 0/1;
  `render_json` emits `"verdict": report.verdict`.
- `loop_doctor/checks.py` registers all six checks
  `[foundation, protocol, prompt, bash, run_health, endpoint]`.
- Cycle 8 briefing "What to Build" row `loop_doctor/cli.py (verify only)`: "No
  API change expected. Verify the exit-code contract (0 go / 1 no-go / 2 usage
  error) still holds with all six checks registered and that the JSON `verdict`
  field is consistent with the exit code."

## Impact
- If the contract drifted (e.g. a check raised, or the JSON verdict disagreed
  with the exit code), the runner and CI would misinterpret results.

## Suggestion
- Verify (via the new tests in TICKET-036) that with all six checks registered the
  exit-code contract holds and the JSON `verdict` field matches the exit code.
- No source change to `cli.py` is expected; if a discrepancy is found, fix it.
