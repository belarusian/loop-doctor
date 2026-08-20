# TICKET-004 — Test suite does not cover the Foundation contract; smoke test masks the break

## Title
`tests/` contains only a package-import smoke test. The Cycle 1 briefing requires
"Unit tests for CLI arg parsing, dir resolution, and report rendering
(deterministic, no network)", none of which exist. As a result CI is green while
the CLI is unimportable (see TICKET-001).

## Evidence
- `tests/test_smoke.py` — single test: `import loop_doctor; assert
  loop_doctor.__name__ == "loop_doctor"`. It never touches `cli`, `project`, or
  `report`.
- `tests/__init__.py` — empty.
- Cycle 1 briefing "What to Build" row `tests/`: "Unit tests for CLI arg parsing,
  dir resolution, and report rendering (deterministic, no network)".
- `.github/workflows/ci.yml` — runs `pytest tests/ -x -q`; with only the smoke
  test, the suite passes even though `loop_doctor.cli` does not exist.

## Impact
- The gate (pytest + ruff + mypy) cannot detect that the tool is non-functional.
- There is no regression protection for the deterministic exit-code contract
  (0/1/2), dir-resolution edge cases, or renderer stability.
- Future cycles build on an untested Foundation; defects surface late.

## Suggestion
Add deterministic, network-free unit tests (using `tmp_path`):
- `tests/test_cli.py` — `main(["check", <tmp>])` returns an int exit code; bad
  args return 2; `--json` output parses via `json.loads`.
- `tests/test_project.py` — ai-dir sibling resolution; 3-file set present /
  gate-log-missing / seed-block-missing.
- `tests/test_report.py` — renderer byte-stability (render twice, compare), JSON
  round-trip, verdict→exit-code mapping.
Keep the existing smoke test. All tests must pass with no network and no external
tools (no `bash`, no `gh`, no git deps).
