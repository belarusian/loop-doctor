# TICKET-009 — No deterministic tests for registry composition, --check filter, non-existent dir, or summary counts

## Title
The Cycle 2 capabilities (check registry, `--check` filter, non-existent-dir
usage error, `Report.add`/`summary`) have no tests. The existing suite
(`tests/test_cli.py`, `tests/test_report.py`) only covers the single hardcoded
`foundation` check and the pre-existing renderers.

## Evidence
- `tests/test_cli.py` — 6 tests, all around the single `foundation` check and
  argparse exit codes. No test for a non-existent `project_dir` returning exit 2
  (currently it returns 1), no test for a `--check` flag (the flag does not exist),
  and no test that the report composes more than one check.
- `tests/test_report.py` — covers byte-stability, JSON round-trip, verdict/exit
  mapping. No test for `Report.add` or `Report.summary` (neither exists yet).
- `tests/test_project.py` — covers ai-dir resolution and 3-file location only.
- There is no `tests/test_checks.py` at all; the registry module does not exist.
- Cycle 2 briefing "What to Build" row `tests/`: "Deterministic, network-free
  tests: registry composes multiple checks into one verdict; --check filter;
  non-existent dir -> exit 2; summary counts; renderers still byte-stable."

## Impact
- The new behavior (exit 2 for a missing dir, `--check` filtering, multi-check
  composition, summary counts) would merge untested, so a regression in the
  exit-code contract or the registry ordering would not be caught.
- The byte-stability guarantee of the renderers is only asserted for the current
  single-check shape; a change that alters output for a multi-check report would
  slip through.

## Suggestion
Add deterministic, network-free tests (no network, no optional deps):
- `tests/test_checks.py`: `run_all` returns a list containing a "foundation"
  Check; registering a second check makes `run_all` return both in stable order;
  the composed `Report` carries a single aggregate verdict (go when no FAIL,
  no-go when any FAIL).
- `tests/test_cli.py`: non-existent `project_dir` returns exit 2; `--check
  foundation` runs only that check; an unknown `--check` name returns exit 2; go
  report returns 0 and no-go returns 1.
- `tests/test_report.py`: `add` grows the report and the verdict tracks it;
  `summary()` counts are correct and stable; `render_text`/`render_json` output
  is unchanged (byte-stable) for the existing sample report.
