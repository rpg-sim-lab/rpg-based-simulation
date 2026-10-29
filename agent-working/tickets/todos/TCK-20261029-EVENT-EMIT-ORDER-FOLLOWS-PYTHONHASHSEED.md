---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED
phase: open
date: 2026-10-29
tags: [determinism, observability]
---

# TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED

## Title
Within one tick, the emit order of progression and equipment events follows the process hash seed. Sort at the emit loops.

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
codebase-implementer found this during codebase M7 batch 2 characterization, and codebase-planner checked it against the source. rpg-planner-ubuntu re-verified it on main 33da13604 and widened it.

Several emit loops iterate a Python `set` of strings or of `EquipSlot` enums. An Enum hashes by its name string. String hashes are randomized per process by `PYTHONHASHSEED`. So when one entity gets two or more IDs of the same kind in one tick, the order of those events differs between processes on the same world and seed.

Harness and gate runs pin `PYTHONHASHSEED=0`, and are reproducible:
- `tools/rpg_measure/paired.py:102`
- `tools/test_architecture/rpg_gate_harness.py:158`
- `tools/perf/rerun_baselines.py:403`

Unpinned CLI and server runs are not reproducible.

rpg-planner ruled on 2026-10-29 that the work splits in two. The ruling is in `agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`. This ticket is (A), the event side only. The state side is TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (B).

## Scope
Sort at emission, with a stable key: the enum `.value` or the string ID itself, never `str(obj)`. These are the sites on 33da13604:
1. `src/observability/event_extractor.py:351`. It iterates `set(eq_slots) | set(prior_eq_slots)` and emits `item_equipped`/`item_unequipped`. Use `sorted(..., key=lambda s: s.value)`. The block is not flag-gated.
2. `src/observability/event_extractor.py:379`. It iterates `set(eq_dur) | set(prior_eq_dur)` and emits `equipment_durability_changed`. Use the same key. Verify that the durability keys are `EquipSlot`; `src/core/equipment.py:260` uses `durability.get(slot, ...)`. If any key is a plain string, use a key that handles both and say so.
3. `src/observability/event_extractor.py:1163` (`skill_unlocked`), `:1173` (`trait_expressed`) and `:1183` (`pillar_trait_unlocked`). These are set differences on the rollback path (`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` OFF). Use `sorted(...)` with an explicit stable key for the element type: the id, or `.value` for an Enum. Don't rely on the natural ordering of mixed or Enum types. The test asserts the element type (rpg-planner ruling 2).
4. `src/observability/event_shapers.py`, `ProgressionShaper` (around line 1031-1050), on the default path. It iterates `id_upd.learned_skills`, `traits_add` and `breakthroughs_add` in list order. Use `sorted(...)`.
   - Those lists come from `list(set(...))` in `src/core/updates.py:276-281` and `src/engine/evolution.py:120`, so their order follows the hash seed.
   - Sorting here makes emission independent of the producers' order.
5. Sweep `src/observability/event_extractor.py` and `src/observability/event_shapers.py` for any other emit loop over a `set`/`frozenset`, or over a list built from one. List each one in the ticket.
   - Fix it here only if it is emission-only.
   - Report anything that reaches state, rather than fixing it.
   - Dict iteration is insertion-ordered and out of scope.

`src/engine/evolution.py:120` is **not edited** in this ticket. Its list goes into `IdentityUpdate.learned_skills`. The apply path folds that list into a set (`src/engine/patches.py:230`, `sk |= set(u_id.learned_skills)`), and state holds `learned_skills: Set[str]` (`src/core/state.py:646`). So its order reaches nothing but emission, and step 4 covers that. rpg-planner accepted this reasoning (ruling 2). Record it in Implementation Notes.

## Out of Scope
- Any state-side ordering: `IdentityUpdate.merge` in `src/core/updates.py`, `src/domains/combat_engagement/learning.py:45`, and set iteration in decision code. All of that is ticket (B).
- Event shape or payload changes.
- Pinning `PYTHONHASHSEED` in non-harness entry points.
- codebase M7's split of `event_extractor.py`. M7 holds its golden fixtures until this ticket lands. Coordinate the merge order through rpg-planner-ubuntu.

## Acceptance Criteria
1. Each site in Scope 1-4 iterates in a sorted, stable-key order. Any extra Scope 5 site is listed with its disposition.
2. Unit tests that are deterministic in-process:
   - With PHASE2 ON, one entity whose update carries `learned_skills`, `traits_add` and `breakthroughs_add` with 3 or more IDs each, in non-sorted list order, emits them in sorted order.
   - The same holds on the rollback path, with PHASE2 OFF and prior/current state sets.
   - Two or more equipment slots changing in one tick emit in `EquipSlot.value` order, for both the equip and the durability loops.
3. A cross-process test runs a fixed short run twice in subprocesses, at `PYTHONHASHSEED=0` and at one other value, and asserts that the event streams are identical.
   - It needs a positive control: show that the same comparison fails on main before the fix, or uses a fixture where two or more IDs land in one tick.
   - If no world and tick count makes two or more land in a short run, drive it from a constructed state, and say so.
4. The final STATE hash at `PYTHONHASHSEED=0` is unchanged against main on one short run (world, seed and ticks recorded). Only event order moves. If the hash changes, STOP and report to rpg-planner.
6. The Completion Summary carries the step-5 sweep report: what was fixed and what was only reported. Reported items are appended to (B)'s audit list.
5. Scoped tests pass:
   - `tests/unit/observability/`
   - the extractor and shaper tests
   - `pytest -m "not slow"` on the touched areas.
   Also run `generate_registry --check` and paths-guard before the push ask.

## Related Tickets
- TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (B, state side)
- TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION (introduced ProgressionShaper)
- TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP (introduced the equipment loops)
- codebase M7 batch 2 (event_extractor split; waits on this ticket for its goldens)

## Related Docs
- `docs/engine/kernel.md` (determinism)
- `docs/guidelines/intentional_divergences.md`: no entry expected, since event order is not a Bible law. If rpg-planner says otherwise, use the ubuntu id block 2.144-2.149.

## Related Stored Artifacts
- `agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/observability/event_shapers.py`
- tests under `tests/unit/observability/`

## Assumptions / Open Questions
- Assumed: no consumer depends on the current within-tick order of these events. SimQ scorers count by type. Check by grepping the readers of the event streams in `src/` and `frontend/`.
- rpg-planner OK'd the plan on 2026-10-29 (ruling 2, recorded in the ruling file). Dispatch is under S4 (#715 6473439661), after #784's main merge.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
