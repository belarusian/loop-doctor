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

    loop-doctor check <project-dir> [--json]

Output is fully deterministic.

## Development

    pip install -e . pytest ruff mypy
    pytest tests/ -x -q
    ruff check loop_doctor/
    mypy loop_doctor/ --ignore-missing-imports

`spoke-lint` and `fourseer` are pinned git dependencies on the published repos
`belarusian/spoke-lint` and `belarusian/fourseer`. The four framework is a
read-only protocol seed, never copied into the repo.
