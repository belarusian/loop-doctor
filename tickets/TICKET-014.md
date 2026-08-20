# TICKET-014 — Tests: run_all order, --check protocol, composed no-go verdict, and existing GO fixtures

## Title
The registry-order, CLI `--check protocol`, and composed-verdict behaviors must be
tested, and the existing GO fixtures in `test_checks.py` and `test_cli.py` use a
minimal gate log (`"gate"`) that will now FAIL the protocol check, flipping those GO
tests to NO-GO.

## Evidence
- `tests/test_checks.py` `_make_ai_dir` writes the gate log as the literal
  `"gate"` (no title line, no THE SEED block). Once `protocol` is registered,
  `run_all` includes it and it FAILs, so `test_run_all_returns_foundation_check`,
  `test_composed_report_carries_single_aggregate_verdict_go`, and
  `test_registering_second_check_makes_run_all_return_both_in_stable_order` (which
  asserts `names == ["foundation", "second"]`) break.
- `tests/test_cli.py` `_make_ai_dir` also writes `"gate"`; the GO tests
  (`test_check_returns_go_when_files_present`, `test_check_json_output_parses`,
  `test_check_from_proj_dir`, `test_go_report_returns_zero`) break.
- Cycle 3 briefing "What to Build" row `tests/`: "run_all returns [foundation,
  protocol] in that order; --check protocol runs only that check; the composed verdict
  is no-go when protocol FAILs."

## Impact
- The suite would go red the moment `protocol` is registered, even though the
  behavior is correct — the fixtures are simply not well-formed gate logs.

## Suggestion
- Update the `_make_ai_dir` helpers in `test_checks.py` and `test_cli.py`
  to write a well-formed gate log (a `# ...` title line and a `## THE SEED`
  fenced block) so the GO fixtures stay GO.
- Add tests: `run_all` returns `[foundation, protocol]` in that exact order;
  `--check protocol` runs only the protocol check; the composed verdict is NO-GO
  when `protocol` FAILs (e.g. a malformed gate log).
