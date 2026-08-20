# TICKET-031 — Endpoint check not registered: run_all omits the endpoint check

## Title
The endpoint check is not registered in the check registry. `loop_doctor/checks.py`
must register the `endpoint` check at import time (after `run_health`) so that
`run_all` returns `[foundation, protocol, prompt, bash, run_health, endpoint]` in
stable order, and the module docstring must list `loop_doctor.endpoint` among the
imports.

## Evidence
- `loop_doctor/checks.py` currently registers `foundation`, `protocol`, `prompt`,
  `bash`, `run_health`. `run_all` returns `[foundation, protocol, prompt, bash,
  run_health]`.
- The module docstring lists `loop_doctor.project`, `loop_doctor.protocol`,
  `loop_doctor.prompt`, `loop_doctor.bash_check`, `loop_doctor.run_health`, and
  `loop_doctor.report` — not `loop_doctor.endpoint`.
- Cycle 7 briefing "What to Build" row `loop_doctor/checks.py`: "Register the
  endpoint check at import time (after run_health) so run_all returns
  [foundation, protocol, prompt, bash, run_health, endpoint] in stable order. Do
  not change the registry API. Update the module docstring to list
  loop_doctor.endpoint."

## Impact
- Even if `endpoint.py` exists, the aggregate go/no-go verdict and the CLI's
  full-run output would not include the endpoint check, so the fifth capability
  would not participate in the verdict.

## Suggestion
In `loop_doctor/checks.py`:
- Import `endpoint_check` from `loop_doctor.endpoint`.
- `register("endpoint", endpoint_check)` after the `run_health` registration.
- Update the module docstring to list `loop_doctor.endpoint` among the imports.
- Do not change the registry API (`register`, `run_all`, `run_one`,
  `registered_names`).
