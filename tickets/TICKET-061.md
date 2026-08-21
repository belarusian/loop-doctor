# TICKET-061: CI CHECK tests (mocked, no network)

## Capability
Table-driven, mocked (patch.object on `loop_doctor.ci._run`), network-free tests
in tests/test_ci.py.

## Minimum coverage
- green -> PASS (and a composed Report verdict GO).
- red -> FAIL (and a composed Report verdict NO-GO).
- in-progress -> FAIL.
- zero check runs -> SKIP.
- not-a-repo -> SKIP.
- non-GitHub remote -> SKIP.
- gh failure -> SKIP.

Each case drives `_run` to return canned `subprocess.CompletedProcess` objects
for the git/gh commands in the order ci_check issues them. Full suite
(existing 178 + new) green at the gate.

## Acceptance
- All cases pass with no network / no real gh.
- patch.object on loop_doctor.ci._run (rule 4), not constructor patches.
