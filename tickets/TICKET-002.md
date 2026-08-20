# TICKET-002 — `loop_doctor/project.py` (dir resolution + 3-file set) is missing

## Title
There is no module to resolve the `ai` dir next to a `proj` dir, nor to locate the
3-file set (gate log, runner prompt, seed reference). The Foundation target
`loop_doctor/project.py` from the Cycle 1 briefing does not exist.

## Evidence
- `ls loop_doctor/` — only `__init__.py`; no `project.py`.
- Cycle 1 briefing "What to Build" lists `loop_doctor/project.py`: "Resolve the ai
  dir next to a proj dir; locate the 3-file set (gate log, runner prompt, seed
  reference)".
- The 3-file protocol is defined in the seed `~/Research/four/README.md`
  ("The 3-file protocol (per project — data handed in, never hardcoded)"):
  - **runner prompt** — the INNER spoke's path (strict shape, e.g. 6-phase).
  - **briefing** — tells the OUTER the log location + the goal for the inner.
  - **log** — the GROUND TRUTH that joins them; append-only, single writer,
    position IS a total order, no date, no index.
- Real example of the 3-file set on disk:
  - gate log: `/home/sasha/AI/loop-doctor/ai/cycle-001-loop-doctor-gate.md`
  - runner prompt: `/home/sasha/AI/loop-doctor/ai/loop-doctor-cycle-runner-prompt.md`
  - seed reference: the log's "THE SEED" block names `/home/sasha/Research/four`.
- Layout convention (seed README "Where things live"): `~/AI/<project>/proj`
  (checkout) + `~/AI/<project>/ai` (log, runner prompt, briefings, trajectories).
  The `ai` dir is a SIBLING of `proj`, one level up.

## Impact
- The CLI (TICKET-001) has nothing to call to find the files it must audit.
- Without a canonical resolver, the protocol check (Cycle 3-4) cannot flag a
  missing or mis-named gate log, and the seed reference cannot be read.
- Ambiguity about "project-dir" (does the user pass `proj/` or the parent
  `~/AI/<project>/`?) is unresolved and will be re-derived inconsistently.

## Suggestion
Create `loop_doctor/project.py` exposing:
- `resolve_ai_dir(project_dir: Path) -> Path` — accept either the `proj` dir or its
  parent; return the sibling `ai` dir. Document which form is canonical.
- `locate_three_files(ai_dir: Path) -> ThreeFiles` — return a dataclass with
  `gate_log: Path | None`, `runner_prompt: Path | None`, `seed_ref: Path | None`.
  - gate log: the `cycle-*-*-gate.md` markdown file(s); flag if none or mis-named.
  - runner prompt: the `*-runner-prompt.md` file.
  - seed reference: parse the "THE SEED" fenced block in the gate log to get the
    read-only seed path (do not hardcode it).
- A `ThreeFiles` dataclass (frozen) so the report model can consume it.
Add unit tests using `tmp_path` fixtures covering: ai-dir sibling resolution,
all-present, gate-log-missing, seed-block-missing.
