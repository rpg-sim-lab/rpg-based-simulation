---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE
phase: open
date: 2026-11-09
tags: [combat, determinism]
---

# TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE

## Title
A flight weighs the free swing it would take

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
A fighter in melee does not flee when the free swing it has felt would kill it (owner, #715 6735931881). Design: `.claude/handover/drafts/rpg-designer-flight-weighs-free-swing-design.md`. Dispatch: rpg-planner.

## Scope
1. Field and carrier: `CombatUpdate.hit_damage_set`, `CombatComponent.last_hit_damage`, digest scheme `flat-sha256-v4`, shared `is_evasive_flight`.
2. The guard `flight_weighs_free_swing` at every FLIGHT_REASONS emission site (later commits).
3. Docs: Bible 02 §7, CONFLICT-04 corollary, divergence 2.202, combat_movement parity entry.

## Out of Scope
KITING and KEEP_DISTANCE; non-flight moves off engagement (e24); the double resolve_attack per tick (filed P2); perf follow-ups (v1 base re-record under v4, ledger row, schema enum, hash_callsite_inventory wording).

## Acceptance Criteria
- Field commit: stripped-digest equivalence on crowded s42 (scheme label normalised and `last_hit_damage` dropped) equals base.
- The designer's 13 rows + 2 + coverage test pass; guard rows discriminate.

## Related Tickets
TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE; TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS

## Related Docs
docs/mechanics/02_combat_laws.md; docs/world_rules conflict-combat.md (CONFLICT-04); docs/engine/deterministic_execution.md

## Related Stored Artifacts
None yet.

## Related Code Areas
src/core/state.py; src/core/updates.py; src/engine/patches.py; src/engine/combat.py; src/engine/movement.py; src/engine/checkpoint.py; src/perf/benchmark_record.py

## Assumptions / Open Questions
No committed baseline or benchmark record carries the scheme in a machine-checked form; re-recording the v1 base under v4, the ledger row, the schema enum and the inventory wording are perf follow-ups queued for the perf seat.

## Implementation Notes
Digest bump to v4 ruled by rpg-planner. docs/engine edits limited to deterministic_execution :85/:102, known_limitations :120, substrate_baseline_contract :68.

## Test Summary
Pinned digests moved by exactly the new key: FIXTURE_DIGEST_V4 added (v3 form reproduced by dropping `last_hit_damage`). Timing NOT MEASURED.

## Files Changed
See commits.

## Completion Summary
Open.
