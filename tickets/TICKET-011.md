# TICKET-011 — The protocol check is not registered, so run_all does not return [foundation, protocol]

## Title
Even once `protocol.py` exists, the `protocol` check is not registered in
`loop_doctor/checks.py`. `run_all` must return `[foundation, protocol]` in
that stable order, but it currently returns only `foundation`.

## Evidence
- `loop_doctor/checks.py` ends with a single import-time registration:
  `register("foundation", _foundation)`. There is no `register("protocol", ...)`.
- `run_all(project_dir)` iterates `_REGISTRY.values()` in insertion order, so
  the order is exactly the registration order. Registering `protocol` after
  `foundation` yields `[foundation, protocol]`.
- Cycle 3 briefing "What to Build" row `loop_doctor/checks.py`: "Register the
  `protocol` check at import time (after `foundation`) so `run_all` returns
  `[foundation, protocol]` in stable order. Do not change the registry API."

## Impact
- The aggregate verdict would not reflect the protocol check, and `--check protocol`
  would be an unknown-check usage error (exit 2) because `registered_names()` would
  not contain `protocol`.
- The stable-order contract (`run_all` returns checks in registration order) is the
  extension point Cycles 4-8 rely on; the protocol check must occupy the slot right
  after `foundation`.

## Suggestion
In `loop_doctor/checks.py`:
- Import `protocol_check` from `loop_doctor.protocol`.
- Add `register("protocol", protocol_check)` at import time, immediately after the
  existing `register("foundation", _foundation)` line.
- Do not change the registry API (`register`, `run_all`, `run_one`,
  `registered_names`).
Add a deterministic, network-free test: `run_all` returns `[foundation,
protocol]` in that exact order on a well-formed project.
