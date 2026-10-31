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
- The designer chooses between the two; a remove-only hotfix is acceptable if the designer prefers it.

## Out of Scope
Adding a home building kind (that is new content and its own owner question). F3 lodging and beds.

## Acceptance Criteria
- AC1: no building name in SERVICE_KINDS that content does not declare; a test fails if one appears.
- AC2: if the set moves to content, every current service mapping is preserved, and state hashes are identical on the 3-world s42 1000t check.
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

## Test Summary

## Files Changed

## Completion Summary
