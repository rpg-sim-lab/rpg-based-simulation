---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES
phase: done
date: 2026-11-14
tags: [world]
---

# Investigation: why `calamity_intensity` never leaves 0.0 (read-only, main 00f09e05a)

Owner approval: #715 6843938212 (read first). No src, test or ledger edits; any ledger edit later goes through tools/parity_ledger_writer.py.

## 1. The producer
- `CalamityService.apply_calamity_consequences` (src/world/calamity.py:87-107): for each entity in `recent_deaths` it finds the region (`LegalityServiceV2.get_region_for_position`, :93-94) and, when `entity.kind == "hero" and region.hazard_level > 0.5` (:99), writes `WorldUpdate(calamity_intensity_set=min(1.0, current + 0.05))` (:100-105).
- **It has no caller.** `apply_calamity_consequences(` appears in no production file under src/: the only mentions are its own definition and a comment in src/world/displacement.py:27. Callers in tests only: tests/unit/world/test_calamity_raid.py and tests/architecture/test_calamity_intensity_producer_unwired.py (a "welcome failure" that pins zero callers). `process_world_dynamics` (called at src/engine/world_dynamics.py:204) does not call it.
- Other writers of `calamity_intensity_set`: only `CalamityPressurePropagator.propagate_seasonal` (src/world/calamity.py:164-170, called at src/engine/world_dynamics.py:281). The apply path reads the field at src/engine/apply_plan.py:180 and writes it at :217; `WorldUpdate.merge` at src/core/update_models/world.py:67. The initial value is `RegionState.calamity_intensity: float = 0.0` (src/core/state.py:290); no world data file sets a nonzero value.
- The propagator only spreads: sources need `calamity_intensity >= 0.10` (`PROPAGATION_THRESHOLD`, :122, :147-148); every 500 ticks (:120, :133) a neighbor gets `min(1.0, neighbor + 0.15 * source)` (:149-153). It cannot create intensity from zero.
- Existing evidence that the producer is never invoked: registries/mechanisms.yaml `calamity_intensity` (state: orphan, verified by a per-method call counter, positive-controlled, 0 calls over crowded_frontier, quest_dense_frontier, hero_guild_routing, frontier_living_world, …).

## 2. Reachability by data (resolved worlds, data/worlds/<w>/resolved/world.resolved.yaml)
Regions with `hazard_level > 0.5`: crowded_frontier 4 (orc_stronghold 3.0, goblin_camp_edge 3.0, goblin_camp 3.0, bandit_road 2.0); urban_political 1 (bandit_road 2.0); frontier_living_world 6 (haunted_battlefield 4.0, goblin_camp_edge 3.0, goblin_camp 3.0, wolf_den 2.0, old_mine 2.0, bandit_road 2.0); highland_traverse 4 (mountain_pass_zone 2.5, wolf_den 2.0, near_forest 1.5, river_ford 1.0); frontier_marches 8 (haunted_battlefield 4.0, orc_stronghold 3.0, goblin_camp_edge 3.0, goblin_camp 3.0, swamp_border_territory 2.5, wolf_den 2.0, old_mine 2.0, bandit_road 2.0).
Hero recipes (role `hero`): crowded_frontier, urban_political and frontier_marches each have 3, count 1 each, all `spawn_region: hometown` (hazard 0.0). frontier_living_world and highland_traverse have no hero recipe. So the data does not make the trigger impossible in three worlds (hazard regions exist and heroes exist), but heroes spawn at hometown and must travel into a hazard region and die there. Whether they do is not established by data alone.

## 3. Consumers (what stays inert while it is 0.0)
- Boss gate: `high_intensity_regions` needs `calamity_intensity > 0.3` at `tick % 5000 == 0` and `tick - last_calamity_tick >= 2000` (src/world/calamity.py:37-46); the boss and magical/demonic spawn behind it are also flag-gated off (`world_boss_spawn_enabled`, :80; `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`, :62).
- Displacement: `DisplacementService.compute_displacement` relocates living entities out of any region with intensity >= 0.6 (src/world/displacement.py:27, 38; called at src/engine/world_dynamics.py:298).
- Regional drain: `hazard_level * (1.0 + calamity_intensity)` (src/world/environment.py:34-36) is just `hazard_level` at 0.
- Transformation requirements: `calamity` and `calamity_less` (src/world/transformation.py:57-59, called at src/engine/world_dynamics.py:314).
- Not a consumer: the contract `docs/world/threat_and_consequences_contract.md:55` mentions "calamity_intensity reduced" on a world boss defeat; no such code was found in this read.

