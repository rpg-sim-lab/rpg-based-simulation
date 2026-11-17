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

# Births: blind predicted direction per corpus grade pillar (rpg-designer-ubuntu, 2026-11-18)
- **Asked by:** rpg-planner-ubuntu, after the run.
- **Blind:** I have seen no run values. My basis is only the scorer code on this worktree's main (3aafdb383):
  - `src/simulation_quality/scorers/*.py`;
  - `config/simulation_quality/scoring_weights.yaml`;
  - `quality_report.py`: the score is the sum of event deltas divided by `max(tick//4, last_event_tick)`, so a per-tick rate;
  - `event_shapers.py`.
- **Disclosure:** this was asked for after the run and written before I saw any value. lead-planner is told so.

## Mechanism common to every pillar
- Births add bodies. Most pillar events are emitted per entity, and the denominator is ticks, not entities.
- So every pillar whose events are mostly positive and per entity drifts up with headcount. A pillar moves the other way only where a newborn produces negative events.
- The old humanoid reproduction step, on a 50-tick cadence, is removed. Births replace it, at a 30-tick cadence for every kind with a profile. So I expect a net gain in births, not a swap.

| pillar | call | mechanism | confidence |
|---|---|---|---|
| WORLD | **up** | Every `entities_add` emits `demographic_birth` at +4 (`event_shapers.py:1168-1174`). Later non-combat deaths of newborns (starvation, age) emit `demographic_mortality` at +2. No WORLD rule is negative on a birth. | high |
| COGNITION | **up (small)** | `self_model_updated` (+1) and `belief_updated` (+2) are per entity. A newborn with a hunger law changes vitals, so it updates its self-model. `knowledge_default_fallback` (-2) has no emitter in src, so empty newborn knowledge costs nothing. **Condition:** newborns enter the strategy loop. If CHILD is skipped there, COGNITION is flat. | medium |
| SOCIAL | **flat** | The SOCIAL events need interactions: cooperation decisions, contracts, groups, reputation shifts over 0.5. A CHILD with no occupation and 0 gold rarely starts one. Inherited reputation is a value write and emits no delta. Possible small up: `grief_urgency_triggered` (+3) when a newborn dies near kin, and a faction-mate `cooperation_event` (+4). | medium |
| COMBAT | **up (small)** | Newborn wolves and spiders raise predator headcount, and low-hp CHILD bodies are prey. That gives more `combat_initiated`, `combat_resolved` and `entity_killed` (attrition). These are positive unless `early_extinction` or an `attrition_spiral` fires, which I don't expect at 1000t. | low |
| ECONOMY | **flat to up** | More eaters means more `resource_harvested` by adults feeding, and more `resource_node_depleted` (scarcity, positive weight). Newborns hold 0 gold, so there's no gold flow from them. | low |
| AGENCY | **up (small)** | Per-entity `action_executed` and `route_selected` events. Risk down: `defer_with_reason` / `population_stasis` if CHILD bodies mostly defer. | low |
| FACTION, PROGRESSION, INFORMATION, NARRATIVE | **flat** | No birth-driven event path. Children don't level, trade info or take quests in 1000t. | medium |

## Per-world note
- urban_political: humanoid-heavy, so the WORLD gain is mostly human and goblin births.
- hero_guild_routing: guild members are mostly job bodies. Births come only from mothers eligible under a profile, so its WORLD gain should be smaller than urban_political's.
- In both worlds WORLD moves the most.

## What would refute this
- **WORLD down or flat:** births are not reaching `entities_add`, or the removed humanoid step out-produced births at s42. Either is a finding, not a grade question.
- **COGNITION down:** newborns emit a negative cognition event I haven't found (`knowledge_rot` on leads they don't have, or `goal_lock_no_cognition`). That needs a trace.
