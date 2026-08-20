# TICKET-033 — No endpoint tests: PASS/FAIL behavior of the endpoint check is untested

## Title
There is no `tests/test_endpoint.py`. The endpoint check's PASS/FAIL behavior is
untested: PASS when all endpoints are reachable (probe True); FAIL (detail names
the down endpoint) when one endpoint is down; FAIL when both are down. The tests
must be deterministic and network-free, overriding the probe per-test with
monkeypatch.

## Evidence
- `ls tests/` — no `test_endpoint.py`.
- Cycle 7 briefing "What to Build" row `tests/test_endpoint.py` (NEW):
  "Deterministic, network-free tests: PASS when all endpoints reachable (probe
  True); FAIL (detail names the down endpoint) when one endpoint is down; FAIL
  when both are down. Override the probe per-test with monkeypatch."
- Rule 4: patch the function (`loop_doctor.endpoint._probe`), not a constructor.

## Impact
- The new capability has no direct coverage; regressions in the PASS/FAIL logic or
  the detail string would go undetected.

## Suggestion
Create `tests/test_endpoint.py` with network-free tests that override
`loop_doctor.endpoint._probe` per-test via `monkeypatch.setattr`:
- PASS when the probe returns True for both endpoints (detail "<n> endpoint(s)
  reachable").
- FAIL when the probe returns False for exactly one endpoint (detail names that
  endpoint, e.g. "unreachable: 192.168.1.161:8081").
- FAIL when the probe returns False for both endpoints (detail names both).