## 4. Docs that describe intensity as working
- docs/mechanics/05_world_evolution.md:494 (the region filter `calamity_intensity > 0.3` of the magical/demonic path); :127 (drain independent of intensity scaling); :351 (boss spawns, inert while deferred, owner decision 14).
- docs/world/ecology_and_calamity_contract.md:79 ("the region with the highest calamity intensity is selected") and :92 ("Hero death in a region with `hazard_level > 0.5` raises that region's `calamity_intensity` by +0.05 per death. Intensity decays naturally if the region stabilises"): both contradicted by the code (no caller, no decay code) and by ENV-06 (docs/world_rules/space-environment/environment.md:176-187: intensity rises only while a region stays above the instability threshold for a sustained period; no single death raises it).
- docs/world/home_exile_refugee_contract.md:69-93 (displacement at >= 0.6; the 0.6 vs "hazard > 0.5 gates growth" comment).
- Parity ledger: docs/parity_ledger/world_dynamics.yaml WORLD-084 (line 1024; status divergent; names the producer "has no caller in src/ (pinned by tests/architecture/test_calamity_intensity_producer_unwired.py)"), WORLD-105 (:1405, verified, the propagator), WORLD-029 (:323) and WORLD-060 (:361), WORLD-063 (:773, test_calamity_intensity_scales_regional_drain.py), WORLD-121 (:1905), WORLD-DISPLACE-001 (:2261), all verified; docs/parity_ledger/infrastructure.yaml INFRA-258 (:3660, :3714) and INFRA-246 (:3878), verified, which describe `calamity_intensity > 0.3` as a separate precondition on natural firing.

## Supersession
The ticket's own Scope block records that owner decision 10 / rule ENV-06 (2026-10-05) superseded the "wire the existing method" idea: the producer to build is the sustained-instability escalation, sequenced after TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES. This read confirms the finding stands on current main: the existing method is orphaned, the propagator only spreads, and nothing raises intensity.

## Open
- Whether heroes ever die in a hazard > 0.5 region in a corpus run is not measured; since the method has no caller the answer does not change intensity. A spy is only needed if the designer wants the counterfactual (how often the old rule would have fired).

## Outcome (2026-11-14): docs-only close, rpg-designer ruling (session message; text in `designer_ruling.md`)

No spy, no re-scope. Superseded claims rewritten with the ENV-06 text (ecology_and_calamity_contract.md:92, threat_and_consequences_contract.md:55); ENV-06 law with no code kept and marked "not built" (the decay clause at ecology_and_calamity_contract.md:92); a Current-play note at each consumer (ecology_and_calamity_contract.md:79, Bible 05 :127 :351 :494, home_exile_refugee_contract.md after the displacement paragraph); ledger support_boundary on WORLD-105, 029, 060, 063, 121 and WORLD-DISPLACE-001 (verified, through tools/parity_ledger_writer.py), the WORLD-084 divergence_note append (divergent). INFRA-258 (text, support_boundary) and INFRA-246 (divergence_note) described the `> 0.3` precondition as "hero-death-dependent"; corrected to the code fact (rpg-planner ruling), status unchanged. registries/mechanisms.yaml `calamity_intensity` already carries the ENV-06 pointer and stays orphan (not edited). The transformation requirements are documented only in parity entry WORLD-062 (world_dynamics.yaml ~:414); it gained a support_boundary (rpg-planner ruling): MOUNTAIN->VOLCANIC can never fire in play, WASTELAND->PLAINS is gated by trauma alone. The ENV-06 producer got its own P2 todo: TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT. The architecture pin's docstring now cites ENV-06 and owner decision 10.
