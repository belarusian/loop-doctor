# TICKET-036 — No exit-code contract test across all six checks + JSON verdict consistency

## Title
`tests/test_cli.py` has per-check no-go tests (text output) but no single
parametrized test that forces EACH of the six checks to FAIL and asserts the CLI
exit code is 1 with the JSON `verdict` field `false`, and no test that a full
GO run yields exit 0 with JSON `verdict` `true`. The exit-code contract
(0 go / 1 no-go / 2 usage error) across all six checks and the JSON verdict
consistency (0<->true, 1<->false) are not explicitly covered.

## Evidence
- `tests/test_cli.py` has `test_check_nogo_when_<check>_fails` for each check but
  each asserts only the text `verdict: NO-GO`, not the JSON `verdict` field, and
  they are not parametrized into one contract test.
- No test asserts `data["verdict"] is False` when exit code is 1, or
  `data["verdict"] is True` when exit code is 0, across all six checks.
- Cycle 8 briefing "What to Build" row `tests/test_cli.py (extend)`: "Exit-code
  contract across all six checks: full run -> 0 when all pass/skip; -> 1 when
  exactly one check FAILs (parametrize: force each of the six checks to FAIL via
  the appropriate seam); -> 2 for a non-existent dir and an unknown --check.
  Confirm the JSON verdict field matches the exit code (0<->true, 1<->false)."

## Impact
- The exit-code contract is what CI scripts and the runner rely on. A regression
  that returned the wrong code for one specific check, or that made the JSON
  verdict disagree with the exit code, would not be caught.

## Suggestion
- Add a parametrized test over the six check names that forces each to FAIL via
  its seam (endpoint: monkeypatch `_probe` False; protocol: malformed gate log;
  foundation: empty ai dir; bash: bad .sh driver; prompt: unknown flag;
  run_health: cycles.out with a missing cycle number) and asserts exit 1 and
  JSON `verdict is False`.
- Add a test that a full GO run yields exit 0 and JSON `verdict is True`.
- Add/keep tests for exit 2 on a non-existent dir and an unknown `--check`.
