# TICKET-063: go/no-go + exit contract for check 7 (ci)

## Capability
Verify and pin by test that the ci check (check 7) participates in the
go/no-go verdict and the exit-code contract:
- ci FAIL => verdict NO-GO, exit 1.
- ci PASS or ci SKIP => no change to the aggregate verdict from the other
  checks (exit 0 when the rest pass/skip).

Extend the Cycle 8 exit-code contract suite in `tests/test_cli.py` rather than
duplicating it. The `_seam_ci` seam (Cycle 13) already drives
`loop_doctor.ci._run` to a red check run; the parametrized
`test_exit_code_one_when_check_fails` already covers ci FAIL => exit 1.

## Acceptance
- A focused test forces ci to SKIP via the seam and asserts the aggregate
  verdict is unchanged (exit 0, verdict true) with the rest passing/skipping.
- A focused test forces ci to PASS via the seam and asserts exit 0, verdict
  true.
- ci FAIL => exit 1 / NO-GO remains pinned (existing parametrized case + a
  dedicated assertion).
- All in the existing suite; no network.
