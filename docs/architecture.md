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
| `loop_doctor/ci.py` | The ci check (green GitHub Actions CI on the main-branch head). |

## Check registry

A check is a callable `fn(project_dir: Path) -> Check`. Checks are registered by
name into a module-level `_REGISTRY` dict in `loop_doctor/checks.py`. `register(name, fn)` adds
or replaces a check; `run_all(project_dir)` runs every registered check in stable
insertion order and returns the list of `Check` results; `run_one(name, project_dir)` runs a
single named check (raising `KeyError` for an unknown name).

The seven checks are registered at import time in this stable order:
```python
register("foundation", _foundation)
register("protocol", protocol_check)
register("prompt", prompt_check)
register("bash", bash_check)
register("run_health", run_health_check)
register("endpoint", endpoint_check)
register("ci", ci_check)
```


## Capabilities

Each check is a small, dependency-light capability with a stable decision
order. The two optional capabilities (`prompt`, `run_health`) and the `ci`
capability degrade to `SKIP` (non-blocking) when their dependency or
environment is indeterminate, so the base install gates hermetically.

### 1. Protocol

- **Purpose** — the 3-file set is present and the gate log is well-formed.
- **Decision order** — resolve the project (reuses `resolve_project`); a
  missing gate log or runner prompt, an unreadable gate log, a missing
  level-1 title line, a missing `THE SEED` fenced block, or a missing seed
  ref is `FAIL` (detail names what is missing); otherwise `PASS`.
- **Seam** — none (pure file inspection, dependency-free).

### 2. Prompt

- **Purpose** — lint the runner prompt's spoke invocations against the
  argparse signatures of the referenced spoke scripts.
- **Decision order** — `spoke_lint` not installed is `SKIP`; otherwise run
  `spoke_lint` and consider invocation findings only (`missing_script`,
  `unknown_flag`, `missing_required`); any finding is `FAIL`, else `PASS`.
- **Seam** — the optional `spoke_lint` import is guarded with
  `try/except ImportError`.
- **SKIP-on-indeterminate** — `SKIP` when `spoke_lint` is absent.

### 3. Bash

- **Purpose** — `bash -n` syntax check on every `.sh` driver in the `proj` dir.
- **Decision order** — no `.sh` drivers is `PASS`; run `bash -n` on each
  (parse-only, never executed); any non-zero exit is `FAIL` naming the
  offending script(s) and the first `bash -n` stderr line; else `PASS`.
- **Seam** — none (shells out to `bash -n`, dependency-free).

### 4. Run health

- **Purpose** — inspect the run artifacts (`cycles.out` + trajectories) for
  a join gap fourseer cannot see.
- **Decision order** — `fourseer` not installed is `SKIP`; no `cycles.out`
  or no cycles is `SKIP`; a missing cycle number (contiguity gap) or an
  orphan trajectory path is `FAIL`; else `PASS`.
- **Seam** — the optional `fourseer` import is guarded with
  `try/except ImportError`.
- **SKIP-on-indeterminate** — `SKIP` when `fourseer` is absent or there are
  no run artifacts yet.

### 5. Endpoint

- **Purpose** — confirm the LLM backends the build loop depends on are
  reachable (`.157:8080` / `.161:8081`).
- **Decision order** — probe each endpoint with a plain TCP connect via
  `_probe`; any unreachable endpoint is `FAIL` naming each `host:port`; else
  `PASS`.
- **Seam** — `_probe(host, port, timeout)` is the single network seam; tests
  patch it (see `tests/conftest.py`) so the suite is network-free.
- **SKIP-on-indeterminate** — none: a network failure is a hard `FAIL`, not a
  `SKIP` (an unreachable backend genuinely blocks the loop).

### 6. CI

- **Purpose** — the project's main-branch head commit has green GitHub
  Actions CI.
- **Decision order** — not a git repo with an `origin` remote is `SKIP`;
  a non-GitHub remote is `SKIP`; `origin/main` cannot be resolved is `SKIP`;
  zero check runs is `SKIP`; any run not yet `completed` is `FAIL` (CI in
  progress); any run with a blocking conclusion (`failure`, `cancelled`,
  `timed_out`, `action_required`) is `FAIL` (CI red); otherwise `PASS` (CI
  green).
- **Seam** — every `git`/`gh` invocation is routed through the single
  module-level `_run(cmd)` helper, which normalizes a missing binary
  (`FileNotFoundError`) to a non-zero result (`returncode=127`); tests patch
  `loop_doctor.ci._run` so the suite is network-free.
- **SKIP-on-indeterminate** — `SKIP` when `gh` is missing, the directory is
  not a git repo with a GitHub `origin`, `origin/main` cannot be resolved,
  there are no check runs, or a `git`/`gh` subprocess or JSON parse fails.
  An indeterminate environment never hard-blocks the verdict.

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
