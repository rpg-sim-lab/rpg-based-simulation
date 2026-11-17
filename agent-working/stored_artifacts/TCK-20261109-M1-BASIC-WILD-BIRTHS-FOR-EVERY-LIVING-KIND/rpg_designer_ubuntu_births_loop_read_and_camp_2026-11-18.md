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

# Births: the loop_detected read for u24, and the ENABLE_CAMP_NEST_SPREAD leftovers (rpg-designer-ubuntu, 2026-11-18)
- **Data:** rpg-planner-ubuntu's relay from the kept head runs at 1f2cd368b, which is pre-reorder. The reorder leaves births identical: 1fa557abf has an equivalence test, and spatial hits are metrics only. I re-ran nothing.

## What a loop flag can and cannot show
- `loop_flags` are tag names. A tag is flagged when it holds more than 70% of a pillar's last-N score window (`pillar_accumulator._check_loop_detection`).
- That measures one tag dominating, not one entity stuck.
- On head it is True on almost every pillar in all three worlds, always with an `*_active` or pillar-typical tag, and the same flag is on main where main was given (hero COGNITION `subjective_divergence`).
- So a flag alone neither shows nor excludes a never-exit loop.
- My read therefore uses the per-entity emission spans of the event type that carries each move. A never-exit loop means one entity emitting the same state-driven event from some tick to the end of the run.

## Row 1: hero_guild_routing COGNITION 2.8169: NO never-exit loop
- The only moving type is `decision_divergence_detected`.
- On head its emitters are:
  - entity 3: 140 events, ticks 138-277, held and then exited;
  - entity 5: 60 events, ticks 296-355, held and then exited;
  - no other emitter, and nothing after tick 355.
- Both entities are alive at 1000, so they stopped meeting the condition; they didn't die in it.
- The never-exit loop is on main (entity 25, ticks 276-975, to the end), and head removes it.
- The `subjective_divergence` flag is on both arms. On head it reflects that divergence events dominate a short stream, not a stuck entity.
- **Stated for u24:** no never-exit loop on head stands behind 2.8169.
- A per-tick project-state run is not needed for this read: the scored events are the evidence.

## Row 2: urban_political SOCIAL: NOT YET READ
- The move is the denominator. Head's SOCIAL stream runs to tick 1000, while main's stops at 551.
- The question is whether head's continued stream is one stuck emitter. `cooperation_event` fires whenever an entity's `last_cooperation_decision` property is set, and the flag on head is `cooperation_active`.
- **Needed:** the per-entity `cooperation_event` spans (count, first tick, last tick) on head, and the same for main.
- **Never-exit test:** whether any entity emits from some tick to tick 1000 at one event per tick. If one does, that entity's events stand behind the move, and the row is not re-pinned.

## Row 3: urban_political_selfmodel_probe WORLD 0.19 -> 0.25 (200 ticks): NOT YET READ
- **Needed:** the per-type WORLD delta for the probe (as given for urban at 1000t).
- If the move is births' own events (`demographic_birth`, plus mortality and trauma), no loop is involved.
- If `hazard_drain_applied` (the flagged tag) is part of the move, give its per-entity spans in both arms.

## ENABLE_CAMP_NEST_SPREAD leftovers: (a), with corrected text
- **(a)'s proposed text is false.** The raid branch is already gone on main: intentional_divergences §2.125 (D70) removed the raid trigger and `RaidService.spawn_raid`.
- Since D70, `test_camp_raid_targeting` uses this world as a "matured camp raids nothing" test. The world also stays listed in `expected_world_flag_state.json`.
- So keep the world (not (b); retiring it breaks that test and fixture), and describe it truthfully.
- **The profile:** drop the `ENABLE_CAMP_NEST_SPREAD: "ON"` line. If `expected_world_flag_state.json` changes as a result, update it in the same PR. (Its current entry doesn't list the flag, so no change is expected.)
- **world.yaml description and the resolved copy:** "Camp-maturity calibration world: a camp seeded near maturity 80 adds no entity when it matures (raid removed by D70; nest-spread removed by TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND). Used by test_camp_raid_targeting."
  - Regenerate the resolved copy with its tool, not by hand.
  - It routes to rpg-planner (u24) via lead-planner.
- **wolf_den_near_forest.yaml:51 comment:** "Nest-spread was removed by TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND; wolves now come from births."
- **Other docs that still name the flag:**
  - **B5 trail:** ch05 §6 (05_world_evolution.md:432, :474) and parity entry world_dynamics.yaml:2060-2106. Add them to the B5 trail list next to ch05's Humanoid Reproduction section.
  - **Rule text:** docs/world_rules/life-body/ecology-population.md:88. It is catalog text, which I don't edit, so it goes to rpg-designer as a B5 item.
  - **Contract doc:** docs/world/raid_boss_camp_contract.md:53, the "Nest fork" section. rpg-planner-ubuntu should say whose doc it is; it needs the same one-line removal note.
  - **Plan:** rpg_m4_beyond_city_epic.md:62 is a dated plan, so it is left as history.
