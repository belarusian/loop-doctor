# TICKET-001 — CLI entrypoint `loop_doctor/cli.py` is declared but does not exist

## Title
`pyproject.toml` declares the console script `loop-doctor = "loop_doctor.cli:main"`,
but `loop_doctor/cli.py` is not present. The installed `loop-doctor` command cannot
be imported.

## Evidence
- `pyproject.toml:17` — `loop-doctor = "loop_doctor.cli:main"` (declared entrypoint).
- `ls loop_doctor/` — contains only `__init__.py` (219 bytes). No `cli.py`.
- `README.md:21` — documents `loop-doctor check <project-dir> [--json]` as the usage.
- `loop_doctor/__init__.py` — package docstring describes the tool, but exports nothing
  and defines no `main`.
- `tests/test_smoke.py` — only asserts `import loop_doctor` succeeds; it does not
  exercise the CLI, so CI is green while the command is broken.

## Impact
- `pip install -e .` succeeds, but running `loop-doctor` (or `loop-doctor check ...`)
  fails at import time with `ModuleNotFoundError: No module named 'loop_doctor.cli'`.
- The entire tool is unusable end-to-end. Every downstream capability (protocol,
  prompt-lint, bash, run-health, endpoint) is unreachable because there is no entry
  to invoke them.
- CI stays green (smoke test only imports the package), masking the break.

## Suggestion
Create `loop_doctor/cli.py` with a `main(argv: list[str] | None = None) -> int` that:
- Uses `argparse` with a single subcommand `check` taking a positional `project-dir`
  and a `--json` flag (store_true).
- Returns deterministic exit codes: `0` = go, `1` = no-go, `2` = usage error
  (argparse already returns 2 on bad args; keep that contract explicit).
- Delegates dir resolution to `loop_doctor/project.py` and rendering to
  `loop_doctor/report.py` (do not inline their logic here).
- Prints the report to stdout (text by default, JSON with `--json`).
- Guard with `if __name__ == "__main__": raise SystemExit(main())`.
Add a unit test that invokes `main(["check", <tmpdir>])` and asserts the exit code
and that `--json` output parses as JSON.
