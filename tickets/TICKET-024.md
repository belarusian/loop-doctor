# TICKET-024 — Tests: run_all order [foundation, protocol, prompt, bash], --check bash, composed no-go

## Title
The registry/CLI tests must be updated for the fourth check. The existing GO
fixtures in `test_checks.py` and `test_cli.py` write a minimal runner prompt
(`"prompt"`) and no `.sh` drivers, so the bash check PASSes on them (no `.sh`
drivers) and the GO tests stay GO — but the `run_all` order assertions and the
`--check` / composed-verdict tests must be updated for the fourth check.

## Evidence
- `tests/test_checks.py` `test_registering_second_check_makes_run_all_return_both_in_stable_order`
  asserts `names == ["foundation", "protocol", "prompt", "second"]`; once `bash` is
  registered it must be `["foundation", "protocol", "prompt", "bash", "second"]`.
- `tests/test_checks.py` `test_run_all_returns_foundation_then_protocol_in_stable_order`
  asserts `names == ["foundation", "protocol", "prompt"]`; it must become
  `["foundation", "protocol", "prompt", "bash"]`.
- `tests/test_cli.py` `test_check_full_run_composes_both_checks` asserts
  `[c["name"] for c in data["checks"]] == ["foundation", "protocol", "prompt"]`; it
  must become `["foundation", "protocol", "prompt", "bash"]`.
- The existing GO fixtures write no `.sh` drivers at the `proj` root, so the bash
  check returns PASS (no `.sh` drivers) and the GO tests remain GO.
- Cycle 5 briefing "What to Build" row `tests/`: "run_all returns
  [foundation, protocol, prompt, bash] in that order; --check bash runs only that
  check; the composed verdict is no-go when bash FAILs".

## Impact
- The suite would go red the moment `bash` is registered (the two order
  assertions), and the new check would be untested at the registry/CLI level.

## Suggestion
- Update `tests/test_checks.py` and `tests/test_cli.py`: the `run_all` order
  assertions to `["foundation", "protocol", "prompt", "bash"]` (and the
  dynamically-registered-check test to include `bash` before `second`); add
  `--check bash` runs only that check; the composed verdict is NO-GO when `bash`
  FAILs (build a `.sh` driver with a syntax error under `tmp_path`).
