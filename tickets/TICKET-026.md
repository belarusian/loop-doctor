# TICKET-026 — Register the run_health check in the registry after bash

## Title
The `run_health` check must be registered in `loop_doctor/checks.py` at import
time, immediately after `bash`, so `run_all` returns
`[foundation, protocol, prompt, bash, run_health]` in stable order. The registry
API must not change.

## Evidence
- `loop_doctor/checks.py` currently registers `foundation`, `protocol`, `prompt`,
  `bash` at import time (four `register(...)` calls at the bottom of the module).
  `run_all` returns `[foundation, protocol, prompt, bash]`.
- The module docstring says it "imports only from `loop_doctor.project`,
  `loop_doctor.protocol`, `loop_doctor.prompt`, `loop_doctor.bash_check`, and
  `loop_doctor.report` (no spoke-lint / fourseer)". Adding `run_health` means
  importing `loop_doctor.run_health` (which itself guards the optional `fourseer`
  import, so the registry stays dependency-free at import time).
- Cycle 6 briefing "What to Build" row `loop_doctor/checks.py`: "Register the
  `run_health` check at import time (after `bash`) so `run_all` returns
  `[foundation, protocol, prompt, bash, run_health]` in stable order. Do not
  change the registry API."

## Impact
- Without registration, `run_all` never runs the run health check, `--check
  run_health` is an unknown check (exit 2), and the aggregate verdict does not
  reflect the fourth capability.

## Suggestion
- In `loop_doctor/checks.py`, import `run_health_check` from
  `loop_doctor.run_health` and add `register("run_health", run_health_check)`
  immediately after `register("bash", bash_check)`.
- Update the module docstring to list `loop_doctor.run_health` among the imports.
- Do not change `register`, `registered_names`, `run_all`, or `run_one`.
