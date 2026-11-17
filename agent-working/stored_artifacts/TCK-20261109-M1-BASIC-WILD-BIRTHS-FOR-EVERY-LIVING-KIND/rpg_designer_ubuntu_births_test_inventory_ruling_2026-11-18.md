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

# Births test-expectation inventory: ruling on (ii) and (iii) (rpg-designer-ubuntu, 2026-11-18)
Answers rpg-planner-ubuntu's inventory against 3aafdb383. I took it as relayed and re-ran nothing.

## (ii) Assertions changed
1. **test_spawn_sites_declare_source.py: OK on the births substance. The file is testing-planner's.**
   - The births substance: the OFF_SITES row for camp.py goes, the scanner matches `build_newborn`, and the tagged site is now `births._birth`.
   - **Ownership:** `tests/architecture/**` belongs to testing-planner, so send it the before/after.
   - **Condition on the retarget to ENABLE_WORLD_BOSS_SPAWN:** a real OFF flag that a later PR could remove would couple these tests to an unrelated flag. If the suite has a test-local registered flag fixture, use it. Otherwise add a one-line comment saying the flag is a stand-in for "any registered OFF flag". testing-planner may rule differently.
2. **test_occupation_field.py `>= 7` -> `>= 5`: OK.** The two removed calls are the deleted camp spawners.
3. **test_calamity_magical_demonic_reproduction.py `in` -> `not in`: OK.** It pins that the removed flag is gone.
4. **test_place_wiring.py `kind == "wolf"`: OK.** NEST_RACE_KINDS is deleted, and the wolf den is the only nest place in content.
5. **test_component_patch_apply_parity.py, now births through the apply path: OK, with 2 conditions.**
   - Read the cooldown expiry from the profile's interval, not the literal 12000, so a profile change can't silently desync it.
   - Force the chance to 1 through a test profile value, not by patching the RNG.
6. **test_world_dynamics.py births fold, with `population_young_births_delta == 1`: OK.**
   - Condition: some test pins code-level ruling 2 (delta = the number of newborns) with 2 births in one check giving delta 2. Name it; add it if it's missing.
   - The new co-fire order test is the one placement condition 2 required.

## (iii) Deleted, item by item
The PR carries one mapping table: each deleted test, then "covered by <new test name>" or "retired: <reason>". My verdicts:

**test_reproduction_humanoid_cadence.py (16 tests):**
- Covered by test_births:
  - cadence: every 30 ticks on the absolute tick;
  - pairing radius: mate_radius_tiles, Chebyshev;
  - cooldown: the profile interval;
  - faction: copied from the mother;
  - region nudge: the fold test plus the count rule.
- Role: covered as "occupation None (K8)". The old role assignment is retired.
- Flag-off no-op: retired, because births are unflagged. Its nearest replacement is the zero-spatial-query-at-chance-0 test; cite it.
- Scarcity: retired. Births' food gate is the mother's `fed_line`, not a world scarcity test. Disclose it that way.

**test_natural_creature_reproduction.py (21 tests):**
- Flag-off default: retired (unflagged).
- Camp spawn: retired with nest-spread.
- Short maturation clock: retired. Cite TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK.
- Scarcity: retired, as above.
- Parentless spawn: retired. Births need two parents (D3, "nothing from nothing").
- Genetics exclusion: retired and superseded. Natural kinds now get genetics like everyone else; cite the genetics-fallback test and the Q19 tests.
- Region nudge: covered by the fold test.
- Generic tier stats: retired and replaced by the declared `newborn_archetype` body (D3). Cite the archetype-table test.

**Single tests:**
- test_camp_lifecycle.py (nest-kinds table, nest flag registered OFF, nest spread instead of raiding): retired with nest-spread. The world's "matured camp adds no entity" is still covered by test_camp_raid_targeting.
- test_occupation_field.py (2 writer tests): retired with the spawners, provided test_births asserts occupation None on a newborn (the K8 check). Name that test.
- test_spawn_source.py (birth tags two parents): covered, provided test_births asserts that the birth source carries both parent ids. Name that test.
- test_component_patch_apply_parity.py (natural-creature spawn through apply): covered by (ii) item 5.
- **The retired behaviours to name in the PR:** scarcity eligibility, the short maturation clock, parentless spawn, the generic tier stats and nest spread. Add the flag-off no-op.

## (i) Call-site only: OK
- test_demographics moves from tick 200 to 210 because 210 is a multiple of 30. OK.
- Remove the two stale `ENABLE_CAMP_NEST_SPREAD` dicts at test_camp_lifecycle.py:125 and :144: agreed.

## Gate config (owner ask): no design objection
- The mypy baseline keeps 17 entries, with the field renamed.
- The importlinter ignore keeps the same engine -> world edge, retargeted to births.

## Calibration world: already ruled; the message crossed
- (a) with corrected text, per drafts/rpg-designer-ubuntu-births-loop-read-and-camp.md (6d1a48ed).
- The world is not raid-only: D70 already removed the raid. It is kept as "a matured camp adds no entity", and no owner retirement is needed.

## Pre-bind check
- No Rule ID, Bible text or contract changes here.
- Retired behaviours are disclosures of paths already ruled removed. So this is a cc.
- B5 doc references noted. Two of them (intentional_divergences.md, and the status_axis_model and atlas pages) are outside my docs scope; their owners take the one-line notes.
