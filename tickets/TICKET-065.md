# TICKET-065: cycle 14 gate

## Capability
Cycle 14 delivers TICKET-063..064: the go/no-go + exit-contract pinning for
check 7, plus docs/CHANGELOG and real validation. Gate green, squash, PR,
merge, close issues.

## Gate (rule 3)
- `/usr/bin/python3 -m pytest tests/ -x -q`
- `/usr/bin/python3 -m ruff check loop_doctor/`
- `/usr/bin/python3 -m mypy loop_doctor/ --ignore-missing-imports`

## Acceptance
- All three gate commands pass.
- Branch build14/ci-contract-docs squashed and merged on main.
- Cycle 14 block appended to the cycle log.
