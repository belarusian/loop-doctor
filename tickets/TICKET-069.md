# TICKET-069 — protocol: THE SEED block is optional (seedless projects must PASS)

## Context / evidence
- 2026-08-25 preflight of ~/AI/sentry (cycle 6 launch gate):
  `python3 -m loop_doctor.cli check ~/AI/sentry/proj` → verdict NO-GO, sole FAIL:
  `FAIL protocol — malformed gate log: no THE SEED block`
  Every other check PASSED: foundation, prompt, bash, run_health (5 cycles
  consistent), endpoint (2 reachable), ci (green at 39ede6d).
- sentry was intentionally set up seedless: its gate log header (level-1 title,
  Repository, Started, Total cycles) has no `THE SEED` fenced block. Seedless
  setups are legal — mission-compiler's `--seed` is optional. A hard requirement
  NO-GO's every seedless project regardless of the rest of the report.

## Defect
`loop_doctor/protocol.py`, `protocol_check`:

    if not _has_seed_block(lines):
        return Check("protocol", Status.FAIL, "malformed gate log: no THE SEED block")

treats an ABSENT seed spec as malformed. It is not: absence is a valid dialect
(seedless project), per the scar rule "parsers grow with the log".

## Desired behavior
- The level-1 `# ...` title line is ALWAYS required (unchanged).
- Gate log HAS a `THE SEED` fenced block → the seed ref must still resolve; an
  empty/unresolvable seed ref still FAILs ("missing: seed ref") — unchanged.
- Gate log has NO `THE SEED` block at all → the seed requirement is SKIPPED and
  the check PASSes (given a valid title line).

## Concrete change (loop_doctor/protocol.py, protocol_check)
Replace the two seed-related FAIL branches with a single conditional that only
FAILs when the block is present but its ref is unresolvable, i.e. of the shape:

    if _has_seed_block(lines) and <parsed>.seed_ref is None:
        return Check("protocol", Status.FAIL, "malformed gate log: missing: seed ref")

(drop the `no THE SEED block` branch entirely; match the actual parsed-log
variable name in the file; keep the title-line check as-is.)

## Regression fixtures (scar rule: one fixture per dialect you meet)
In the protocol test module / existing fixture layout:
1. seedless gate log (valid title line, no THE SEED block, otherwise valid
   dialect) → protocol PASS.
2. gate log with an empty/unresolvable THE SEED block → protocol FAIL
   ("missing: seed ref") — keep/extend existing coverage.
3. gate log with no title line → still FAIL (unchanged).

## Acceptance
1. `python3 -m pytest tests/ -x -q` green;
   `python3 -m ruff check loop_doctor/` clean;
   `python3 -m mypy loop_doctor/ --ignore-missing-imports` clean.
2. Real validation (record in the log Results table):
   `cd ~/AI/loop-doctor/proj && python3 -m loop_doctor.cli check ~/AI/sentry/proj`
   → protocol no longer reports "no THE SEED block"; record the full report
   as-is (other checks' verdicts unchanged).
3. Squash, PR, merge to main, close issues with citation, append the cycle block.
