# TICKET-019 — Tests: prompt PASS/FAIL/SKIP, run_all order, --check prompt, composed no-go

## Title
Deterministic, network-free tests are needed for the new `prompt` check and for the
registry/CLI behaviors it introduces. The existing GO fixtures in `test_checks.py` and
`test_cli.py` write a minimal runner prompt (`"prompt"`) that contains no spoke
invocations, so the prompt check PASSes on them (no invocation findings) and the GO
tests stay GO — but the `run_all` order assertions and the `--check` / composed-verdict
tests must be updated for the third check.

## Evidence
- `tests/test_checks.py` `test_run_all_returns_foundation_then_protocol_in_stable_order`
  asserts `names == ["foundation", "protocol"]`; once `prompt` is registered it must be
  `["foundation", "protocol", "prompt"]`.
- `tests/test_cli.py` `test_check_full_run_composes_both_checks` asserts
  `[c["name"] for c in data["checks"]] == ["foundation", "protocol"]`; it must become
  `["foundation", "protocol", "prompt"]`.
- The existing GO fixtures write the runner prompt as the literal `"prompt"` (no
  invocation lines), so the prompt check returns PASS (no invocation findings) and the
  GO tests remain GO.
- Cycle 4 briefing "What to Build" row `tests/`: "prompt PASSes on a well-formed prompt
  whose invocations match the spoke signatures; FAILs (with the right detail) on a prompt
  with an unknown flag or a missing script; SKIPs when `spoke_lint` is not importable
  (patch the import to simulate absence); FAILs when the runner prompt is missing;
  run_all returns [foundation, protocol, prompt] in that order; --check prompt runs only
  that check; the composed verdict is no-go when prompt FAILs."

## Impact
- The suite would go red the moment `prompt` is registered (the two order assertions),
  and the new check would be untested.

## Suggestion
- Add `tests/test_prompt.py`: PASS on a well-formed prompt whose invocations match the
  spoke signatures; FAIL (with the right detail) on a prompt with an unknown flag and on
  a prompt with a missing script; SKIP when `spoke_lint` is not importable (patch the
  import to simulate absence); FAIL when the runner prompt is missing.
- Update `tests/test_checks.py` and `tests/test_cli.py`: the `run_all` order assertion to
  `["foundation", "protocol", "prompt"]`; add `--check prompt` runs only that check; the
  composed verdict is NO-GO when `prompt` FAILs.
- Tests must be deterministic and network-free: build a small fake `spokes_dir` with a
  minimal argparse spoke script under `tmp_path`, and write the runner prompt text to
  `tmp_path` so `resolve_project` locates it.
