# TICKET-034 — run_all / --check assertions omit endpoint; no endpoint no-go / single-check tests

## Title
`tests/test_checks.py` and `tests/test_cli.py` assert the full check list as
`[foundation, protocol, prompt, bash, run_health]` and have no endpoint-specific
tests. They must be updated to include `endpoint` in the full-list assertions
(now `[foundation, protocol, prompt, bash, run_health, endpoint]`), and new tests
added: a NO-GO-when-endpoint-fails test (override the probe to False) and a
`--check endpoint` single-check test.

## Evidence
- `tests/test_checks.py` asserts
  `names == ["foundation", "protocol", "prompt", "bash", "run_health"]` in
  `test_run_all_returns_foundation_then_protocol_in_stable_order` and
  `["foundation", "protocol", "prompt", "bash", "run_health", "second"]` in
  `test_registering_second_check_makes_run_all_return_both_in_stable_order`.
- `tests/test_cli.py` asserts
  `names == ["foundation", "protocol", "prompt", "bash", "run_health"]` in
  `test_check_full_run_composes_both_checks`.
- Cycle 7 briefing "What to Build" row `tests/test_checks.py` + `tests/test_cli.py`:
  "Update the run_all / --check full-list assertions to include endpoint (now
  [foundation, protocol, prompt, bash, run_health, endpoint]); add a
  NO-GO-when-endpoint-fails test (override probe to False) and a --check endpoint
  single-check test."

## Impact
- The full-list assertions would fail once `endpoint` is registered, and the
  endpoint check's participation in the aggregate verdict and the `--check`
  filter would be untested.

## Suggestion
- Update the full-list assertions in `test_checks.py` and `test_cli.py` to include
  `endpoint` (now `[foundation, protocol, prompt, bash, run_health, endpoint]`).
- Add a NO-GO-when-endpoint-fails test (override `loop_doctor.endpoint._probe` to
  return False) asserting the composed verdict is NO-GO / exit 1.
- Add a `--check endpoint` single-check test asserting only the `endpoint` check
  runs and PASSes (probe True via the conftest fixture).
