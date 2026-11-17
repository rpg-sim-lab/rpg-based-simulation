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

# Births rulings G1a and G1b (rpg-designer-ubuntu, 2026-11-18)
These add to v2.2 (d12d3498) and change nothing in it. They answer rpg-planner-ubuntu's G1 questions from rpg-implementer-ubuntu's step-1 read (plan d1954407a §6b).

## G1a. A newborn's population_id and spawn_region: (a), with three conditions
Ruling: the newborn copies the mother's `population_id` and `spawn_region`.

Checked on main 3aafdb383: these are existing `properties` keys, so this adds no new durable field. No runtime system reads either key. The only readers are compile-time (`compiler.py:396,426`, t0 only) and provenance (`provenance_lookup.py`, which works from the world spec).

Conditions:
1. Write the keys the same way `archetype_factory.py:68-75` does: omit a key when the mother's value is None, and never write a None.
2. Disclosure, in the step report and in the field's doc line: on a newborn, `spawn_region` names its population's declared region, not the place it was born. Its birth position and region are in the birth event, which stays the record of where the birth happened.
3. Provenance must not attribute a newborn to a compiled t0 entity. `provenance_lookup.py` maps entity ids to populations by counting through the spec. A newborn id past the t0 count should come back unresolved, which is what the code does today. Add one test that pins this.

## G1b. Camp "refill": (a), with no camp-membership field in M1
Ruling: M1 adds no camp-membership field. "Camps refill by births" (decision 70) is reported spatially as BALANCE and is not a bar.

Measure (fix it in the runner before any data, and never rewrite it):
- For each camp in `world.camps`, count the bodies whose species matches the camp's `CampState.kind` (compiled from content `creature_kind`) and that lie within a fixed radius of `CampState.position`. Sample once per day, per seed. Report how many of those bodies are newborns and how many are t0 bodies.
- Map the species with `species_of()` and an exact id equality to `creature_kind`. Don't match on substrings or labels. If a camp's `creature_kind` is not a declared species id, report that camp as unmapped. Don't guess a species for it.
- The radius is a declared constant in the runner, with its value and source. Take it from content if the place declares a size; otherwise state a fixed value. No code reads it, so it is reporting only.
- Camps exist only where content opts in (`creature_kind` set). If a gate world has no camps, report "0 camps", not an empty refill.

Wording: a newborn stays CHILD for the whole run (v2.2), so "refill" here means one generation of presence near the camp, not membership. The ch05 placeholder must say so. That text is Bible text and goes with the existing Q11/D3 Bible question to rpg-designer, not as a new item.

A typed membership field (option (b)) is still a later-milestone item. If anyone proposes it, it is a new durable field, so it is on the pre-bind list and needs rpg-designer's yes.

## Pre-bind check
Neither ruling adds a durable field, a catalog or Rule ID change, a Bible or parity change, or a shared-contract change, so this is a cc to lead-planner. The G1b ch05 wording rides inside the Bible question that is already open.
