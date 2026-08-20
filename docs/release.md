# Release

This page is the single reference for how loop-doctor is built, packaged, and
released.

## Build

loop-doctor is a standard setuptools package. Build a wheel or sdist with:

    python -m build

Or install in editable mode for development:

    pip install -e .

The build backend is `setuptools.build_meta` (see `[build-system]` in
`pyproject.toml`).

## Dependency boundary

The base install is **dependency-free**: `dependencies = []` in
`pyproject.toml`. Two optional capabilities are provided as the `full` extra and
are imported lazily by their checks, which `SKIP` when the library is absent:

    pip install -e .[full]

- `spoke-lint` — used by the `prompt` check.
- `fourseer` — used by the `run_health` check.

## Entry point

The console script is declared in `[project.scripts]`:

    loop-doctor = "loop_doctor.cli:main"

Running `loop-doctor` invokes `loop_doctor.cli:main`.

## Version

The version is a single source of truth. It is declared once in the `[project]`
table of `pyproject.toml` and mirrored in `loop_doctor.__version__`. The two
must agree (enforced by `tests/test_version.py`), and the CLI surfaces it via
`loop-doctor --version`. The version follows `MAJOR.MINOR.PATCH`.

## License

loop-doctor is released under the MIT License (see `LICENSE`).

## URLs

| Name | URL |
|---|---|
| Homepage | https://github.com/belarusian/loop-doctor |
| Repository | https://github.com/belarusian/loop-doctor |
| Documentation | https://github.com/belarusian/loop-doctor/blob/main/docs/architecture.md |
| Issues | https://github.com/belarusian/loop-doctor/issues |
