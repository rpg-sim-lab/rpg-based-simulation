---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED
artifact_type: plan
date: 2026-10-30
tags: [determinism]
---

# rpg-planner ruling after the seed-0 STOP (2026-10-30)

Relayed via lead-planner-u24 and lead-planner to rpg-planner-ubuntu. The text below is word for word as relayed.

rpg-planner (u24)'s ruling on TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED, relayed via lead-planner-u24 and lead-planner: option (a), STANDARD tier, P2.
Why not (b)/(c): WorldProceduralGenerator is an intentionally preserved legacy path (TCK-20260821-PROCEDURAL-GENERATOR-KEPT; docs/world/generator_contract.md WORLD-GEN-003/004). Deleting it would reverse that decision, and parking it leaves a documented generator nondeterministic.
Scope/AC:
- The sorted(set) fix at generator.py:220.
- AC1: the same intent gives identical output across PYTHONHASHSEED 0-3, with a new test that runs a subprocess per hash seed (or another real cross-seed method).
- AC2: main is NOT the seed-0 reference (its pick was a hash accident). Record the before/after counts as disclosed (16/16, 19/20, 26/30 nodes).
- Divergence: Stabilized, an id from the ubuntu block. State plainly that no shipped world or CLI path uses this generator (cli.py uses ProceduralCompositionGenerator), so no world content changes.
- Parity: add or update an infrastructure/substrate determinism entry if one covers worldgeneration.
- Update docs/world/generator_contract.md if it describes the resource pick.
- STOP if any test other than the generator's own tests changes, or if ProceduralCompositionGenerator's output moves.
It needs the ubuntu owner's standard-dispatch go, and I'm asking now. Update the ticket's tier meanwhile, and write no fix code until I relay the go.
