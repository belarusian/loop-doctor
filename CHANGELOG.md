# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-08-20

Initial release of loop-doctor, a pre-flight readiness auditor for the four
pipeline. Given a project dir (an `ai` dir next to a `proj` dir), it returns a
go or no-go report for launching build cycles.

### Added

- **Six checks** (registered in stable order):
  - `foundation` — the `ai` dir resolves and the 3-file set is located.
  - `protocol` — the 3-file set is present and well-formed (append-only gate
    log, runner prompt, seed reference).
  - `prompt` — spoke-lint (optional) lints the runner prompt against the spokes dir.
  - `bash` — `bash -n` syntax check on every `.sh` driver in the project root.
  - `run_health` — fourseer (optional) counts executed cycles and detects a
    `cycles.out` join gap.
  - `endpoint` — confirms the driver targets `.157:8080` and `.161:8081` and that no
    run is currently alive.
- **Go/no-go aggregate** — a single `Report.verdict` is `True` (go) iff no check
  `FAIL`s; `WARN` and `SKIP` are non-blocking.
- **Exit-code contract** — `0` = go, `1` = no-go, `2` = usage error.
- **CLI surface** — `loop-doctor check <project-dir> [--json] [--check NAME]`,
  `loop-doctor check --list-checks` (discovery), and `loop-doctor --version`.
- **Deterministic renderers** — byte-stable text and JSON output (no
  timestamps or hostnames, sorted keys, fixed status-count order).
- **Hardening** — full test coverage across all check modules, `docs/architecture.md`,
  `examples/` sample reports, and release metadata (`LICENSE`, `CHANGELOG.md`).

### Notes

- The base install is dependency-free: `spoke-lint` and `fourseer` are optional git
  extras (`pip install -e .[full]`) imported lazily by the `prompt` and `run_health` checks,
  which `SKIP` when the library is absent.
