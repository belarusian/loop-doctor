# TICKET-013 — Tests: protocol_check PASS/FAIL cases are not covered

## Title
There are no tests for the new `protocol_check`. The PASS path (well-formed 3-file
set) and each FAIL path (missing gate log, missing runner prompt, absent seed block,
gate log lacking a title line) must be covered with deterministic, network-free tests.

## Evidence
- `tests/` has no `test_protocol.py`. Existing tests cover `project`,
  `checks`, `cli`, `report`, `pyproject`, and a smoke test.
- `tests/test_project.py` already builds well-formed gate logs via a `GATE_LOG`
  constant (a `# ...` title line, a `## THE SEED` fenced block) and a
  `_make_ai_dir` helper with `gate`/`seed_block` toggles — a useful
  pattern to reuse.
- Cycle 3 briefing "What to Build" row `tests/`: "protocol PASSes on a well-formed
  3-file set; FAILs (with the right detail) when the gate log is missing, the runner
  prompt is missing, the seed block is absent, or the gate log lacks a title line."

## Impact
- Without these tests the protocol check's FAIL details are unverified, and a regression
  that silently flips a FAIL to a PASS (or vice versa) would go undetected.

## Suggestion
Add `tests/test_protocol.py` with deterministic, network-free tests:
- PASS on a well-formed 3-file set (gate log with title + THE SEED block, runner
  prompt present).
- FAIL with a detail naming the missing gate log when the gate log is absent.
- FAIL with a detail naming the missing runner prompt when it is absent.
- FAIL with a detail naming the absent seed block when the gate log has no THE SEED
  block.
- FAIL with a detail naming the missing title line when the gate log has no `# ...`
  line.
