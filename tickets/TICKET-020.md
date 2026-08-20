# TICKET-020 — No bash check: root .sh driver scripts are not syntax-checked

## Title
There is no BASH CHECK. The Cycle 5 target `loop_doctor/bash_check.py` does not
exist. Nothing syntax-checks the project's root `.sh` driver scripts. The
`foundation`, `protocol`, and `prompt` checks only confirm the 3-file set is
located and well-formed and that the runner prompt's spoke invocations are
valid; they never parse the shell driver scripts that actually launch the build
cycles.

## Evidence
- `ls loop_doctor/` — contains `__init__.py`, `checks.py`, `cli.py`, `project.py`,
  `protocol.py`, `prompt.py`, `report.py`. No `bash_check.py`.
- `loop_doctor/checks.py` registers `foundation`, `protocol`, `prompt`. `run_all`
  returns `[foundation, protocol, prompt]`.
- `loop_doctor/project.py` now provides `resolve_proj_dir(project_dir) -> Path`
  (added this cycle, mirroring `resolve_ai_dir`): accepts either the `proj` dir
  itself or its parent and returns the `proj` dir. This is the anchor the bash
  check uses to find the root `.sh` drivers.
- The seed (`/home/sasha/Research/four`) ships root driver scripts (`transform.sh`,
  `pipelines/v2/run-cycles.sh`) and its CHANGELOG verifies them with
  `bash -n <script>` (syntax check only, no execution).
- Cycle 5 briefing "What to Build" row `loop_doctor/bash_check.py` (NEW): "a
  `bash_check(project_dir) -> Check` named `bash`. Find the root `.sh` driver
  scripts in the project dir (the `proj` dir itself, not the `ai` dir) — i.e.
  `*.sh` files directly in `project_dir` (resolve the proj dir from `project_dir`,
  accepting either the proj dir or its parent). Run `bash -n <script>` (syntax
  check only, no execution) on each, in sorted order for determinism. PASS when
  every driver parses cleanly; when there are no `.sh` drivers, PASS with a detail
  like 'no .sh drivers'. FAIL with a detail naming the offending script(s) and the
  `bash -n` stderr (e.g. 'syntax error: <name>: <first stderr line>'). Use
  `subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)`;
  treat a non-zero returncode as a syntax failure. Keep the check dependency-free
  (stdlib only)."

## Impact
- The third of the five real capabilities (Cycles 3-8) is absent. A root `.sh`
  driver with a syntax error (an unclosed `if`, a stray `then`) would still be
  reported GO, masking a driver that would fail at launch time.

## Suggestion
Create `loop_doctor/bash_check.py` with:
- `bash_check(project_dir: Path) -> Check` named `bash`.
- Resolve the `proj` dir via `loop_doctor.project.resolve_proj_dir` (do NOT
  re-implement resolution).
- Find `*.sh` files directly in the `proj` dir (not recursive, not the `ai` dir),
  sorted for determinism.
- When there are none, return `Check("bash", Status.PASS, "no .sh drivers")`.
- For each script, run `subprocess.run(["bash", "-n", str(script)],
  capture_output=True, text=True)`; a non-zero `returncode` is a syntax failure.
- PASS when every driver parses cleanly; FAIL with a detail naming the offending
  script(s) and the first `bash -n` stderr line (e.g. "syntax error: <name>:
  <first stderr line>").
- Keep the check dependency-free (stdlib only: `pathlib`, `subprocess`).
