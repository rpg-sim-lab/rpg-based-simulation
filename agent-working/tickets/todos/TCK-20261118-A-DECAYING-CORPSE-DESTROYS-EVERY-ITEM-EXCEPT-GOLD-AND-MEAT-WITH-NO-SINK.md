---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261118-A-DECAYING-CORPSE-DESTROYS-EVERY-ITEM-EXCEPT-GOLD-AND-MEAT-WITH-NO-SINK
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-A-DECAYING-CORPSE-DESTROYS-EVERY-ITEM-EXCEPT-GOLD-AND-MEAT-WITH-NO-SINK

## Title
When a corpse decays, its gold becomes a ground purse and its raw meat leaves through MEAT_DECAYED, but every other item it holds disappears with no typed sink, so atomic conservation cannot balance from the records

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-planner-ubuntu while designing the M1 births undead-from-corpse origin (relayed by lead-planner-u24, 2026-11-18). rpg-planner confirmed it by a code read on main 99a83adc9; it was not measured.
- `src/engine/world_dynamics.py::WorldDynamicsSystem._decay_corpses` (~:345-361): a corpse whose decay tick is reached goes into `corpses_remove`. Only `corpse.gold > 0` is carried out, as a `GroundItemState` purse (EXCH-02, ruling 61).
- `_meat_decayed_events` (~:40-49): raw meat left on the corpse leaves through the typed MEAT_DECAYED / `CORPSE_DECAY` sink (decision 44, ch. 03 "Sink").
- Nothing else in `corpse.items` (equipment, potions, materials, any non-meat item) gets a ground item, an event or a sink. It leaves the world when the body is removed.
- ch. 03 (Atomic Conservation) says every unit leaves through a typed, recorded sink. So this is a conservation-law gap, not a balance choice.
- The undead-from-corpse origin (owner Q-R5 "Corpse only now", #715) inherits the same body lifecycle. Under the final Q-R6 ruling (b), the births rising path drops every non-gold, non-meat item as a ground item through one shared helper, and its R2 row bars all three. This ticket brings decay onto the same helper.

## Scope
1. Evidence, with no behaviour change: on the 3 standard cells at 5000 ticks, count the non-meat item units on corpses at their decay tick, by item_id. Also check whether HardLawMonitor's conservation check covers corpse items at all, and why it doesn't fire.
2. LAW SET by rpg-designer (2026-11-18, the final Q-R6 ruling (b), relayed by lead-planner-u24). A decaying corpse's non-meat, non-gold items become ground items at its tile, carrying the source entity and the tick, like the ruling-61 purse. They go through ONE shared ground-item helper, the same one the births undead-rising path uses, so decay and rising follow one law. The typed CORPSE_DECAY sink per item is NOT the fix. Gold stays the purse and raw meat stays MEAT_DECAYED. Sequencing: the M1 births PR introduces the helper. Whichever of births and this ticket lands second reuses the other's helper. Still open: whether this is HARD for M1 (rpg-designer).
3. Fix, tests (a decayed corpse holding a non-meat item leaves a ground item at its tile with source entity and tick, and conservation balances), ch. 03 text, parity and divergence.

## Out of Scope
- TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME (a different decay-tick defect).
- The undead origin itself (M1 births PR, ubuntu lane), apart from sharing its ground-item helper.

## Acceptance Criteria
- No item leaves the world at corpse decay: every non-meat, non-gold item becomes a ground item at the corpse tile (source entity, tick) through the shared helper. A test pins it.
- The step 1 count is delivered before the fix.

## Related Tickets
- TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (the undead-from-corpse origin rides it)

## Related Docs
- docs/engine/known_limitations.md §1.2 (the limits line until this lands); docs/parity_ledger/town_resource.yaml TOWN-211 (divergent until this lands)
- docs/mechanics/03_economic_laws.md (Atomic Conservation; raw meat Source/Sink, CORPSE_DECAY)

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/world_dynamics.py (_decay_corpses, _meat_decayed_events), the conservation checks in src/observability/

## Assumptions / Open Questions
- How many non-meat items corpses actually hold at decay is unmeasured. A body that is looted first loses nothing.
- Whether this is a HARD error for M1 (owner #715 6936893143: deeper issues go to Phase 3 unless they are hard errors). rpg-designer rules.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
