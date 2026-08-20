# TICKET-038 — CI workflow does not install the `full` extra, so prompt/run_health FAIL tests never run for real

## Title
`.github/workflows/ci.yml` installs only the base package (`pip install -e .
pytest ruff mypy`) without the `full` extra, so `spoke_lint` and `fourseer` are
absent in CI. The prompt / run_health FAIL tests therefore SKIP (or, before the
test-side guard, FAIL) in CI and never exercise the real spoke_lint / fourseer
code paths.

## Evidence
- `.github/workflows/ci.yml` Install step: `pip install -e . pytest ruff mypy`
  (no `.[full]`).
- `pyproject.toml` defines `[project.optional-dependencies] full = [spoke-lint,
  fourseer]`.
- Cycle 6 lesson 3: CI is RED for this pre-existing reason.
- Cycle 8 briefing "What to Build" row `.github/workflows (or CI config)`: "If a
  CI workflow exists, install the `full` extra (`pip install -e .[full]`) so
  spoke_lint / fourseer are present and the prompt / run_health FAIL tests run
  for real in CI."

## Impact
- CI does not exercise the two optional-dep code paths (prompt lint via
  spoke_lint, run health via fourseer), so a regression in those paths would not
  be caught by CI.

## Suggestion
- Change the CI Install step to `pip install -e .[full] pytest ruff mypy` so the
  `full` extra (spoke_lint, fourseer) is present and the prompt / run_health FAIL
  tests run for real in CI.
