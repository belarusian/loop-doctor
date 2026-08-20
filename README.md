# loop-doctor

A pre-flight readiness auditor for the four pipeline. Given a project dir
(an `ai` dir next to a `proj` dir), it returns a go or no-go report for
launching build cycles.

## Checks

- **Protocol check** — the 3-file set is present and well-formed: an
  append-only markdown gate log, a runner prompt, and a seed reference.
- **Prompt lint** — invokes spoke-lint (imported as a library) on the runner
  prompt against the spokes dir, surfacing flag mismatches.
- **Bash check** — runs `bash -n` on every `.sh` driver in the project root.
- **Run health** — uses fourseer (imported as a library) to count executed
  cycles and detect a `cycles.out` that fourseer cannot see (the join gap).
- **Endpoint check** — confirms the driver targets the intended LLM endpoints
  `.157:8080` and `.161:8081`, and that no run is currently alive.

## Usage

    loop-doctor check <project-dir> [--json] [--check NAME]
    loop-doctor check --list-checks

- `--json` — emit the report as JSON instead of text.
- `--check NAME` — run only the named check (e.g. `foundation`) instead of
  every registered check.
- `--list-checks` — print the registered check names (one per line, in stable
  registration order) and exit 0. This is a discovery flag: it does not require
  a project dir and does not run any check.

Output is fully deterministic.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | go — no check FAILed (or `--list-checks` succeeded) |
| 1 | no-go — at least one check FAILed |
| 2 | usage error — non-existent project dir, a file passed as the project dir, an unknown `--check` name, or `check` with neither a project dir nor `--list-checks` |

### JSON output shape

With `--json`, the report is a JSON object with three top-level keys:

- `verdict` (bool) — `true` for go, `false` for no-go.
- `summary` (string) — the stable status-count line, identical to
  `Report.summary()`, e.g. `"pass=3 fail=1 warn=1 skip=1"`.
- `checks` (list) — one object per check, in stable registration order, each
  with `name`, `status` (`pass`/`fail`/`warn`/`skip`), and `detail`.

Keys are sorted and the output is indented with 2 spaces, so it is byte-stable
for a given report.

## Development

    pip install -e . pytest ruff mypy
    pytest tests/ -x -q
    ruff check loop_doctor/
    mypy loop_doctor/ --ignore-missing-imports

The base install is dependency-free: the Foundation (CLI, dir resolution,
report model) imports nothing external, so it builds and tests hermetically.
`spoke-lint` and `fourseer` are optional git extras on the published repos
`belarusian/spoke-lint` and `belarusian/fourseer`, installed with
`pip install -e .[full]` and imported lazily by the capabilities that need
them (prompt lint, run health). The four framework is a read-only protocol
seed, never copied into the repo.
