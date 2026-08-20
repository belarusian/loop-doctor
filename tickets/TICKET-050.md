# TICKET-050 — Add a `--version` flag to the loop-doctor CLI

## Title
Add a `--version` flag to the `loop-doctor` CLI that prints the package
version and exits 0, sourced from the single `__version__` constant so it
cannot drift from `pyproject.toml`.

## Evidence
- `loop_doctor/__init__.py` defines `__version__ = "0.0.1"`.
- `pyproject.toml` independently declares `version = "0.0.1"`.
- `loop_doctor/cli.py` (`build_parser`) registers only the `check` subcommand and its
  `--json` / `--check` / `--list-checks` flags. There is no `--version` action on the
  top-level parser or the `check` subparser.
- `grep -rn "version" loop_doctor/cli.py` returns nothing; the version constant is never read by the CLI.
- `grep -rn "version" tests/` returns nothing; no test pins a `--version` behavior.

## Impact
- A user or CI job cannot confirm which loop-doctor build is installed without inspecting
  the source tree. `loop-doctor --version` currently falls through to an argparse usage
  error (exit 2).

## Suggestion
- In `build_parser` (loop_doctor/cli.py), add
  `parser.add_argument("--version", action="version", version=f"loop-doctor {__version__}")` on the
  top-level parser, importing `__version__` from `loop_doctor`.
- Add tests in `tests/test_cli.py`: `main(["--version"])` returns 0 and stdout contains
  `loop-doctor 0.0.1`; `--version` works with no project dir; `main([])` still returns 2.
