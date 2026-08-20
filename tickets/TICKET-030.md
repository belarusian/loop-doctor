# TICKET-030 — No endpoint check: the two LLM endpoints are never probed

## Title
There is no ENDPOINT CHECK. The Cycle 7 target `loop_doctor/endpoint.py` does not
exist. Nothing verifies that the project's two LLM endpoints are reachable. The
`foundation`, `protocol`, `prompt`, `bash`, and `run_health` checks confirm the
3-file set is located and well-formed, that the runner prompt's spoke invocations
are valid, that the root `.sh` drivers parse, and that the recorded run is
consistent; none of them checks that the LLM endpoints the pipeline depends on are
actually reachable.

## Evidence
- `ls loop_doctor/` — contains `__init__.py`, `bash_check.py`, `checks.py`,
  `cli.py`, `project.py`, `prompt.py`, `protocol.py`, `report.py`,
  `run_health.py`. No `endpoint.py`.
- `loop_doctor/checks.py` registers `foundation`, `protocol`, `prompt`, `bash`,
  `run_health`. `run_all` returns `[foundation, protocol, prompt, bash,
  run_health]`.
- The seed (`/home/sasha/Research/four/examples/spokes/durable-state-implementation.py`)
  names the two default LLM endpoints in its "URLs:" block: `.157:8080` (fast
  model, short context) and `.161:8081` (large model, long context), with defaults
  `FIVE_BASE_URL=http://192.168.1.157:8080/v1` and
  `FIVE_LARGE_URL=http://192.168.1.161:8081/v1`.
- Cycle 7 briefing "What to Build" row `loop_doctor/endpoint.py` (NEW): "a
  `endpoint_check(project_dir) -> Check` named `endpoint`. Probes the two default
  LLM endpoints (192.168.1.157:8080 fast, 192.168.1.161:8081 large) with a TCP
  connect (socket), NOT a live LLM run. PASS with '<n> endpoint(s) reachable' when
  all are reachable; FAIL with a detail naming the unreachable endpoint(s). The
  probe is a module-level function `_probe(host, port, timeout=2.0) -> bool` so
  tests can patch it. Stdlib only (socket)."

## Impact
- The fifth of the five real capabilities (Cycles 3-8) is absent. A project whose
  LLM endpoints are down would still be reported GO, masking an environment that
  cannot actually run the pipeline.

## Suggestion
Create `loop_doctor/endpoint.py` with:
- A module-level `_probe(host: str, port: int, timeout: float = 2.0) -> bool`
  that opens a `socket` and attempts `connect((host, port))`, returning `True` on
  success and `False` on any `OSError`/timeout. Stdlib only.
- `endpoint_check(project_dir: Path) -> Check` named `endpoint`. Probes the two
  default endpoints (192.168.1.157:8080, 192.168.1.161:8081). PASS with
  "<n> endpoint(s) reachable" when all are reachable; FAIL with a detail naming
  the unreachable endpoint(s) (e.g. "unreachable: 192.168.1.161:8081").
- Do NOT issue an LLM API call (no HTTP request to /v1); a TCP connect is a
  reachability probe and is allowed.
