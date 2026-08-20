# Architecture

loop-doctor is a pre-flight readiness auditor. Given a project dir (an `ai` dir
next to a `proj` dir), it resolves the project, runs a registry of checks, and
renders a deterministic go/no-go report. The whole pipeline is dependency-free
at the core; two optional capabilities degrade to `SKIP` when their libraries are
absent.

## Module map

| Module | Role |
|---|---|
| `loop_doctor/cli.py` | Argument parsing, the `check` subcommand, `--version`, `--list-checks`, exit codes. |
| `loop_doctor/checks.py` | The check registry: `register` / `run_all` / `run_one` and the six registered checks. |
| `loop_doctor/report.py` | The `Check` / `Report` / `Status` model and the byte-stable text/JSON renderers. |
| `loop_doctor/project.py` | Project-dir / `ai`-dir resolution and the 3-file set. |
| `loop_doctor/protocol.py` | The protocol check (3-file set well-formedness). |
| `loop_doctor/prompt.py` | The prompt check (spoke-lint, optional). |
| `loop_doctor/bash_check.py` | The bash check (`bash -n` on root `.sh` drivers). |
| `loop_doctor/run_health.py` | The run-health check (fourseer, optional). |
| `loop_doctor/endpoint.py` | The endpoint check (`.157:8080` / `.161:8081`). |

## Check registry

A check is a callable `fn(project_dir: Path) -> Check`. Checks are registered by
name into a module-level `_REGISTRY` dict in `loop_doctor/checks.py`. `register(name, fn)` adds
or replaces a check; `run_all(project_dir)` runs every registered check in stable
insertion order and returns the list of `Check` results; `run_one(name, project_dir)` runs a
single named check (raising `KeyError` for an unknown name).

The six checks are registered at import time in this stable order:
```python
register("foundation", _foundation)
register("protocol", protocol_check)
register("prompt", prompt_check)
register("bash", bash_check)
register("run_health", run_health_check)
register("endpoint", endpoint_check)
```


## Report model

```python
class Status(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"
```

A `Check` is a frozen dataclass `(name, status, detail)`. A `Report` is an ordered list of
checks with a derived `verdict` property: `verdict` is `True` (go) if and only if no
check has status `FAIL`. `WARN` and `SKIP` are non-blocking — they surface information but
never flip the verdict.

## Renderers

Both renderers are byte-stable for a given report: no timestamps, no
hostnames, and no reliance on dict/set iteration order.

- `render_text(report)` — a `verdict: GO|NO-GO` line, then one `STATUS name — detail` line
  per check in insertion order.
- `render_json(report)` — a JSON object with `verdict` (bool), `summary` (the stable
  status-count line, e.g. `"pass=5 fail=0 warn=0 skip=1"`), and `checks` (a list of `{name, status, detail}`).
  Emitted with `sort_keys=True` and `indent=2`.

## Exit-code contract

| Code | Meaning |
|---|---|
| `0` | go — no check `FAIL`ed (or `--list-checks` / `--version` succeeded) |
| `1` | no-go — at least one check `FAIL`ed |
| `2` | usage error — non-existent project dir, a file passed as the project dir, an unknown `--check` name, or `check` with neither a project dir nor `--list-checks` |

## Determinism invariants

- No timestamps or hostnames in any output.
- JSON keys are sorted; the status-count line uses a fixed order
  (`pass, fail, warn, skip`).
- Checks render in stable registration order.
- The `prompt` and `run_health` checks `SKIP` (non-blocking) when `spoke-lint` / `fourseer` are
  not installed, so the base install gates hermetically.
