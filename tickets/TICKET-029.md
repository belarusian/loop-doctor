# TICKET-029 — Tests: run_all order [foundation, protocol, prompt, bash, run_health], --check run_health, composed no-go

## Title
The registry/CLI tests must be updated for the fifth check. The existing GO
fixtures in `test_checks.py` and `test_cli.py` write a minimal runner prompt
(`"prompt"`) and no run artifacts, so the run health check SKIPs on them (no
`cycles.out`) and the GO tests stay GO — but the `run_all` order assertions and
the `--check` / composed-verdict tests must be updated for the fifth check.

## Evidence
- `tests/test_checks.py`
  `test_registering_second_check_makes_run_all_return_both_in_stable_order`
  asserts `names == ["foundation", "protocol", "prompt", "bash", "second"]`; once
  `run_health` is registered it must be
  `["foundation", "protocol", "prompt", "bash", "run_health", "second"]`.
- `tests/test_checks.py`
  `test_run_all_returns_foundation_then_protocol_in_stable_order` asserts
  `names == ["foundation", "protocol", "prompt", "bash"]`; it must become
  `["foundation", "protocol", "prompt", "bash", "run_health"]`.
- `tests/test_cli.py` `test_check_full_run_composes_both_checks` asserts
  `[c["name"] for c in data["checks"]] == ["foundation", "protocol", "prompt",
  "bash"]`; it must become
  `["foundation", "protocol", "prompt", "bash", "run_health"]`.
- The existing GO fixtures write no `cycles.out` in the `ai` dir, so the run
  health check returns SKIP (no `cycles.out`) and the GO tests remain GO.
- Cycle 6 briefing "What to Build" row `tests/`: the run health check must be
  exercised at the registry/CLI level too.

## Impact
- The suite would go red the moment `run_health` is registered (the two order
  assertions), and the new check would be untested at the registry/CLI level.

## Suggestion
- Update `tests/test_checks.py` and `tests/test_cli.py`: the `run_all` order
  assertions to `["foundation", "protocol", "prompt", "bash", "run_health"]`
  (and the dynamically-registered-check test to include `run_health` before
  `second`); add `--check run_health` runs only that check; the composed verdict
  is NO-GO when `run_health` FAILs (build a `cycles.out` with a join gap under
  `tmp_path`).
