---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Rising in docs/engine/authoritative_pipeline.md: two B5 texts (rpg-designer-ubuntu, 2026-11-18, for rpg-designer's ruling at B5)
- **Basis:**
  - rpg-designer's condition on the rise placement (relayed by lead-planner): not pre-bind, and the pipeline doc must describe a phase that now creates bodies;
  - my placement ruling (B): a sub-step at the END of `resource_transactions`, after decay's post-transfer filter (economy.py:283).
- **Before text:** from impl 36ecbb3bf. The row-28 anchor occurs exactly once there.
- **Where it goes:** the Rising bullet sits directly after the Births Law bullet. That is the re-ruled Births Law text (reproduction design rev 2 §9), which B5 places in the "Ecological Dynamics" section.

## 1. Row 28 of the phase table
**Before:**
```
| 28 | `resource_transactions` | Enforces resource conservation and atomic transaction integrity. |
```
**After:**
```
| 28 | `resource_transactions` | Enforces resource conservation and atomic transaction integrity, and, after the decay filter, raises declared risen bodies from corpses (ECOL-07). |
```

## 2. New "Rising" bullet, inserted directly after the Births Law bullet
```
- **Rising Law** (ECOL-07; `src/engine/economy.py`, end of phase 28): Every `cadence.rises` ticks (30 by default, `src/engine/cadence.py`; absolute kernel tick), for each species declaring a risen profile, each corpse whose dead body's species is in the profile's `source_species`, and which neither decays this tick (`tick + 1 < decay_tick`) nor was taken or re-added by a transfer this tick (decay's post-transfer filter, so loot and meals win), may rise as one new body of the declaring species, by the profile's chance per check, drawn from the run's seeded RNG and keyed on the corpse. In one tick, births (phase 22) run before rising (phase 28), and risen ids come from the tick's merged update, so they never collide with that tick's newborns. The step commits only typed updates: the risen body with its RISEN source (source corpse and original entity), the corpse's removal, its gold as a purse, its raw meat out of the world through the decay sink, recorded as consumed by the rising, and its other items as ground items, through `corpse_remains`, the helper decay shares, called only after the post-transfer filter.
```
- Names aligned to the plan at impl 36ecbb3bf §11: the cadence is `cadence.rises`, mirroring `cadence.births`. The profile (`RisenProfileDefinition`, `SpeciesDefinition.risen_profile`, data/content/living/risen_profiles.yaml) has `source_species`, `rise_chance_per_check` and `risen_archetype`, and no cadence field. The rest of the names: SpawnKind RISEN, RISE_DRAW_SUB_ID, the helper `src/world/corpse_goods.py::corpse_remains` (called only after the post-transfer filter), and `src/world/risen.py` RisenService.
- **The 5 conditions rpg-designer checks at B5:**
  1. ids from `EntityGenerator.for_state(state, merged update)`;
  2. placement occupancy sees this tick's newborns;
  3. the phase-order line, which is this bullet plus ch05;
  4. the chance-0 twin is hash-equal to rise-off;
  5. the tick cost is measured under audit_mode.

## Ruling (rpg-designer, relayed by lead-planner, 2026-11-18)
- Row 28: APPROVED verbatim.
- Rising Law: APPROVED, with the meat clause amended as above, so its cause is named. The cadence.rises and corpse_remains delta was already with rpg-designer.
- **The meat record names its cause.** The implementer picks one form and says which:
  - (a) MEAT_DECAYED with a typed payload field `cause: "risen"`, where decay writes `"decay"`;
  - (b) a category of its own.
  - The conservation reader treats both as the same sink. R2 counts the meat against that record.
- rpg-designer checks the 5 B5 conditions against the code at B5.
