# TICKET-053 — Add docs/architecture.md

## Title
Add `docs/architecture.md` documenting how loop-doctor is structured: the
check-registry pattern, the report model, the renderers, and the exit-code contract.

## Evidence
- No `docs/` directory exists.
- README.md documents usage (CLI flags, exit codes, JSON shape) but not structure.
- The module docstrings already describe each of these accurately.

## Impact
- A contributor landing on the repo must read all nine modules to understand the
  registry pattern, the report model, and the determinism invariants.

## Suggestion
- Create `docs/architecture.md` with sections: Overview, Check registry, Report
  model, Renderers, Exit-code contract, and Determinism invariants.
