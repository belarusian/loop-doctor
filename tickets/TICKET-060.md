# TICKET-060: registry + CLI surface for the ci check

## Capability
Register `ci` in the check registry so `loop-doctor check <dir>` runs seven
checks, `--check ci` selects it, `--list-checks` shows it, and the JSON report
gains a `ci` entry.

## Changes
- loop_doctor/checks.py: `from loop_doctor.ci import ci_check`;
  `register("ci", ci_check)` after `endpoint` so run_all returns seven checks in
  stable order [foundation, protocol, prompt, bash, run_health, endpoint, ci].
  Update the module docstring import list to include loop_doctor.ci.
- No change to cli.py (it reads the registry dynamically).

## Surface test updates (TICKET-060)
These tests enumerate the check surface and MUST be updated to include `ci`
(appended last, after endpoint):
- tests/test_checks.py `test_registering_second_check_makes_run_all_return_both_in_stable_order`:
  expected names list gains "ci" before "second".
- tests/test_checks.py `test_run_all_returns_foundation_then_protocol_in_stable_order`:
  expected names list gains "ci".
- tests/test_cli.py `test_check_full_run_composes_both_checks`: hardcoded names
  list gains "ci".
- tests/test_cli.py `SIX_CHECKS` -> rename to `SEVEN_CHECKS` and append "ci";
  update `test_exit_code_zero_when_all_pass_or_skip` and the
  `@pytest.mark.parametrize("check_name", ...)` in
  `test_exit_code_one_when_check_fails`. For the parametrized FAIL test, add a
  `_seam_ci` (patch.object on `loop_doctor.ci._run`) that makes ci FAIL and
  register it in `_SEAMS`. In the test environment tmp_path is not a git repo,
  so an un-patched ci_check SKIPs (non-blocking) — that keeps
  `test_exit_code_zero_when_all_pass_or_skip` green.

## Acceptance
- `--list-checks` prints seven names ending in "ci".
- `--check ci` selects the ci check.
- Full-run JSON report contains a "ci" entry.
