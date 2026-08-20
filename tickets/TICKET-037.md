# TICKET-037 — prompt / run_health FAIL tests are not robust to the optional deps being absent

## Title
The "prompt FAILs" and "run_health FAILs" composed tests in `tests/test_prompt.py`
and `tests/test_run_health.py` assume `spoke_lint` / `fourseer` are importable.
When the optional `full` extra is NOT installed, the prompt check SKIPs (instead
of FAILing) and the run_health check SKIPs, so these tests FAIL. The suite must
be green whether or not the `full` extra is installed.

## Evidence
- `tests/test_prompt.py::test_prompt_fails_on_unknown_flag`,
  `test_prompt_fails_on_missing_script` call `prompt_check` and assert
  `Status.FAIL`; with `spoke_lint` absent the check returns `Status.SKIP`.
- `tests/test_run_health.py::test_run_health_fails_on_missing_cycle_number`,
  `test_run_health_fails_on_missing_trajectory_path` call `run_health_check` and
  assert `Status.FAIL`; with `fourseer` absent the check returns `Status.SKIP`.
- Cycle 6 lesson 3: CI is RED because the workflow installs only the base
  package (no `full` extra), so `spoke_lint` is absent and the prompt FAIL test
  fails (prompt SKIPs instead of FAILs).
- Cycle 8 briefing "What to Build" row `tests/test_prompt.py +
  tests/test_run_health.py`: "Make the SKIP-vs-FAIL tests robust to the optional
  deps being ABSENT ... Guard them so they SKIP (pytest.skip) when the optional
  dep is not importable, so the suite is green whether or not the `full` extra
  is installed."

## Impact
- The suite is red in any environment without the `full` extra (including CI as
  currently configured), masking real regressions and blocking green CI.

## Suggestion
- Add a module-level guard (e.g. a helper that `importlib.util.find_spec`s the
  optional dep and `pytest.skip`s when it is absent) and apply it to the prompt
  FAIL tests (spoke_lint) and the run_health FAIL tests (fourseer).
- Keep the existing SKIP-when-uninstalled tests (they mock the import to None and
  must still pass regardless of the real install state).
