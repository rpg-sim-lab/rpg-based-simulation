---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS

All tests are in `tests/codebase/`, using tmp registries (the `seeded` fixture pattern) and hand-built `Finding`s. Nothing touches the repo baseline or runs a real scan.

## Unit tests (`ratchet.likely_moves`)
- One gone row plus one new finding, same `(symbol, tool, rule)`, different file, value ≤ ceiling → one pair, not ambiguous.
- Value over the ceiling → no pair.
- Symbol `None`, `<module>`, or tool jscpd → no pair.
- Same file → no pair (that's a rename or line move, already key-stable).
- Two new findings for one gone row, and two gone rows for one finding → all candidates, each `ambiguous=True`.
- Output order is deterministic.
- `compare` results are unchanged with or without pairing: `blocking_failed` is still True (regression guard, option A was not chosen).

## Unit tests (`registry.move_rows`)
- Moves exactly the matched rows. The moved row is equal to the original except `file`.
- Unmatched rows of the old file stay put.
- Each refusal raises and leaves the input rows unchanged:
  - over-ceiling value;
  - target key exists;
  - `--symbol` not movable;
  - nothing to move.

## CLI tests (`python3 -m codebase.health` via `main(argv)`)
- `check` on the moved fixture exits 1 and prints the "likely move" line with the exact command.
- `move a.py b.py --from DIR` exits 0, and `check` exits 0 afterwards.
- A refusal exits 2 and leaves the registry file byte-identical.
- `--summary-out` contains the pair.

## Regression
- Run `tests/codebase/` in full, especially `test_code_health_ratchet_registry.py` and `test_code_health_ci_summary.py`.
- Run `make code-health` on the real tree. It must still give the same verdict, with no likely-move lines on main.
