# TICKET-018 — Register the prompt check in the registry after protocol

## Title
The `prompt` check must be registered in `loop_doctor/checks.py` at import time,
immediately after `protocol`, so `run_all` returns `[foundation, protocol, prompt]` in
stable order. The registry API must not change.

## Evidence
- `loop_doctor/checks.py` currently ends with `register("foundation", _foundation)` and
  `register("protocol", protocol_check)`.
- `run_all` iterates `_REGISTRY.values()` in insertion order, so registration order is
  the stable order.
- `loop_doctor/cli.py` `run_check` composes the full `Report` from `run_all` (or a
  single named check via `--check NAME`); no API change is needed for `--check prompt`
  to work once the check is registered.
- Cycle 4 briefing: "Register the `prompt` check at import time (after `protocol`) so
  `run_all` returns `[foundation, protocol, prompt]` in stable order. Do not change the
  registry API."

## Impact
- Until registered, `--check prompt` is a usage error (exit 2) and the aggregate verdict
  never reflects the prompt check.

## Suggestion
- Add `from loop_doctor.prompt import prompt_check` and
  `register("prompt", prompt_check)` at the end of `loop_doctor/checks.py`, after the
  `protocol` registration.
- Verify `loop_doctor/cli.py` needs no change: `--check prompt` runs only that check and
  the aggregate verdict reflects all three checks; the exit-code contract (0 go / 1
  no-go / 2 usage error) is preserved.
