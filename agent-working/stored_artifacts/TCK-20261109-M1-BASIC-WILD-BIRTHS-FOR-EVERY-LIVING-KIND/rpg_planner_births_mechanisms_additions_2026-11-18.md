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

# rpg-planner (u24): mechanisms.yaml for the four births additions, on plan 1d96b0ac2
Source: rpg-planner, relayed by lead-planner-u24, 2026-11-18. Transcribed by lead-planner (ubuntu) from the relayed message.
Ubuntu fills in each `verified` block from the births own-job evidence, using a runtime instrument. code_trace alone never supports a `done` claim.

## NEW ENTRIES (draft)
1) - id: pregnancy_gestation
     layer: entity
     summary: "A conceived child grows for a species-set gestation period before it is born; a death ends the pregnancy."
     systems: [world]
     depends_on: [humanoid_reproduction, aging_death]
     state: done
     implemented_by: [src/core/pregnancy.py::<the service or class>, src/core/state.py::PregnancyState]
2) - id: corpse_rising
     layer: entity
     summary: "Some dead bodies rise again as undead; the risen keep the dead body's goods rules (purse, meat, ground items)."
     systems: [world]
     depends_on: [corpse_goods_conservation]
     state: done
     implemented_by: [src/world/risen.py::<class>, src/entities/archetype_factory.py::ArchetypeEntityFactory::build_risen, src/core/spawn_source.py::SpawnSource]
3) - id: corpse_goods_conservation
     layer: world
     summary: "A dead body's goods are never lost: its coin becomes a purse, its meat leaves through decay, and every other item is left on the ground where it lies."
     systems: [economy]
     depends_on: [inventory_trade_conservation]
     state: partial
     implemented_by: [src/world/corpse_goods.py::corpse_remains]
   Note: "partial until TCK-20261118-A-DECAYING-CORPSE-DESTROYS-EVERY-ITEM-EXCEPT-GOLD-AND-MEAT-WITH-NO-SINK switches _decay_corpses to the helper. Today only the rising path uses it." That ticket's PR moves it to done.

## BINDINGS (change these from the file map)
- **Mate gate.** No row of its own. Bind src/world/mate_gate.py::<class> under humanoid_reproduction only.
  - The gate only READS bonds and marriages, so it is NOT bound to affection_relationship_bonds. Add affection_relationship_bonds to humanoid_reproduction's depends_on instead.
  - A reader isn't an implementer. The same rule kept MarriageState out of affection's binding.
- **humanoid_reproduction.** Also bind births.py (conception and birth) and archetype_factory::build_newborn.
  - Bind both method-level wherever the file holds other mechanisms.
  - The gated -> done change needs the owner-approved flag state and runtime evidence in the note.
- **aging_death.** No new binding: the death-site clear lives inside LifecycleSystem::resolve_lifecycle, which is already bound. Add one sentence to its note.
  - Don't bind state.py's pregnancy field to aging_death.
- **world_dynamics.py hook.** WorldDynamicsSystem is already class-bound (registry :2344).
  - Bind the NEW methods method-level, as WorldDynamicsSystem::<birth method> and ::<rise method>. Don't bind the class again.
- **No new bindings** for event_shapers PREGNANCY_ENDED, schema/repository/reference_graph/matrix or the content yaml, as long as those files are already bound.
- **cadence.py.** Bind it only if it survives, under corpse_rising.
- **Checks.** Run the mechanism completeness check (the one that gave 58/54/4/0) and state_caller on the births head, and send rpg-planner the output lines.
  - Completeness must show 0 unbound.
  - No file may drop its last binding. That is the camp/EntityGenerator class of miss.

## NOTE
- The rise now sits at the end of resource_transactions (economy.py), not in world_dynamics, so the world_dynamics rise-method binding may not apply.
- Bind the economy.py rise sub-step method-level under corpse_rising instead.

## FOLLOW-UP from rpg-planner (u24), 2026-11-18. This supersedes the world_dynamics rise binding above.
- **Binding:** corpse_rising binds to the economy.py rise method, method-level (economy.py carries other mechanisms), NOT to WorldDynamicsSystem. Drop the "world_dynamics hook: corpse_rising" binding. Keep only humanoid_reproduction's world_dynamics method, if births still hooks there.
- **Helper hazard** (now noted in rpg-planner's decay ticket):
  - `_decay_corpses` runs in world_dynamics BEFORE the transfers. Later, economy.py `_without_decay_of_looted_bodies` (~:282) drops the MEAT_DECAYED record for a body that a same-tick CORPSE loot takes or that a meal re-adds.
  - So corpse_remains() must NOT drop ground items at world_dynamics time. A body looted or re-added on its decay tick would DUPLICATE its goods.
  - The rise at the end of resource_transactions is the right place for the same reason. The later decay switch moves there too.
- **Tests for the births rise:**
  - a body looted on the rise tick doesn't rise with goods it no longer has;
  - a re-added body follows the applied outcome.
