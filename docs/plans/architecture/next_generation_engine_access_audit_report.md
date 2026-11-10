---
status: active
layer: architecture
authority: P2
audience: agent
phase: open
date: 2026-11-11
tags: [architecture, engine, determinism]
---

# Next-generation engine: stage 1 access audit report

Ticket: TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT. Evidence base: main 993400a52. Main is now 2ea0e4d8f (#859, docs and tooling only): `git diff 993400a52 2ea0e4d8f -- src data config` is empty (exit 0, run 2026-11-11), so the base cells hold for both. Cells measured on branch `rpg-nextgen-access-audit` head f19379c43 (src diff vs 993400a52: 9 files, +767/-2). Observe-only; flag `ENABLE_ACCESS_AUDIT` (off by default, hash-neutral).

## Run

6 cells, 5000 ticks each, pinned runner (`PYTHONHASHSEED=0`) via the approved wrapper (sha256 39706ba7…), one cell at a time on an otherwise idle host. Every cell's end hash equals the 993400a52 base cell's `final_hash` (lane C's results in `/mnt/data2/rpg-measure/results/993400a52995-72320cac-5000/`); every cell has observations > 0; every cell observed the same 35 of 43 declared steps. Timing NOT MEASURED: the wall column is informational and makes no perf claim.

| cell | end hash (= 993400a52 base) | observations | distinct steps | wall s (informational) | peak RSS MB |
|---|---|---|---|---|---|
| crowded_frontier s42 | d842c209… MATCH | 160631 | 35 | 1336.2 | 575 |
| crowded_frontier s43 | 21ec90e1… MATCH | 159512 | 35 | 1329.4 | 573 |
| crowded_frontier s44 | 361f4a37… MATCH | 159597 | 35 | 1286.8 | 550 |
| crowded_frontier s45 | 27112822… MATCH | 162533 | 35 | 1528.9 | 601 |
| crowded_frontier s46 | 5b1f0092… MATCH | 163137 | 35 | 1684.8 | 647 |
| urban_political s46 | fc945eae… MATCH | 163668 | 35 | 1151.2 | 512 |

Interim evidence, not used below: the first two cells on the earlier head 11668e5b2 (s42, s43) also matched their base hashes. That head keyed the sampled timeline check by `id()` and reported 27 and 87 "findings"; they were `id()` reuse (see "Sampled content check"), which is why the check was changed.

## Declared, not exercised on the gate worlds

These 8 declared steps were never observed, identically in all 6 cells. This is not a pass for them. Reason, read from an earlier 300-tick probe on crowded s42 and urban s46 (flag mode and `should_run_phase` calls; the cell JSONs carry no skip counters): the feature flag is OFF (manager default), so `run_phase` returns before `should_run_phase`. No graph skips, no other cause. The other 4 cells are inferred from the identical observed set, not probed. The 300-tick probe covers only ticks 0-300.

| step | flag (OFF = skipped by run_phase) |
| --- | --- |
| memory_update | ENABLE_MEMORY_UPDATE |
| habit_bias_action_style | ENABLE_HABIT_BIAS_ACTION_STYLE |
| role_model_selection | ENABLE_ROLE_MODEL_IMITATION |
| self_model | ENABLE_SELF_MODEL_COGNITION |
| information_intent_execution | ENABLE_INFORMATION_INTENT_EXECUTION |
| information_propagation | ENABLE_INFORMATION_HUB_ACCUMULATION |
| world_emergence | ENABLE_WORLD_EMERGENCE |
| progression_conversion | ENABLE_PROGRESSION_EVOLUTION |


## Declared vs observed writes (union over 6 cells)

Writes are observed by diffing the input StateUpdate against the step's result (`su:<field>`, `eu:<bucket>`; entity ids folded out). A declared pattern may end in `*`.

Where the declared writes came from (`source` in `declarations.py`): 26 steps from the PhaseDependencyGraph output domains mapped to buckets, 12 from the feasibility review section 2 table, 5 from the step name alone (`first_pass`); 7 steps are declared coarsely as `su:*` (whole update). So a mismatch below mostly reads as a declaration that is too thin (graph domains are coarser than the buckets) rather than proof a step writes outside its remit; the two cannot be told apart from this data alone. **Attribution caveat:** a write is the diff of the step's input update against its result, so a bucket the step only re-copies, merges or compacts shows as a write (for example trust_boundary's eu:biological, eu:readiness_delta and eu:resource_transfers may come from update compaction, not from a write by the step). This audit cannot distinguish the two.

### Observed but not declared

| step | undeclared observed writes |
| --- | --- |
| trust_boundary | eu:biological, eu:readiness_delta, eu:resource_transfers |
| information_belief | eu:property_updates, eu:self_model_bundle_set |
| cooperation | eu:property_updates, su:metric_counters |
| action_routing | eu:biological, eu:cognition_bundle_set, eu:group_id_set, eu:readiness_delta, eu:resource_transfers, eu:social, eu:stamina_update, eu:strategic, eu:wound_update, su:rejection_events, su:rejections_delta, su:world_events_add |
| position_swaps | eu:navigation, eu:property_updates, eu:stamina_update |
| movement_routing | eu:cognition_bundle_set, eu:combat, eu:property_updates, eu:resource_transfers, eu:stamina_update, su:metric_counters, su:rejections_delta |
| interaction_enforcement | eu:interaction, eu:resource_transfers, su:rejections_delta |
| town_resolution | eu:combat, su:building_updates, su:metric_counters, su:resource_updates |
| world_dynamics | eu:combat, eu:strategic |
| resource_transactions | eu:biological, eu:combat, eu:identity, eu:intent_results, eu:interaction, eu:readiness_delta, eu:resource_transfers, eu:strategic, su:building_updates, su:corpses_add_or_update, su:corpses_remove, su:node_updates, su:rejection_events, su:rejections_delta, su:transaction_trace, su:world_events_add |
| strategic_intelligence | eu:interaction, eu:property_updates |
| near_death_hardening | eu:cognition_bundle_set |
| occupancy_resolution | su:rejection_events |
| lifecycle | eu:active, eu:cognition_bundle_set, eu:intent_results, eu:interaction, eu:inventory, eu:lifecycle |
| groups | su:next_group_id_set |
| expired_offers | eu:identity, eu:strategic |
| capacity_enforcement | eu:strategic |

17 of 35 observed steps write something their declaration does not list.


### Declared but not observed (observed steps only)

| step | declared writes never seen |
|---|---|
| trust_boundary | su:* |
| actor_validity | su:* |
| contracts | eu:inventory |
| blacksmith | eu:inventory, su:resource_updates |
| faction_awareness | su:faction_updates |
| military_conflict | su:faction_updates, su:world_events_add |
| combat_engagement | eu:combat |
| interaction_enforcement | eu:inventory, eu:social, su:node_updates, su:resource_updates |
| building_sabotage | eu:social, su:building_updates |
| town_resolution | eu:inventory, eu:social, su:world_updates |
| quest_rewards | eu:identity, eu:inventory, eu:resource_transfers, eu:reward |
| guild_visit | su:quest_registry_add |
| shop | eu:inventory, eu:social, su:resource_updates |
| paid_information | eu:inventory, eu:strategic, su:information_providers_update |
| evolution | eu:attributes, eu:identity |
| strategic_intelligence | eu:identity, eu:task |
| lead_contradiction | eu:strategic |
| near_death_hardening | eu:attributes |
| groups | eu:social, su:groups_remove |
| clan_lifecycle | su:clan_updates |
| expired_offers | su:* |
| diplomatic_transitions | su:world_events_add |

## In-place mutation of the INPUT update (most important for child 4)

Two steps mutate the update they were handed, in place, instead of returning a new one. A scheduler that gave a step its own copy of the update, or ran steps out of order, would change results.

How it was detected, as built: before each step the recorder takes a token for every field of the INPUT `StateUpdate` and for every bucket of each of its `EntityUpdate`s (the value for a primitive, (id, length) for a container, the id otherwise); after the step it takes the same snapshot of the same input object, and any token that changed is an in-place mutation (`observe.snapshot_update`, `observe.update_inplace`). It sees a bucket replaced or resized on the input update; it does not see an equal-length in-place edit inside a bucket's contents.

No tick count for this table: the recorder keeps the in-place mutation buckets as a per-step set over the run (`inplace_update_mutations`), not a per-tick counter, so how many ticks each step did this is not known from these cells and is not estimated here. (The hidden-mutation tables below do carry tick counts.)

| step | bucket(s) mutated in place |
| --- | --- |
| evolution | eu:combat, eu:identity, eu:property_updates |
| world_dynamics | su:world_updates |


## Hidden mutations of tick-start state

Detector (plan section 3a): Tier 1 is a content digest of a watch list read with plain `object.__getattribute__` (no properties), to depth 3 with a 400-node cap per digest: `route_plans`, `movement_cache`, `occupancy_snapshot`, `_occupancy_map_cache`, `transient_claims`, `_has_hostiles_or_dead_cache`, `world_indexes`, `_spatial_grid_cache`, `_region_list_cache`, `_node_map_cache`, `_corpse_map_cache`, `_ground_item_map_cache`, `_building_map_cache`, `_region_index_cache`, `_building_region_map_cache`, `_readonly_entities_cache`, and each entity's `timeline`. Tier 2 is identity plus length (deques included) for every other attribute of the state and of each entity. Beyond depth 3 or the node cap a node falls back to its id. Counts below are ticks seen, summed over the 6 cells (6 x 5000 = 30000 ticks per step at most).

### Watch list (Tier 1)

| step | field (ticks seen, summed over cells) |
| --- | --- |
| combat_engagement | world_indexes (2337 ticks) |
| cooperation | _readonly_entities_cache (680 ticks), entities[*].timeline (3195 ticks) |
| information_belief | _region_index_cache (931 ticks) |
| interaction_routing | _corpse_map_cache (28055 ticks), _ground_item_map_cache (28055 ticks), _node_map_cache (28055 ticks) |
| movement_routing | _occupancy_map_cache (24403 ticks), _region_index_cache (22986 ticks), route_plans (23822 ticks), transient_claims (30000 ticks) |
| position_swaps | _occupancy_map_cache (29994 ticks) |
| shop | _building_map_cache (479 ticks) |
| strategic_intelligence | _region_list_cache (14212 ticks), _spatial_grid_cache (18350 ticks) |
| town_resolution | _building_region_map_cache (1500 ticks), _region_index_cache (381 ticks) |
| world_dynamics | _region_index_cache (5702 ticks) |


Almost all rows are lazy `_..._cache` fields filled on first read: expected, low weight. Not caches: `route_plans` and `transient_claims` (movement_routing) are real state written outside the update, and `entities[*].timeline` (cooperation) is an append outside the update.

### Tier 2 hits (promote to the watch list)

| step | field (ticks seen, summed over cells) |
| --- | --- |
| combat_engagement | _index_hits (30000 ticks), _index_misses (2337 ticks) |
| strategic_intelligence | _index_hits (14204 ticks) |


These are hit/miss counters of the index cache. Plan section 3a promotes a hit "for the next run"; no next run is planned in v1, so `_index_hits` and `_index_misses` are promoted for child 4 or a v2 run and have not been re-run as watch-list fields. Nothing here suggests they carry decision state.

### Why the first run missed cooperation's `timeline.append`

`entity.timeline` is `deque(maxlen=200)` (`src/core/state.py:1018`). The first container fingerprint did not include `collections.deque`, so an append to a full deque (length unchanged) was invisible. The detector now includes deques and tokens a timeline by (deque id, length, element ids); positive control 1 appends to a deque already at maxlen=200 and asserts it is seen. After the fix cooperation's timeline append is observed (row above).

### Strategic cache flag (`_has_hostiles_or_dead_cache`)

Not seen mutated by strategic_intelligence in any cell (0 ticks), and it is on the watch list. Static reading: `src/core/state.py:1490` sets it at state construction; `src/systems/strategic_systems/intelligence.py:326-347` writes it only when it is None, which does not occur on tick-start state; `src/engine/pipeline_phases/actions.py:347` clears it on the per-actor sliding state, a different object from the tick-start state. So the observation and the reading agree; this is a reading plus an observation, not a proof.

### No hidden mutation observed, for the kinds a positive control proved detectable

25 steps: trust_boundary, actor_validity, contracts, blacksmith, faction_awareness, military_conflict, action_routing, interaction_enforcement, building_sabotage, quest_rewards, guild_visit, paid_information, resource_transactions, evolution, belief_staleness_decay, lead_contradiction, near_death_hardening, occupancy_resolution, lifecycle, groups, clan_lifecycle, expired_offers, capacity_enforcement, diplomatic_transitions, faction_sentiment. The positive controls (`tests/unit/engine/access_audit/test_observer_controls.py`) prove these kinds detectable: a timeline append (including on a full deque), a `route_plans` `object.__setattr__`, an in-place dict value change on a watch attribute, an equal-length list element swap on a watch attribute, a cache flag flip, a Tier 2 list append (reported for promotion), and a change in a process global. "No hidden mutation observed" means only that. It does not mean none exist.

### What the detector cannot see (plan section 3a, verbatim)

- an in-place change that keeps identity and length in a field **outside** the watch list;
- a write to an attribute that did not exist before the step and is removed again before the step returns;
- mutation of an object reached only through a process global outside the section 1 watch list.

Also: the depth-3 and 400-node caps; `id()` reuse inside one step; steps not exercised in these cells (the 8 flag-OFF steps); and the attribution caveat above. Positive control `test_blind_spot_an_in_place_change_outside_the_watch_list_is_NOT_detected` proves the first limit is real.

## Sampled content check of mutable timeline elements

Timeline elements are either frozen slots dataclasses (cooperation events, `src/domains/cooperation/events.py`; identity is content, so the per-step token covers them) or mutable pydantic `SimulationEvent` records (`src/observability/events.py:54`, `event_id: str` with a uuid4 default factory at `:56`; 19 direct subclasses, among them CombatDamageEvent, QuestEvent, GoldTransactionEvent, StrategicCognitionEvent in `src/observability/cognition/events.py:8`). The per-step token cannot see an in-place edit of a mutable element, so every 100 ticks the recorder compares each mutable element's content digest with the first one it saw. It names no step.

- Key: the baseline is per element, keyed by `id()` (no reference to the element is held, so lifetimes and later ids are unchanged), with the element's stable key stored alongside: its own `event_id`, else (tick, type, ordinal among same-tick same-type elements in that deque). A different stable key at a remembered id is a different event that reused the `id()`: counted as "replaced", not as a finding. Because the record is per element, one `SimulationEvent` shared by several entities' deques (the fan-out at `src/observability/entity_timeline.py:39-42`) is reported once; the reported `entity` and `index` are the last holder in dict iteration order. A hit records the changed field names with old and new values truncated to 80 chars.
- Result: 50 samples per cell, **0 edits in 300 samples; 860 replaced**. Per cell:

| cell | samples (every 100 ticks) | edits | replaced (id reused, not an edit) |
|---|---|---|---|
| crowded_frontier s42 | 50 | 0 | 20 |
| crowded_frontier s43 | 50 | 0 | 82 |
| crowded_frontier s44 | 50 | 0 | 26 |
| crowded_frontier s45 | 50 | 0 | 199 |
| crowded_frontier s46 | 50 | 0 | 523 |
| urban_political s46 | 50 | 0 | 10 |

- Reading: this is evidence, not proof, that no mutable timeline element is edited in place. It is the input for the frozen=True hygiene candidate under child 4, which this report does not file.
#### Limits of the sampled check

Sampled every 100 ticks, so an edit reverted before the next sample, or made to an element evicted before the next sample, is not seen. Fallback key: its ordinals shift if an earlier same-tick same-type element is evicted, so it would count as replaced (an undercount of edits). The share of sampled elements on the fallback key is 0 by construction: the writers of `entity.timeline` are `src/observability/entity_timeline.py:77` (`record_to_entity`, typed `SimulationEvent`, reached through `src/engine/kernel.py:1027`) and the cooperation phase (`src/domains/cooperation/phase.py:38,47,57,116`, frozen records, not sampled); every `SimulationEvent` has `event_id` at construction. `entity_timeline.py:52` (`_append_to_timeline`) also appends, but to the store's own `_timelines` dict, not to `entity.timeline`, and is not sampled. That holds for the code as of f19379c43; a new mutable event type without an `event_id` on a timeline would use the fallback.

## Process globals

Watch list (read through `sys.modules`, never imported from the hot path): `src.content.terrain_cost._terrain_cache`, `src.core.registries.runtime_content_source`, `src.content.common_knowledge_seed._warm_catalog_provider` and `._fallback_catalog`. The list was built by searching for module-level mutable objects reachable from `refine`; it is not proven exhaustive. This departs from plan section 1's list (registries, the content catalog, the terrain cache, the observability config): the terrain cache, the content catalog (the two `common_knowledge_seed` objects) and one registries-module global (`runtime_content_source`) are on the watch list; the only other module-level names in `src/core/registries.py` are `catalog_fingerprint` (a str, not watched); and no observability config object was found as a module global reachable from `refine`, so it is not on the list. Registry objects held on the kernel or on state, rather than as module globals, are not covered by this check at all. All of this is from a search of the source, not proven exhaustive.

No process-global change detected (watch list: see Limits).


## Cross-entity proxies

Two proxies for steps whose writes reach another entity's entry: (a) entries created for an entity id that was absent from the input update; (b) the most distinct entity ids written per bucket in one tick. Both are proxies, not an actor-versus-target trace.

| step | ticks creating entries | max entries created | max distinct entity ids written per bucket |
| --- | --- | --- | --- |
| action_routing | 381 | 2 | eu:biological (12), eu:cognition_bundle_set (4), eu:combat (4), eu:group_id_set (1), eu:interaction (2), eu:moved_this_tick (3), eu:navigation (3), eu:new_position (3), eu:readiness_delta (6), eu:resource_transfers (3), eu:social (4), eu:stamina_update (4), eu:strategic (1), eu:task (6), eu:wound_update (2) |
| belief_staleness_decay | 20 | 1 | eu:strategic (1) |
| capacity_enforcement | 0 | 0 | eu:strategic (19) |
| combat_engagement | 12938 | 9 | eu:cognition_bundle_set (23), eu:property_updates (23), eu:strategic (23) |
| contracts | 1219 | 4 | eu:social (7), eu:strategic (8) |
| cooperation | 21564 | 16 | eu:property_updates (22), eu:social (4), eu:strategic (13) |
| expired_offers | 0 | 0 | eu:identity (8), eu:strategic (8) |
| groups | 8 | 2 | eu:group_id_set (8), eu:strategic (12) |
| guild_visit | 0 | 0 | eu:strategic (2) |
| information_belief | 1 | 1 | eu:property_updates (1), eu:self_model_bundle_set (1), eu:strategic (1) |
| interaction_enforcement | 0 | 0 | eu:interaction (5), eu:resource_transfers (2) |
| interaction_routing | 0 | 0 | eu:interaction (8) |
| lifecycle | 0 | 0 | eu:active (2), eu:cognition_bundle_set (2), eu:intent_results (2), eu:interaction (1), eu:inventory (4), eu:lifecycle (2) |
| movement_routing | 14399 | 20 | eu:cognition_bundle_set (3), eu:combat (3), eu:moved_this_tick (22), eu:navigation (23), eu:new_position (22), eu:property_updates (3), eu:resource_transfers (1), eu:stamina_update (22) |
| near_death_hardening | 0 | 0 | eu:cognition_bundle_set (2), eu:combat (2) |
| occupancy_resolution | 0 | 0 | eu:moved_this_tick (6), eu:navigation (5), eu:new_position (6) |
| position_swaps | 108 | 3 | eu:moved_this_tick (4), eu:navigation (4), eu:new_position (4), eu:property_updates (4), eu:stamina_update (4) |
| resource_transactions | 0 | 0 | eu:biological (2), eu:combat (3), eu:identity (2), eu:intent_results (3), eu:interaction (1), eu:inventory (3), eu:readiness_delta (3), eu:resource_transfers (3), eu:strategic (2) |
| strategic_intelligence | 1011 | 4 | eu:interaction (8), eu:navigation (9), eu:property_updates (1), eu:strategic (12) |
| town_resolution | 402 | 7 | eu:combat (15) |
| trust_boundary | 0 | 0 | eu:biological (12), eu:readiness_delta (5), eu:resource_transfers (2) |
| world_dynamics | 21894 | 14 | eu:combat (2), eu:strategic (25) |


Class S (static, not observed): reading the step bodies shows three known cross-entity writers that child 4's merge rules must cover. Cooperation's JOIN_PARTY promotion writes an EntityUpdate for the offering partner, not the acting entity (`src/domains/cooperation/phase.py:164-194`, via `ContractService.accept_contract`). Trust and grudge are carried in `grudge_delta`/`fear_delta`/`debt_delta` maps keyed by another entity id and merged by addition (`src/core/updates.py:312-357`). The combat witness tier updates each witness's own OpponentModel for the participants of a fight (`src/domains/combat_engagement/phase.py:179-205`, section 13.7). This was read, not traced per actor, and no follow-up ticket is proposed here.

## Identity-only replacements (A3)

A bucket replaced by an equal object (identity changed, value equal) is a write by identity but not by value. No bucket's `==` raised in any cell. Many steps replace most `su:*` buckets by equal objects; cause not established here (copy or rebuild of the update), so those are summarised by count.

| step | eu buckets replaced by an equal object | number of su:* buckets so |
|---|---|---|
| action_routing | eu:navigation, eu:task | 1 |
| actor_validity | - | 2 |
| belief_staleness_decay | - | 39 |
| building_sabotage | - | 1 |
| combat_engagement | eu:cognition_bundle_set | 39 |
| diplomatic_transitions | - | 38 |
| faction_sentiment | - | 38 |
| groups | - | 4 |
| information_belief | - | 39 |
| interaction_enforcement | - | 2 |
| interaction_routing | eu:interaction | 0 |
| lifecycle | eu:resource_transfers | 13 |
| movement_routing | - | 2 |
| near_death_hardening | eu:cognition_bundle_set | 0 |
| occupancy_resolution | eu:navigation | 2 |
| quest_rewards | - | 1 |
| resource_transactions | eu:interaction, eu:new_position | 14 |
| shop | eu:resource_transfers | 0 |
| strategic_intelligence | eu:interaction, eu:property_updates, eu:strategic | 0 |
| town_resolution | - | 4 |
| trust_boundary | eu:readiness_delta, eu:resource_transfers | 7 |
| world_dynamics | - | 39 |

## Reads (statically derived, not observed)

Reads are a static inventory, NOT a check. Each step's declared `reads_tick_start` was produced from the same AST scan of its entry function (`state.X` and `getattr(state, "X")`), then pinned in `declarations.py` so a new read in the entry fails `test_declarations`. Declared and scanned reads therefore agree by construction (0 mismatches carries no information). The scan is non-transitive (reads in callees are not seen): a lower bound. Steps with `entry=None` have no scan. Nothing was observed at runtime.

| step | statically derived reads |
|---|---|
| trust_boundary | entity_updates, rejection_events, rejections_delta |
| actor_validity | entities, tick |
| memory_update | entities, tick |
| habit_bias_action_style | entities |
| role_model_selection | entities, tick |
| self_model | entities, pending_self_model_information_events, tick |
| information_belief | entities, local_scars, regions, tick |
| information_intent_execution | entities, tick |
| cooperation | entities, groups, periodic_due_ticks, social_cooperation_enabled, tick |
| contracts | entities, tick |
| blacksmith | building_tiles, buildings, entities |
| faction_awareness | factions |
| information_propagation | factions, tick |
| military_conflict | factions, regions, tick |
| action_routing | entities, tick |
| position_swaps | entities |
| movement_routing | entities |
| combat_engagement | entities, tick |
| interaction_routing | entities |
| interaction_enforcement | chests, corpses, entities, ground_items, resource_nodes, tick |
| building_sabotage | entities |
| town_resolution | buildings, entities, global_resources, owed, recent_world_events, regions, tick, town_tiles |
| world_dynamics | chests, entities, feature_flags, next_entity_id, regions, tick |
| world_emergence | entities, seed, tick |
| quest_rewards | - |
| guild_visit | buildings, entities, feature_flags |
| shop | buildings, entities, tick |
| paid_information | entities, information_providers, tick |
| resource_transactions | - |
| evolution | entities, tick |
| progression_conversion | entities, progression_conversion_enabled |
| strategic_intelligence | _has_hostiles_or_dead_cache, entities, tick, town_center, town_tiles |
| belief_staleness_decay | entities, tick |
| lead_contradiction | entities, information_providers, tick |
| near_death_hardening | entities, tick |
| occupancy_resolution | entities, tick |
| lifecycle | entities, tick |
| groups | entities, groups, region_loyalty_pressure, tick |
| clan_lifecycle | clans, entities, tick |
| expired_offers | entities, tick |
| capacity_enforcement | entities, tick |
| diplomatic_transitions | no scan (entry=None) |
| faction_sentiment | no scan (entry=None) |

## Re-proof on the merged tree (crowded s42, 5000 ticks)

| arm | tree | end hash |
|---|---|---|
| plain arm_child (lane C) | main 993400a52 | d842c20983d731d6454f72aa79566583b96bd17c7c198dd1e2b69fe10b71ddde |
| audit ON (approved wrapper) | 86b30e3e7 (main 993400a52 + this branch, earlier build) | d842c20983d731d6454f72aa79566583b96bd17c7c198dd1e2b69fe10b71ddde |
| audit ON (approved wrapper) | f19379c43 | d842c20983d731d6454f72aa79566583b96bd17c7c198dd1e2b69fe10b71ddde |

MATCH. Caveat: #857 did not move this seed's trajectory (the 993400a52 base hash equals the cefa99b07 one), so this shows neutrality on the merged tree, not across a moved trajectory. The other 5 cells matched their 993400a52 base cells in the Run table.

## Limits

- Reads are not observed (no read proxy, per the planner ruling of 2026-11-10).
- Timing NOT MEASURED; no perf claim.
- 6 cells on 2 worlds; steps behind OFF flags are unexercised.
- The recorder is passed via `state.feature_flags["ACCESS_AUDIT_SINK"]` (not hashed, `compare=False`); a checkpoint pickles the whole state and would carry it: unsupported with the audit on. This departs from plan section 3 (records in a kernel-owned auditor); the PR states it.
- The audit writes none of the fields in TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ.
- Debt: the recorder is a runtime object held on `feature_flags["ACCESS_AUDIT_SINK"]`. Acceptable for a flag-off, observe-only audit, but not a pattern for child 4 to build on.
