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

# Births: exact before/after texts for the ENABLE_CAMP_NEST_SPREAD leftovers (rpg-designer-ubuntu, 2026-11-18)
- **Basis:** the ruling in drafts/rpg-designer-ubuntu-births-loop-read-and-camp.md (6d1a48ed). These are the texts it describes.
- **Before text:** taken from births head 1f2cd368b. Each anchor occurs once in its file.
- **Revision 2:** this applies rpg-planner (u24)'s two wording fixes, relayed by lead-planner, and the display rename.
- **Revision 3:** the seeded maturity is 79.9, not 79.5 (module :52, :57; the 79.5 on main was already stale). This revision also adds §4, the module-file riders.
- **The id is unchanged.** The id `camp_maturity_calibration_pilot` and its directory are read by 3 tests, so they stay. Only the display name changes.

## 0. data/worlds/camp_maturity_calibration_pilot/world.yaml, line 3: display name (owner: rpg-planner on u24)
**Before:** `name: "Camp/Nest Maturity Calibration Pilot"`
**After:** `name: "Camp Maturity Calibration Pilot"`
- Checked by rpg-planner-ubuntu (tests/), by lead-planner (the rest of main) and by me at 1f2cd368b. Nothing reads the name except the regenerated `resolved/world.resolved.yaml`.

## 1. data/worlds/camp_maturity_calibration_pilot/world.yaml, line 4 (owner: rpg-planner on u24, via lead-planner)
**Before:**
```
description: "Unit-tier isolation world proving CampService.process_camps()'s raid and Nest-spread branches (RAID_MATURITY_THRESHOLD=80.0) fire in a real, practical-length run -- TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE's own real user decision (dedicated calibration world with seeded near-threshold maturity, not a production balance-constant change). Composes frontier_village_core + camp_maturity_calibration_pilot, the latter seeding a CAMP (goblin) and a NEST (wolf) both at maturity=79.5 so the real ~160,000-tick production accrual gate is bypassed via content alone, leaving only the real, practical last_raid_tick>=500 gate. With ENABLE_CAMP_NEST_SPREAD=ON (via this world's own calibration profile), the goblin camp (not in CampService.NEST_RACE_KINDS) takes the raid branch and the wolf nest (in NEST_RACE_KINDS) takes the Nest-spread branch in the same run -- both real branches proven in one calibration."
```
**After:**
```
description: "Unit-tier isolation world proving that a matured camp adds no entity in a real, practical-length run. Composes frontier_village_core + camp_maturity_calibration_pilot, the latter seeding a CAMP (goblin) and a NEST (wolf) both at maturity=79.9, so they pass the old 80.0 threshold within a few ticks without the ~160,000-tick production accrual. Built for TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE to prove the raid and Nest-spread branches; the raid spawn was removed by D70 (divergence 2.125, TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70), and the maturity gate with its Nest-spread branch by TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND, so both camps now only mature and spawn nothing. Read by tests/integration/world/test_camp_raid_targeting.py, tests/unit/world/test_world_rules_are_deterministic.py and tests/simulation_quality/fixtures/expected_world_flag_state.json."
```
- After this edit, regenerate `resolved/world.resolved.yaml` and the other `resolved/` reports with the world's compile tool. Never hand-edit them.

## 2. config/simulation_quality/profiles/camp_maturity_calibration_pilot.yaml, line 2 (births PR)
- Delete the line that sets `ENABLE_CAMP_NEST_SPREAD` to `"ON"`.
- If that leaves the profile's flags map empty, keep the file only if a loader requires it. Otherwise follow the profile pattern of the other corpus worlds.
- If `tests/simulation_quality/fixtures/expected_world_flag_state.json` moves, it comes to me.

## 3. data/content/world_modules/wolf_den_near_forest.yaml, lines 49-54 (births PR)
**Before:**
```
    # TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE: NEST-kind Place, position is the
    # centroid of grid_bounds. creature_kind=wolf is in CampService.NEST_RACE_KINDS,
    # so with ENABLE_CAMP_NEST_SPREAD=ON this camp's own raid branch is replaced by
    # the Nest-spread offspring branch instead — matches this module's own
    # wild_beast_pack/wolf_pack_small theming exactly. maturity left unset, same
    # caution as every other Stage B Place in this corpus (no calibrated value yet).
```
**After:**
```
    # TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE: NEST-kind Place, position is the
    # centroid of grid_bounds. A camp adds no entity (raid spawn removed by D70; maturity gate and
    # Nest-spread removed by TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND);
    # wolves now come from births. maturity left unset, same caution as every other Stage B
    # Place in this corpus (no calibrated value yet).
```
- A content-module comment doesn't change the compiled world. If any world's resolved hash moves anyway, stop and report it.

## 4. data/content/world_modules/camp_maturity_calibration_pilot.yaml (unowned riders, births PR)
### 4a. Insert after line 1 (`# STATE: ADDITIONAL`)
```
# Since TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND: the raid spawn (removed by D70,
# divergence 2.125), the maturity gate and Nest-spread are all gone, and CampService.process_camps()
# only grows maturity. This module now seeds near-threshold maturity so a test can show that a
# matured camp adds no entity. The header below is kept as history.
```
### 4b. Line 17, the stale seed value inside the historical header
**Before:** `# change needed -- this module seeds it at 79.5, just under the real threshold, so`
**After:** `# change needed -- this module seeds it at 79.9, just under the real threshold, so`
### 4c. Line 26, `description:`
**Before:**
```
description: "Unit-tier isolation module seeding near-threshold camp/nest maturity to prove CampService's raid and Nest-spread branches fire in a practical-length run."
```
**After:**
```
description: "Unit-tier isolation module seeding near-threshold camp/nest maturity (79.9) so a practical-length run shows a matured camp adds no entity (raid spawn removed by D70, divergence 2.125; gate and Nest-spread removed by TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND)."
```
- `display_name` at line 25 is already "Camp Maturity Calibration Pilot", so it is unchanged. World.yaml line 3 now matches it.
- Content comments and descriptions shouldn't move the compiled world beyond the regenerated `resolved/` texts. If any state hash moves, stop and report it.

## Code note for rpg-planner-ubuntu (not a text)
- At 1f2cd368b `CampService.RAID_MATURITY_THRESHOLD = 80.0` (src/world/camp.py:17) has no reader in src; `process_camps` now only matures.
- Remove it in the births PR or name it as kept for the M3 raid design. It's the same pattern as `RaidService`'s kept constants in 2.125.
