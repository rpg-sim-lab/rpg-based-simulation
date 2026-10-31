---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261101-SERVICE-KINDS-NAMES-A-BUILDING-KIND-NO-CONTENT-DECLARES
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-SERVICE-KINDS-NAMES-A-BUILDING-KIND-NO-CONTENT-DECLARES

## Title
The service table names a building kind ("home") that no content declares, and names building kinds in code at all

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Designer finding 2026-11-01, during the F3 review (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE). `src/engine/building_services.py:29` declares `SERVICE_KINDS = {"REST": frozenset({"inn", "home"}), "EAT": frozenset({"inn"}), "SELL": frozenset({"shop"}), "REPAIR": frozenset({"blacksmith"})}`. `data/content/world/buildings.yaml` declares no `home` kind, so `"home"` is a dead entry. The table is also a set of building names in code, which goes against D56's intent that behaviour reads declared kind properties rather than names (roadmap §12.2, decision 50).

## Scope
- Remove the dead `"home"` entry, or move the service sets to a declared content trait on the building kind (for example `services: [REST, EAT]`), with SERVICE_KINDS derived from content.
- RULED: content trait (see Implementation Notes).

## Out of Scope
Adding a home building kind (that is new content and its own owner question). F3 lodging and beds.

## Acceptance Criteria
- AC1: no building name in SERVICE_KINDS that content does not declare; a test fails if one appears.
- AC2 (designer correction 2026-11-01): every current service mapping is preserved; behaviour-identical on the 3-world s42 1000t check: at tick 0 the only state difference is `serves` on buildings, and every event stream and every other state field is byte-equal for the whole run.
- AC3: mechanisms.yaml town_services and the parity ledger are updated to match.

## Related Tickets
TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE; TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN.

## Related Docs
docs/plans/systemic_world/roadmap.md §12.2; docs/guidelines/intentional_divergences.md 2.119; registries/mechanisms.yaml town_services.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/building_services.py; data/content/world/buildings.yaml; the world assembly building profile.

## Assumptions / Open Questions
After F3 lands (F3 touches the same module). The designer decides remove-only or a content trait. Dispatch needs an owner go, or S4 if it is remove-only and filed as a hotfix.

## Implementation Notes
- 2026-11-01 SETTLED, shape (b). WORK's path, verified by the planner: `hires_for_pay` is a BuildingState field (src/core/state.py:1261) written into to_canonical_dict (state.py:1279), and building_services.py:38-39 reads the building state with no building name. So `serves` goes on BuildingState, copied at compile like beds and hires_for_pay. The designer corrects AC2 to: "behaviour-identical: at tick 0 the only state difference is `serves` on buildings; every event stream and every other state field is byte-equal for the whole run" (it replaces "hash-identical").
- 2026-11-01 DESIGNER RULING: use the CONTENT TRAIT. Each building kind declares `serves: [...]` in buildings.yaml (inn REST+EAT, shop SELL, blacksmith REPAIR); SERVICE_KINDS is derived from it; it follows WORK's path (ruling 66, D56). The dead "home" disappears because nothing declares it. It must be hash-identical.
- PLANNER NOTE, sent to the designer: "copied at compile like beds" and "hash-identical" conflict if `serves` enters BuildingState.to_canonical_dict, because beds moved the tick-0 hash. The implementer must state which holds: (a) `serves` is resolved into a content/registry lookup and not into the building's canonical dict, so hashes stay identical; or (b) it is on building state, and the hash moves (the AC then needs the designer's restatement). Settle this before the plan.

## Test Summary

## Files Changed

## Completion Summary
