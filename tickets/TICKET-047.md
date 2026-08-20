# TICKET-047 — Exhaustive edge-case tests for loop_doctor/protocol.py

## Title
Add exhaustive edge-case and branch-coverage tests to tests/test_protocol.py so
every branch of loop_doctor/protocol.py is pinned, without changing any source
behavior. Cover: PASS on a well-formed gate log (exact detail "ai dir
{ai_dir}"); FAIL on a missing gate log (existing); FAIL on a missing runner
prompt (existing); FAIL when both are missing (detail lists both); FAIL on a
missing THE SEED block (existing); FAIL on a missing title line (existing);
FAIL on an unresolvable seed ref (existing); the seed-reference extraction;
malformed/empty gate-log edge cases (empty file, only ## headings, THE SEED
marker with no following fence); and the _has_title_line / _has_seed_block
helpers.

## Evidence
- loop_doctor/protocol.py has _FENCE_RE (three backticks or ~~~),
  _TITLE_RE = re.compile(r"^# \S"), _SEED_MARKER = "THE SEED",
  _has_title_line, _has_seed_block, and protocol_check.
- protocol_check FAILs "missing: " + ", ".join(missing) when the gate log and/or
  runner prompt are absent; FAILs "malformed gate log: unreadable" on
  OSError/UnicodeDecodeError; FAILs "malformed gate log: no title line"; FAILs
  "malformed gate log: no THE SEED block"; FAILs "missing: seed ref"; else
  PASSes f"ai dir {ai_dir}".
- tests/test_protocol.py has 6 tests; it does not pin the PASS detail, the
  both-missing detail, the empty/unreadable gate-log cases, the ~~~ fence
  variant, or the helper functions.

## Impact
- The PASS detail, the both-missing detail, the empty/unreadable gate-log
  branches, the ~~~ fence variant, and the helper functions are not pinned.

## Suggestion
- Add a PASS test asserting the exact detail f"ai dir {ai_dir}".
- Add a FAIL test with both gate log and runner prompt missing (detail lists
  both, in order).
- Add FAIL tests for an empty gate log (no title line) and a gate log using a
  ~~~ fence for the THE SEED block (should still PASS).
- Add a FAIL test for a gate log whose THE SEED marker has no following fence.
- Add unit tests for _has_title_line (level-1 vs ## vs indented) and
  _has_seed_block (marker before fence, marker after fence, no marker).
