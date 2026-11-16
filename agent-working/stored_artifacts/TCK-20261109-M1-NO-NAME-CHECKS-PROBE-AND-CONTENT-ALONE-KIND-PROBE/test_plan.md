---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE: test_plan

- Synthetic package (`tmp_path/src/<pkg>/`): each shape found (24 cases, incl. getattr, a bound local, role_id/faction_id/species/archetype); data-by-id, other records' kinds, numbers, assignments, another record's bound local, a local leaking across functions, a reassigned local not found (15 cases); excluded package not scanned; report-only reported but not gating; every `src/domains/*` gating.
- Rulings: runtime excluded, content_semantics gates, a promoted row gates inside a report-only package and a stale promotion fails, a reasoned exclusion is reported and not gating and a stale or reasonless one fails.
- Ratchet: new switch fails; listed switch passes; second switch under a row fails; stale row fails; over-counted row fails; package in no list / two lists / gone fails.
- Output: text and JSON rows carry file, line, symbol, name; counts line.
- Real tree: green with the committed allowlist; every row has a one-line reason and the retire ticket; no duplicate key.
- Perturbation (nothing committed; first version of the scan): changed `EntityRole.HERO` to `EntityRole.GUARD` at `src/engine/occupancy_snapshot.py:33` and added a `Faction.NEUTRAL` compare to `src/ai/coming_of_age.py`; the real-tree test failed on both with the new-switch message; src restored.

## Proof Plan
- level: architecture (static AST scan of src/, plus a synthetic package)
- proof kind: ratchet: a committed allowlist of the current switches; a new switch, a stale row or a changed count fails
- oracle source: the planner and rpg-planner rulings in the ticket (switch definition, package lists), not the code
- expected effect: adding a role, kind or faction name switch to a gating package turns the test red; removing one without lowering its row turns it red
- selected commands: pytest tests/architecture/test_no_name_switches_in_decision_paths.py
