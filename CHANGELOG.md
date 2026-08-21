# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **CI check resolves the project's git repo via `proj/`** (TICKET-067) —
  `loop_doctor/ci.py` now resolves the git repo with
  `loop_doctor.project.resolve_proj_dir` (the `proj` dir, mirroring the bash
  check) and runs every `git`/`gh` command with `-C str(repo_dir)`. Previously
  it ran git in the raw project dir, so a fleet-style layout (a `proj/` git
  repo with an `origin` remote next to an `ai/` dir) was wrongly `SKIP`ped as
  "no origin" and the check never verified CI. The check now reaches the
  green/red decision on the real repo; a `proj/` that is not a git work tree,
  has no `origin`, or is a non-GitHub remote still `SKIP`s.
- **run_health unions cycle markers across all `cycles*.out` artifacts**
  (TICKET-068) — `loop_doctor/run_health.py` now computes contiguity over the
  union of the cycle markers in *every* `cycles*.out` file in the `ai` dir
  (glob `cycles*.out`, sorted, deduped by `cycle_no`), so a rotated / segmented
  history (e.g. `cycles.out` + `cycles-4.out`) no longer produces a false
  "missing cycle" gap. A cycle number genuinely absent from all artifacts is
  still reported honestly as `FAIL` (naming the number); no `cycles*.out`
  artifacts is still `SKIP`. The orphan-trajectory check is validated over the
  unioned cycles.

### Added


- **CI check** (check 7, registered last) — `loop_doctor/ci.py` verifies the
  project's main-branch head commit has green GitHub Actions CI via `git` +
  `gh`. It is the seventh registered check, so `loop-doctor check <dir>` runs
  seven checks and `--list-checks` lists `ci` last. An indeterminate
  environment (no `gh`, a non-git directory, a non-GitHub remote, no check
  runs, or a failed subprocess/JSON parse) is a non-blocking `SKIP`, mirroring
  the prompt check's optional-dependency convention.
- **Go/no-go + exit-code contract for the CI check** — the Cycle 8 suite in
  `tests/test_cli.py` now pins that `ci` FAIL flips the aggregate to NO-GO
  (exit 1) while `ci` PASS or `ci` SKIP leave the aggregate verdict unchanged
  (exit 0, verdict true) when the other checks pass/skip.
- **Docs** — `docs/architecture.md` gains a Capabilities section (the six
  capability checks, including the CI check) and the module map / registry
  reflect seven checks; `README.md`'s check list now lists all seven checks.

### Notes

- The CI check is dependency-free except for the `git` and `gh` binaries,
  which are invoked through a single module-level `_run` seam so the test
  suite stays deterministic and network-free.

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
