---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED
phase: open
date: 2026-10-30
tags: [determinism]
---

# TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED

## Title
The intent-driven world generator picks each node's resource type with the RNG from a list built by list(set(...)), so the generated world depends on PYTHONHASHSEED. Sort the list.

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by the (B) audit of TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (item 5e, investigation at 16f7eb1f1). `src/worldgeneration/generator.py:220` builds `resource_types = list(set(r.resource_type ...))` and then calls `rng.choice(..., resource_types, ...)` per node. The RNG is seeded, but the list it indexes is in hash-seed order. So the same seed and catalog give different generated worlds across processes. This affects the intent-driven `WorldGenerator` path only, not the declarative worlds in `data/worlds`.

rpg-planner ruled on 2026-10-30 (ruling 3, Q2, in `TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`): this goes in a SEPARATE ticket, P2, in the ubuntu queue, not in B.

## Scope
1. First step: list every pinned generator output, meaning snapshots, golden worlds and content assertions that read `WorldGenerator` output, with file:line. Grep tests/ and tools/ for `WorldGenerator`, `generator.generate` and fixtures built from it.
2. Change the site to `sorted(set(...))` with a stable key (the resource type id string, or `.value` if it is an Enum).
3. If step 1 found pinned outputs: re-pin them, and tell rpg-planner-ubuntu, who tells the owner (ruling: "re-pins them with the owner's knowledge"). If none: say so.
4. Add a test: generate the same seed and intent in subprocesses at PYTHONHASHSEED 0 and 1, and assert identical resource types per node. Positive control: the comparison fails on main.

## Out of Scope
- data/worlds declarative assembly.
- Any other set-order site (those are TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED).

## Acceptance Criteria
1. The pinned-output inventory is in Implementation Notes, before any code change.
2. The generator site iterates a sorted, stable-key list.
3. The cross-seed test passes, and its positive control is shown.
4. Any re-pinned output is listed with the old and new value, and the owner's knowledge is recorded (comment id).
5. Scoped tests pass (`tests/` for worldgeneration, `-m "not slow"`), and generate_registry --check and paths-guard pass.

## Related Tickets
- TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (B; the audit that found it)
- TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED (A, #790)

## Related Docs
- docs/engine/kernel.md (determinism)
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md (ruling 3, Q2)

## Related Code Areas
- src/worldgeneration/generator.py

## Assumptions / Open Questions
- Hotfix tier, so dispatch is under S4 once rpg-planner OKs this plan. rpg-planner ruled the split and the first step; the plan OK for the fix itself is still to be confirmed.
- It queues behind the corpus hotfix and B on rpg-implementer-ubuntu.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
