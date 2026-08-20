# TICKET-035 — No explicit aggregate go/no-go tests across all six checks

## Title
`tests/test_report.py` has generic verdict tests (a/b/c) but no EXPLICIT
aggregate go/no-go tests built from the real six-check `run_all` output. There is
no test that a Report built from `run_all` is GO when every check is
PASS/SKIP/WARN and NO-GO when ANY single one of the six checks is FAIL
(parametrized over which check fails), and no test that the verdict is
independent of check insertion order.

## Evidence
- `tests/test_report.py` tests use synthetic `Check("a", ...)`, `Check("b", ...)`
  names, not the six real check names.
- `tests/test_checks.py` has per-check no-go tests but no single parametrized
  "any one of the six fails -> NO-GO" test and no order-independence test.
- Cycle 8 briefing "What to Build" row `tests/test_report.py (extend)`: "Explicit
  aggregate go/no-go tests across all six checks: a Report built from run_all is
  GO when every check is PASS/SKIP/WARN and NO-GO when ANY single check is FAIL
  (parametrize over which check fails). Verify the verdict is independent of
  check insertion order (reorder the same six checks -> same verdict)."

## Impact
- The go/no-go aggregate is the core contract of the tool; it is only covered
  indirectly. A regression that made the verdict depend on check order, or that
  let one specific check's FAIL be ignored, would not be caught.

## Suggestion
- Add a helper that builds the six named checks in a given status map.
- Add a parametrized test: for each of the six check names, set that check to
  FAIL (others PASS) and assert `Report(checks=...).verdict is False`.
- Add a test: all six PASS/SKIP/WARN -> verdict True.
- Add an order-independence test: build the same six checks in two different
  insertion orders and assert the verdict (and summary) are identical.
