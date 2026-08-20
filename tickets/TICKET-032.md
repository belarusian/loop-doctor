# TICKET-032 — No conftest autouse fixture: endpoint probe would hit the real network

## Title
There is no `tests/conftest.py`. Once the endpoint check is registered in
`run_all`, every existing GO fixture that calls `run_all` (or the CLI full run)
would perform a real TCP connect to the two LLM endpoints, making the suite
network-dependent and non-deterministic (and failing in a hermetic CI). An autouse
fixture that patches `loop_doctor.endpoint._probe` to return `True` is required so
the existing GO fixtures stay GO deterministically without a real network probe.

## Evidence
- `ls tests/` — no `conftest.py`.
- `tests/test_checks.py` and `tests/test_cli.py` have many GO fixtures that call
  `run_all` / `main(["check", ...])` and assert `verdict is True` / exit 0.
- Cycle 7 briefing "What to Build" row `tests/conftest.py` (NEW): "An autouse
  fixture that patches `loop_doctor.endpoint._probe` to return True (endpoints up)
  for every test, so the existing GO fixtures stay GO deterministically without a
  real network probe."

## Impact
- Without it, the suite becomes network-dependent and the existing GO fixtures
  would be flaky or fail in a hermetic environment.

## Suggestion
Create `tests/conftest.py` with an autouse pytest fixture that patches
`loop_doctor.endpoint._probe` to a function returning `True` for the duration of
every test (use `monkeypatch.setattr` or `unittest.mock.patch`), restoring the
original after each test.
