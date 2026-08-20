# TICKET-040 — Add a --list-checks discovery flag to the check subcommand

## Title
`loop_doctor/cli.py` must gain a `--list-checks` flag on the `check`
subcommand. When set, it prints the registered check names (one per line, in
stable registration order) to stdout and returns 0 WITHOUT running any check
and WITHOUT requiring the project dir to exist. This closes the CLI passthrough
gap: today there is no way to discover the registered checks.

## Evidence
- `loop_doctor/cli.py::build_parser` defines the `check` subcommand with a
  required positional `project_dir` and `--json` / `--check NAME`; there is no
  discovery flag.
- `loop_doctor/checks.py::registered_names()` returns the six names in stable
  registration order `[foundation, protocol, prompt, bash, run_health,
  endpoint]`.
- Cycle 9 briefing "What to Build" row `loop_doctor/cli.py`: "Add a
  --list-checks flag ... print the registered check names (one per line, in
  stable registration order) to stdout and return 0 WITHOUT running any check
  and WITHOUT requiring the project dir to exist."

## Impact
- Without it, a caller cannot enumerate the available checks; the only way to
  learn them is to read the source.

## Suggestion
- Make `project_dir` optional (`nargs="?"`, default `None`) so `check
  --list-checks` parses with no dir.
- In `main`, handle `--list-checks` BEFORE the `project_dir.is_dir()` guard:
  print `checks_mod.registered_names()` one per line and return 0.
- A bare `check` (no dir, no `--list-checks`) is a usage error -> 2.
