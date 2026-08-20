# TICKET-045 — Exhaustive edge-case tests for loop_doctor/endpoint.py

## Title
Add exhaustive edge-case and branch-coverage tests to tests/test_endpoint.py
so every branch of loop_doctor/endpoint.py is pinned, without changing any
source behavior. The endpoint list must be asserted to be exactly
192.168.1.157:8080 and 192.168.1.161:8081; PASS when all reachable; FAIL when
any one is unreachable (parametrize over which); the exact detail-string format
for both PASS and FAIL; and that the check is independent of the project dir
(it never reads the filesystem). Use the existing endpoint._probe seam
(conftest autouse fixture + monkeypatch.setattr override, Rule 4).

## Evidence
- loop_doctor/endpoint.py defines _ENDPOINTS = (("192.168.1.157", 8080),
  ("192.168.1.161", 8081)), a module-level _probe(host, port, timeout=2.0), and
  endpoint_check(project_dir) that builds unreachable = [f"{host}:{port}" for
  host, port in _ENDPOINTS if not _probe(host, port)], returns FAIL
  "unreachable: " + ", ".join(unreachable) when non-empty, else PASS
  f"{len(_ENDPOINTS)} endpoint(s) reachable".
- tests/test_endpoint.py has 4 tests (pass-all, fail-one, fail-both,
  probe-override). It does not pin the exact endpoint list, the exact detail
  strings, or parametrize over which single endpoint is down.

## Impact
- The exact endpoint set and the exact detail-string format are not pinned; a
  regression that changes an endpoint, a port, or the detail wording would not
  be caught.

## Suggestion
- Assert _ENDPOINTS equals the exact two (host, port) pairs.
- Parametrize the single-down case over index 0 and 1; assert the exact FAIL
  detail string and that the up endpoint is absent.
- Assert the exact PASS detail string and the exact FAIL detail
  "unreachable: 192.168.1.157:8080, 192.168.1.161:8081" when both are down.
- Confirm the check ignores the project dir (pass a nonexistent dir; still
  PASS under the default probe).
