# TICKET-043 — Add --list-checks CLI tests and a file-as-project-dir exit-2 edge test

## Title
`tests/test_cli.py` must add tests for `--list-checks` (it prints the six
registered names in stable order, returns 0, and works even when the project
dir does not exist / is not supplied) and an edge-case test that a
`project_dir` that is a FILE (not a dir) is a usage error (exit 2).

## Evidence
- `loop_doctor/cli.py::main` guards with `project_dir.is_dir()` (a file is not
  a dir), so a file already returns exit 2; the test pins that behavior.
- `loop_doctor/checks.py::registered_names()` yields the six names in stable
  order.
- Cycle 9 briefing "What to Build" row `tests/test_cli.py`.

## Impact
- The new discovery flag and the file-as-dir edge case would be untested.

## Suggestion
- Add tests: `--list-checks` prints the six names in order; returns 0; needs no
  project dir; runs no check (no `verdict` in output); works with a bogus dir.
- Add a test that a regular file passed as the project dir -> exit 2 with a
  usage-error message. Do NOT change the guard.
