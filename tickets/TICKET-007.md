# TICKET-007 — CLI does not compose the Report from the registry, and a non-existent project_dir is a no-go (exit 1) instead of a usage error (exit 2)

## Title
`loop_doctor/cli.py` `run_check` builds a single hardcoded `foundation` check
rather than composing the full `Report` from the check registry. A non-existent
`project_dir` is currently reported as NO-GO with exit code 1, but the Cycle 2
briefing requires it to be a usage error with exit code 2. There is also no
`--check NAME` flag to run or filter a single check.

## Evidence
- `loop_doctor/cli.py:28` `run_check(project_dir)` resolves the project and builds
  exactly one `Check("foundation", ...)`. It does not call a registry.
- `loop_doctor/cli.py:47` `main(argv)` calls `run_check(Path(args.project_dir))`
  unconditionally; there is no existence check on `project_dir` before running.
- Verified behavior: `main(["check", "/tmp/does-not-exist-xyz-123"])` prints
  "verdict: NO-GO / FAIL foundation — missing: gate log, runner prompt" and returns
  exit code 1. A missing directory is a caller mistake, not a project that failed a
  check, so it should be exit 2.
- `loop_doctor/cli.py:18` `build_parser()` defines only the positional
  `project_dir` and `--json`. There is no `--check NAME` option.
- Cycle 2 briefing "What to Build" row `loop_doctor/cli.py`: "run_check builds the
  full Report from the registry; a non-existent project_dir is a usage error
  (exit 2), not a no-go; add --check NAME to run/filter a single check; keep exit
  codes 0 go / 1 no-go / 2 usage error."

## Impact
- The exit-code contract is ambiguous: a typo'd or missing path is indistinguishable
  from a real no-go (both exit 1), so an operator cannot tell "I pointed at the wrong
  directory" from "this project is not ready".
- `run_check` cannot grow to compose multiple checks without a rewrite, because the
  check set is hardcoded to one.
- There is no way to run or inspect a single named check, which Cycles 3-8 will need
  for focused debugging.

## Suggestion
In `loop_doctor/cli.py`:
- `run_check(project_dir, check=None)` builds the `Report` from
  `loop_doctor.checks.run_all(project_dir)` (or a single named check when
  `check` is given), so the CLI composes the full report from the registry.
- In `main`, before running: if `Path(args.project_dir)` does not exist (or is not a
  directory), print a usage error to stderr and return 2. Do not run the checks.
- Add a `--check NAME` option to `build_parser`; when set, run/filter only that
  check (unknown name is a usage error, exit 2).
- Keep the exit-code contract: 0 = go, 1 = no-go, 2 = usage error (argparse errors
  and the non-existent-dir / unknown-check cases all map to 2).
Add deterministic, network-free tests: non-existent dir returns 2; `--check
foundation` runs only that check; an unknown `--check` name returns 2; a go report
returns 0 and a no-go report returns 1.
