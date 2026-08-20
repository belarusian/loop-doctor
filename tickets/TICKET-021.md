# TICKET-021 — Register the bash check in checks.py so run_all returns [foundation, protocol, prompt, bash]

## Title
The `bash` check is not registered in the check registry. `loop_doctor/checks.py`
registers `foundation`, `protocol`, and `prompt` at import time; `run_all` returns
`[foundation, protocol, prompt]`. The new `bash` check (TICKET-020) must be
registered at import time, immediately after `prompt`, so `run_all` returns
`[foundation, protocol, prompt, bash]` in stable order.

## Evidence
- `loop_doctor/checks.py` ends with three `register(...)` calls:
  `register("foundation", _foundation)`, `register("protocol", protocol_check)`,
  `register("prompt", prompt_check)`.
- `run_all(project_dir)` returns `[fn(project_dir) for fn in _REGISTRY.values()]`
  in insertion order, so the registration order is the stable order.
- The registry API (`register`, `registered_names`, `run_all`, `run_one`) must not
  change; only a new `register("bash", bash_check)` call is added.
- Cycle 5 briefing "What to Build" row `loop_doctor/checks.py`: "Register the
  `bash` check at import time (after `prompt`) so `run_all` returns
  `[foundation, protocol, prompt, bash]` in stable order. Do not change the
  registry API."

## Impact
- Without registration, `--check bash` would raise `KeyError` (mapped to a usage
  error) and the aggregate verdict would not reflect the bash check.

## Suggestion
- In `loop_doctor/checks.py`, import `bash_check` from `loop_doctor.bash_check`
  and add `register("bash", bash_check)` immediately after
  `register("prompt", prompt_check)`.
- Do not change the registry API or the order of the existing three registrations.
