---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, engine, determinism, planning]
---

# Merge inventory: every StateUpdate and EntityUpdate field, on main 1fb40ac76


Evidence for `TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC` (child 4); the spec is `next_generation_engine_contract_spec.md`. A static read of `origin/main` `1fb40ac76`, 2026-11-09, by a research subagent of architecture-planner-u24; nothing was run. Three items were rechecked by hand: §5 items 1, 3 and 4.
Scope: every field of `EntityUpdate` (src/core/updates.py:697-803) and `StateUpdate` (src/core/updates.py:1015-1311) plus the nested update types they carry, as folded by `AuthoritativeApplyPipeline.refine` (src/engine/pipeline.py:42-467) and consumed by `ApplyPath.apply_generation` (src/engine/apply.py:241-610), `ApplyPlanBuilder.build_plan` (src/engine/apply_plan.py:119-417) and the component patches (src/engine/patches.py:17-836).

All paths are relative to the repo root, and every line number refers to origin/main. The ticket's citation `updates.py:788-803` is the body of `EntityUpdate.merge`. The class itself starts at :697.

## 0. How the fold works

- **Shape.** `refine` threads one `StateUpdate` through about 45 `run_phase(name, upd, fn, flag)` calls (pipeline.py:103-134). Each step returns a new `StateUpdate`. There are two step shapes:
  - **Rewrite steps** take `u` and return `replace(u, ...)`. Examples: action_routing, movement, economy and groups.
  - **Additive steps** return `u.merge(X)`, where `X` is a fresh StateUpdate built from tick-start `state`. Examples: information_belief (pipeline.py:202), faction_awareness (:241), information_propagation (:251), diplomatic_transitions (:282), military_conflict (:292), combat_engagement (:321), belief_staleness_decay (:403) and faction_sentiment (:438).
- **Merge helpers.**
  - `StateUpdate.merge` (updates.py:1106-1110) calls `merge_many` (updates.py:1112-1298).
  - Group fields are merged by `merge_group_fields` (src/core/group_update_merge.py:7-23).
  - Per entity, `EntityUpdate.merge` (updates.py:766-803) calls each nested `X.merge`.
  - At apply, `extract_patches` (patches.py:771-836) turns the single merged EntityUpdate into ComponentPatches. The order is fixed: Kind, Lifecycle, Biological, Interaction, Identity, Navigation, Combat, Stamina, Inventory, Equipment, Strategic, Quest, Social, Task, Attribute, Reward, Wound, StatusEffect, SelfModel, Cognition.
  - The patches run *after* the passive pre-pass (apply.py:117-219, then :222-223), then the derived-stat recompute (apply.py:642-699), then the region re-resolve (apply.py:231-237).
- **Compactor.** `StateUpdateCompactor.compact_with_metrics` (src/engine/compactor.py:37-154) runs once, before the first step (pipeline.py:97). It nulls sub-updates whose `is_noop()` is true (compactor.py:131-136) and drops empty EntityUpdates (compactor.py:142-145).
- **What "order-sensitive" means here.** The durable result after apply depends on the order in which refine steps (or list entries) contributed. There are three ways this happens:
  - last-writer-wins (LWW) on merge;
  - list order that apply consumes sequentially with clamps or capacity checks;
  - float re-association. This one is marked "weak".

## 1. EntityUpdate fields (30)

| # | Field (updates.py line) | Type | Merge rule in refine (updates.py line) | Refine writers (file:line; phase) | Apply consumption | Order-sensitive? |
|---|---|---|---|---|---|---|
| 1 | `entity_id` :704 | int | Key. A merge across ids raises (:770-771) | all | Selects the entity (apply_plan.py:380-386) | no. It is the key |
| 2 | `kind_set` :705 | Optional[str] | LWW non-None (:774) | engine/world_dynamics.py:317 (world_dynamics) | KindPatch (patches.py:50-52). Compactor drops it when it equals the current kind (compactor.py:84-86) | **yes**. LWW |
| 3 | `new_position` :706 | Optional[tuple] | LWW (:775) | engine/movement.py:100,388 and engine/pipeline_phases/movement.py:455 (position_swaps/movement_routing); engine/lodging.py:150,218,232,328,373-377 (grant_beds in resource_transactions, place_leavers in occupancy_resolution); engine/pipeline_phases/occupancy.py:151 (occupancy_resolution); world/displacement.py:63 (world_dynamics). trust_boundary and actor_validity strip or reset it (pipeline_phases/trust.py:163-180, actor_validity.py:127) | NavigationPatch `_fast_replace_navigation` resets `region_id` to None (patches.py:296-298). It is re-resolved at apply.py:231-237 | **yes**. LWW. Occupancy runs last among movers (pipeline.py:407) |
| 4 | `moved_this_tick` :707 | bool | OR (:776) | same sites as `new_position` | Counted only as `movement_count` (apply.py:387). The compactor clears it with a no-op position (compactor.py:92-98) | no. OR is commutative |
| 5 | `readiness_delta` :708 | float | Sum (:777) | engine/lodging.py:158; engine/work_shift.py:89,98 (action_routing, town_resolution); engine/domain/{core,combat,skill,aoe}_actions.py, many sites (action_routing via domain_logic). Zeroed by trust_boundary (trust.py:174) | Single clamp [0,100] after the sum (patches.py:344-345). The passive regen is applied first (apply.py:186-190) | weak. Float re-association only. One clamp |
| 6 | `active` :709 | Optional[bool] | LWW (:778) | systems/lifecycle_systems/lifecycle.py:271 (lifecycle); world/boss.py:156,267 (world_dynamics) | LifecyclePatch sets it before the lifecycle fields (patches.py:72-73). Compactor prunes it when equal (compactor.py:88-90) | **yes**. LWW |
| 7 | `interaction` :710 | InteractionUpdate (updates.py:72-91) | Nested (:779): `target_node_id`/`kind` LWW, `progress_delta` sum, `reset` OR (updates.py:87-90) | engine/interaction.py:85-208 (interaction_enforcement); pipeline_phases/interactions.py:57 (interaction_routing); engine/economy.py:150 (resource_transactions); systems/strategic_systems/intelligence.py:399,404,649,677 (strategic_intelligence); work_shift.py:87,98 | `reset` discards all progress (patches.py:156-157). Otherwise progress is added and the sets are LWW (patches.py:159-164) | **yes**. LWW, and reset dominates |
| 8 | `resource_transfers` :711 | List[ResourceTransferIntent] (update_models/resources.py:12-46) | Concat (:780) | combat/core/skill actions (action_routing); blacksmith.py:254; shop.py:92; pipeline_phases/paid_information.py:184; quest_opportunity_rewards.py:98 (quest_rewards); lodging.py:150-204; interaction.py:201; domains/progression/resolver.py:77 (progression_conversion); lifecycle.py:303 (lifecycle). Resolved and cleared (`resource_transfers=[]`) by economy.py:256 in resource_transactions. Re-resolved for later emitters only by `_resolve_death_transfers` (pipeline.py:570-578) | Resolution walks entities in sorted-id order (economy.py:57) and each entity's list in order, against shared `reservations` (economy.py:49-51). Apply runs `InventoryService.apply_transfer` per entry in list order (patches.py:401-403; core/inventory.py:22-29), with a gold clamp ≥0 and a weight capacity on adds (inventory.py:150+) | **yes**. Order decides who wins a reservation. The clamp and capacity are applied per entry |
| 9 | `identity` :712 | IdentityUpdate (:240-292) | Nested (:781). `role/faction/craft_target/evolution_level/life_stage/class_id/unspent_ap_set` LWW. `recipes/breakthroughs/skills/traits_add/remove` are a sorted set union. `cooldown_updates` is dict LWW per key. The deltas sum (:275-291) | evolution.py:133 (evolution); blacksmith.py:160,254; economy.py:329; intelligence.py:699,853; lifecycle.py:194,219; social_systems/contracts.py:326 (expired_offers); party_lifecycle.py:232 (groups); boss.py:265 and creature_territory.py:71 (world_dynamics); progression/resolver.py:87 | IdentityPatch (patches.py:190-254). `unspent_ap_set` overrides the delta (:227-228). Traits are computed as `(old∪add)−remove` (:231). RewardPatch then re-levels from xp (patches.py:656-666). Derived stats are recomputed (apply.py:642-699) | **yes**. LWW on sets and cooldowns |
| 10 | `attributes` :713 | AttributeUpdate (:425-457) | Int sum (:444-457) | evolution.py:125; economy.py:333; domains/demographics/cohort.py:127; core_actions.py:400 | Adds, then `enforce_attribute_caps` once (patches.py:615-640) | no. Integer sum with one cap |
| 11 | `inventory` :714 | InventoryUpdate (update_models/inventory.py:8-29) | Nested: `items_add/remove` concat, `gold_delta` sum (inventory.py:19-26). Stripped by trust_boundary (trust.py:168) | economy.py:253,311 (accumulated accepted transfers); town_resolution.py:138,177; action_intent.py:214 | `InventoryService.apply_update`: removals, then adds with a weight/slot cap; `gold` is clamped at 0 (core/inventory.py:150+). Runs before the transfers (patches.py:399-403) | **yes**. Capacity is checked as items are added in list order |
| 12 | `strategic` :715 | StrategicUpdate (:525-640) | Nested (:784). All `*_add_or_update` / `*_remove` lists concat. `current_project/objective`, `overload_*`, `last_routing_*` and `home_region_id_set` LWW. `boredom_delta` sums (:597-640) | Many: cooperation phase.py:192 and services.py:305 (cooperation); information phase.py:76,173; combat_engagement phase.py:378,454; contracts.py:76 (contracts); blacksmith.py:198,215; world_dynamics.py:196; displacement.py:63; economy.py:337; lodging.py:119,140; guild_visit.py:84; capacity_enforcement.py:152,174; lead_contradiction and belief (STATIC-ONLY: scan did not attribute a line, UNVERIFIED) | StrategicPatch (patches.py:453-524). Per collection the adds apply in list order, last entry per id wins, then the removes (remove beats same-tick add) (:459-467). `turning_points` are concatenated, then truncated to the last `max_turning_points` (:489-493). `committed_intentions` are sorted by `sequence_index` (:469-477). `home_region_id` is the inverse: the existing value wins (:522) | **yes**. Last occurrence per id wins. The pipeline comment depends on this (pipeline.py:395-401) |
| 13 | `biological` :716 | BiologicalUpdate (:393-423) | Deltas sum. `*_set` LWW (:411-423). Stripped by trust_boundary (trust.py:175) | economy.py:331 (contingent `biological_upd`); building_services.py:80; core_actions.py:66,114,129 | `*_set` overrides the delta. Clamp [0,100] (patches.py:123-135). Runs after the passive hunger/sleep pre-pass (apply.py:119-124, 208-212) | **yes**. LWW on sets, and a set masks every delta |
| 14 | `social` :717 | SocialUpdate (:303-391) | `trust/grudge/place_attachment/regional_reputation/combat_loss` **sum**. `familiarity/debt/fear/salience/rejection_increment` are **dict LWW per key** (:373-384). `bond_updates`, `betrayal_records_add`, `nemesis_promotion` and `contracts_*` concat. `reputation_set`/`last_offer_tick_set` LWW | cooperation/phase.py:261 (cooperation, trust+grudge); contracts.py:76; combat_actions.py:102 and core_actions.py:202-543 (action_routing); party_lifecycle.py:232 (groups) | `RelationshipService.process_update` (systems/social_systems/relationships.py:24-134). Summed deltas are clamped once (trust [-1,1] :41, grudge [0,5] :54). `bond_updates` apply sequentially with a per-entry clamp (:61-91). `rejection_count` is rebuilt from **only** the keys in this update (:133) | **yes**. The LWW dict deltas lose writes. The sequential bond clamp depends on order |
| 15 | `quest` :718 | QuestUpdate (update_models/quests.py:8-68) | Grouped by `quest_id` into `MULTI`: progress sums, `status_set` LWW, sorted by id (quests.py:16-63) | combat_actions.py:83; movement_actions.py:38; aoe_actions.py:101; economy.py:250,343; trust strips status (trust.py:189) | QuestPatch updates `strategic.projects` *after* StrategicPatch (patches.py:540-556) | **yes**. LWW on status |
| 16 | `reward` :719 | RewardUpdate (:504-523) | Sum. Stripped by trust_boundary (trust.py:169) | economy.py:341; evolution.py:133 | RewardPatch, then `LevelingService.process_progression` (patches.py:656-666) | no. Sum |
| 17 | `lifecycle` :720 | LifecycleUpdate (:464-502) | `age_delta` sums. Ten `*_set` fields LWW (`_LIFECYCLE_SET_FIELDS` :460-461, :497). Lists concat. `reproduction_cooldowns_add` is dict LWW | lifecycle.py:271,287 (lifecycle); reproduction_humanoid.py:106-107 and boss.py:265 (world_dynamics) | LifecyclePatch (patches.py:69-107). It clears the stale `passive_death_cause` (:102-105) | **yes**. LWW on death fields |
| 18 | `combat` :721 | CombatUpdate (:104-166), carrying CombatIntent (:93-102) | Numeric deltas sum. `attacker_id`+`hit_tick_set` LWW as a pair (:146). `alive_set` LWW. `outcome_kind`: the first non-SURVIVE value sticks unless a later one is KILL (:150-151). `equipment_upd`/`attacker_equipment_upd`/`wound_update` are **replaced**, not merged (:160-162). `social_upd`/`strategic_upd` merge. `trace` dict LWW. **`merge` returns self when `other.is_noop()`**, and `is_noop` (:133-137) ignores every nested/flag field | combat.py:205-557 via combat_actions.py:68-105, skill_actions.py:119 and aoe_actions.py:61-69 (action_routing); world_dynamics.py:108 (hazard); town_resolution.py:99,109; evolution.py:133; hardening.py:103 (near_death_hardening); lodging.py:158; movement.py:330. Stripped by trust_boundary (trust.py:176) | CombatPatch (patches.py:322-348) applies only hp/max_hp/atk/def/speed/perm bonus/alive and the attacker pair. `hazard_damage`, `outcome_kind`, `is_lethal`, `trace`, `simultaneous_intents`, `resource_transfers` and the nested `*_upd`/`wound_update` are **never applied**. Producers must unpack them (combat_actions.py:70-72, 104-108) | **yes**. Attacker LWW and outcome precedence. Payloads riding in a "no-op" CombatUpdate are silently dropped |
| 19 | `equipment` :722 | EquipmentUpdate (:46-70) | `slot_updates` dict LWW. `durability_delta` sum per slot. `durability_set` dict LWW | combat_actions.py:68; skill/aoe actions; evolution.py:133; economy.py:339; progression/resolver.py:41 | EquipmentPatch: the delta is applied, then the set overrides it, clamp [0,100] (patches.py:422-437) | **yes**. LWW on slots and sets |
| 20 | `navigation` :723 | NavigationUpdate (:168-218) | Nearly every field LWW. `target_clear/clear_target/clear_path/lodged_in_clear` OR. `wait_count`/`oscillation_count` sum (:196-218) | movement.py:100,202,256,388 (movement_routing/position_swaps); lodging.py:126-376; blacksmith.py:254; intelligence/tactical (strategic_intelligence, action_routing); trust attaches failure_reason (trust.py:157-160) | NavigationPatch (patches.py:277-301). `target_set` beats `target_clear`. `lodged_in_clear` beats `lodged_in_set` (:294) | **yes**. LWW |
| 21 | `task` :724 | TaskUpdate (:220-238) | `work_kind_set` LWW. `payload_set` dict-merge LWW per key. action_routing **replaces** the actor's whole task (pipeline_phases/actions.py:212, 318-330) | actions.py (action_routing); tactical*/intelligence (strategic_intelligence); progression/resolver.py:50-96; lodging.py:232; sleep_debt.py:69; candidate_selector.py:314 | TaskPatch replaces the payload wholesale (patches.py:591-599) | **yes**. LWW plus whole replace |
| 22 | `stamina_update` :725 | StaminaUpdate (:642-659) | Delta sum. `current_set`/`max_stamina_set` LWW | combat_actions.py:113; skill/aoe actions; movement.py:388; pipeline_phases/movement.py:455 | `(set or current)+delta`, clamped [0, max]. `max_stamina_set or ...` treats 0.0 as unset (patches.py:364-375). The aggressive compactor drops deltas <0.1 (compactor.py:126-128) | **yes**. LWW on set |
| 23 | `wound_update` :726 | WoundUpdate (:661-678) | Lists concat | combat_actions.py:105; skill_actions.py:122; aoe_actions.py:72 (unpacked from CombatUpdate) | WoundPatch appends wounds and scars, marks heals (patches.py:682-693). Runs after CombatPatch. Derived stats are recomputed (apply.py:656) | **yes**. The wounds tuple order is the merge order |
| 24 | `status_effect_update` :727 | StatusEffectUpdate (:680-695) | Concat | **none in src/** (git grep finds no `status_effect_update=` outside patches.py:709,828) | StatusEffectPatch: remove by kind, then append (patches.py:711-720) | latent. Would be yes (list order) |
| 25 | `group_id_set` :728 | Optional[int] (-1 = clear) | LWW (:797) | systems/world_systems/groups.py:112-306 (groups); combat_actions.py:108 (betrayal −1) | IdentityPatch: `-1` becomes None (patches.py:235-237). Nulled by `resolve_group_adds` for a rejected add (apply_plan.py:76-84) | **yes**. LWW |
| 26 | `self_model_bundle_set` :729 | Any (whole SelfModelBundle) | **Whole-object LWW** (:798) | information/phase.py:76 (information_belief); action_intent.py:214; lead_contradiction.py:221 | `changes["self_model"] = bundle` (patches.py:738-740) | **yes**. Whole replace |
| 27 | `cognition_bundle_set` :730 | Any (whole CognitionModel) | **Whole-object LWW** (:799). Writers follow a read-through-then-replace convention (core/cognition_write.py:6-48; pipeline.py:162-188) | memory/phase.py:66; habit_phase.py:55; role_model_phase.py:80; combat_actions.py:132-134 (action_routing); movement.py:395; combat_engagement/phase.py:172-175,459; quests.py:212,242 (quest_rewards); hardening.py:106; lifecycle.py:139 | `changes["cognition"] = bundle` (patches.py:766-768) | **yes**. Whole replace. Correctness depends on every writer reading through |
| 28 | `intent_results` :731 | List[IntentResult] | Concat (:800) | economy.py:253 (resource_transactions); combat_engagement/phase.py:174,378,454; information/phase.py:76 | **Replaces** `identity.latest_intent_results` with this tick's tuple (patches.py:243-245) | **yes**. The tuple order is the merge order |
| 29 | `property_updates` :732 | Dict[str,Any] | Dict LWW per key (:802) | cooperation/phase.py:209-211; progression/phase.py:85; information/phase.py:76,108; world_emergence/phase.py:122; combat_engagement/phase.py:454; movement.py:388; pipeline_phases/movement.py:455; evolution.py:133-146; intelligence.py:699,1000 | `identity.properties.update` (patches.py:239-241). The compactor prunes unchanged keys (compactor.py:101-115) | **yes**. LWW per key |
| 30 | `pending_action_intent` :739 | Optional[ActionIntent] | LWW (:801) | information/phase.py:108 (information_belief); information_intent_execution.py:58 | **Not applied.** There is no patch in extract_patches (patches.py:771-836). It is transient, read by information_intent_execution | yes-transient. LWW, never durable |

EntityUpdate tally: 30 fields. 23 are order-sensitive (#2,3,6,7,8,9,11-15,17-23,25-29). One is weak, float only (#5). Four are not order-sensitive (#1,4,10,16). Two are latent or transient (#24 has no writer; #30 is never applied).

### Nested-type notes (not repeated above)

- `CombatUpdate.is_noop` (updates.py:133-137) leaves out `equipment_upd`, `attacker_equipment_upd`, `wound_update`, `social_upd`, `strategic_upd`, `trace`, `hit_tick_set`, `outcome_kind`, `is_lethal`, `is_opportunity_attack` and `failure_reason`. A CombatUpdate carrying only those fields is therefore:
  1. returned unchanged by `CombatUpdate.merge` (updates.py:141-142);
  2. nulled by the compactor (compactor.py:131-136);
  3. counted as no-op by `EntityUpdate.is_noop` (updates.py:754), so `StateUpdate.compact` (updates.py:1300-1308) and `EntityUpdate.merge` (updates.py:768) drop the whole EntityUpdate.
- `InventoryUpdate.merge` (update_models/inventory.py:19-26) has no noop short-circuit. `BuildingUpdate.merge` (update_models/buildings.py:24-42) merges an inventory only when both sides have one.
- `QuestUpdate.is_noop` for a named quest is always False (update_models/quests.py:68: `not bool(self.quest_id) and ...`).
- `ResourceTransferIntent` contingent `*_upd` fields are applied only through conservation results on acceptance (core/conservation.py:165-268, 460-466).

## 2. StateUpdate fields (53) and nested world/group types

Merge rules are in `merge_many` (updates.py:1112-1298) unless noted. "set→list" means a Python `set` is converted back with `list(...)`, so the resulting order is the set's iteration order.

| # | Field (line) | Type | Merge rule | Refine writers (file:line; phase) | Apply consumption | Order-sensitive? |
|---|---|---|---|---|---|---|
| 1 | `entity_updates` :1021 | Dict[int,EntityUpdate] | Per-id `EntityUpdate.merge` (:1178-1179). Most rewrite steps rebuild it (`refined_entity_updates = dict(...)`) | nearly every step (see §1) | Per entity: passive pre-pass, then patches (apply_plan.py:361-393; apply.py:103-239) | **yes**. Via §1 |
| 2 | `entities_add` :1022 | List[EntityState] | Extend (:1201) | world/camp.py:117, boss.py:188,286, calamity.py:50,68, creature_territory.py:76, reproduction_humanoid.py:103, world_dynamics.py:255 (all world_dynamics) | Inserted after the replacements. A duplicate id raises `DuplicateEntityIdError` (apply.py:69-78, 321-325). `next_entity_id` is moved past the adds (apply.py:81-91) | no. A collision is fatal, not resolved by order |
| 3 | `entity_spawn_sources` :1023 | Dict[int,SpawnSource] | Union. Two different sources for one id raise ValueError (:1005-1012, :1259) | reproduction_humanoid.py:104 (world_dynamics) | Not read by apply. Read by observability/run_ledger.py:234 | no |
| 4 | `entities_remove` :1024 | List[int] | set→list (:1134, :1202, :1260) | **none in src/** | Popped *before* `entities_to_replace` is written back (apply.py:282-297). An id that is also in the plan (any passive change on a bio/life-due tick, apply_plan.py:362-364) is **re-inserted** | latent. Remove-then-resurrect hazard |
| 5 | `nodes_add` :1025 | List[ResourceNodeState] | Extend (:1203) | world/ecology.py:147 (world_dynamics) | Applied after node_updates, overwriting by id (apply_plan.py:256-257). Invalidates the grid (:225) | **yes**. LWW by id |
| 6 | `node_updates` :1026 | Dict[int,ResourceNodeUpdate] (:806-819) | Per id: `charges_delta` sum, `cooldown_set` LWW | interaction.py:214; economy.py:262; world_dynamics.py:336; ecology.py:147. trust_boundary sets it to `{}` | Charges unclamped. A cooldown set wins. Updates to unknown ids are dropped (apply_plan.py:233-255) | **yes**. Cooldown LWW |
| 7 | `ground_items_add_or_update` :1027 | List | Extend | world_dynamics.py:336 | Removes run first, then adds by id LWW (apply_plan.py:295-300) | **yes**. LWW by id |
| 8 | `ground_items_remove` :1028 | List[int] | set→list | economy.py:262. trust_boundary sets it to `[]` | Popped (apply_plan.py:297-298) | no |
| 9 | `item_instances_add_or_update` :1029 | List[ItemInstance] | Extend (:1206) | **none** | By id LWW (apply.py:306-308) | latent |
| 10 | `item_instance_updates` :1030 | Dict[int,ItemInstanceUpdate] (update_models/inventory.py:32-50) | **Plain overwrite LWW** per id (:1229-1230). The contract is documented at inventory.py:37-44 | **none** | Appends the owner to history (apply.py:309-316) | latent. LWW drops transfers |
| 11 | `corpses_add_or_update` :1031 | List | Extend | economy.py:262 | Decay, then removes, then adds by id LWW (apply_plan.py:303-315). Plus death bodies (apply.py:299-304) | **yes**. LWW by id |
| 12 | `corpses_remove` :1032 | List[int] | set→list | economy.py:262; world_dynamics.py:336. trust sets it to `[]` | Popped | no |
| 13 | `owed_add_or_update` :1033 | List[OwedRecord] | Extend | economy.py:262 | `fold_owed`: removals, then adds by id LWW (core/models/world_records.py:62-69; apply.py:367) | **yes**. LWW by id |
| 14 | `owed_remove` :1034 | List[str] | set→`sorted` (:1268) | town_resolution.py:156 | as #13 | no |
| 15 | `scars_add_or_update` :1035 | List[LocalScarState] | Extend | **none** | Adds **then** removes. This is the reverse of ground items and corpses (apply_plan.py:328-334) | latent |
| 16 | `scars_remove` :1036 | List[int] | set→list | **none** | as #15 | latent |
| 17 | `chest_updates` :1037 | Dict[int,ChestUpdate] (:902-915) | Per id: sets LWW | interaction.py:214; economy.py:262; world_dynamics.py:336. trust sets it to `{}` | Applied before `chest_add_or_update` (apply_plan.py:265-272) | **yes**. LWW |
| 18 | `chest_add_or_update` :1038 | List[ChestState] | Extend | **none** | Whole replace after the chest updates (apply_plan.py:271-272) | latent |
| 19 | `building_updates` :1039 | Dict[int,BuildingUpdate] (update_models/buildings.py:11-42) | `hp_delta`/`maintenance_shifts_done_delta` sum. `functional_set`/`price_modifiers_set`/`maintenance_shifts_done_set` LWW. Inventories merged | sabotage.py:71 (building_sabotage); town_resolution.py:156; economy.py:262. trust sets it to `{}` | `_building_after`: hp clamp [0,max], set-then-delta for shifts, hp=0 forces non-functional (apply_plan.py:103-117). A violent destruction adds +2 trauma (apply_plan.py:284-291) | **yes**. LWW on sets |
| 20 | `camp_updates` :1040 | Dict[str,CampUpdate] (:917-938) | Deltas sum. Sets LWW | world/camp.py:117-141; world_dynamics.py:255 | Unclamped add. Sets LWW (apply_plan.py:337-351) | **yes**. LWW on sets |
| 21 | `world_updates` :1041 | Dict[str,WorldUpdate] (:844-899) | Sets LWW. Deltas sum. `modifiers_add/remove` sorted-set union. `siege_state_clear` OR | world_dynamics.py:128,181,219-221,272-274 (**mutated in place**, see §3); camp.py; boss.py:310; calamity.py:107,171; reproduction_humanoid.py:103; influence.py:71; cohort.py:428; world_emergence/phase.py:134; military_conflict.py:217,352; lifecycle.py:324 | `trauma_score_set` **replaces** `trauma_delta`, and so does the retaliation pair. Influence unclamped. Owner sentinel −1 decoded. Modifiers `(old−remove)+add`. Births added on top of cohorts. `service_availability` clamped [0,1]. Siege: clear > set > keep, then a clamped progress delta (apply_plan.py:174-221). Plus `process_recovery` first (apply_plan.py:166-172) | **yes**. LWW, and a set masks deltas from every step |
| 22 | `resource_updates` :1042 | Dict[str,float] | Float sum (:1194-1195) | economy.py:262 (treasury); town_resolution.py:156; world_dynamics.py:336 | Added into `global_resources` (apply.py:363-365) | weak. Float only |
| 23 | `home_storage_updates` :1043 | Dict[int,InventoryUpdate] | Per-id `InventoryUpdate.merge` (concat) | economy.py:262 | `InventoryService.apply_update` with capacity (apply_plan.py:317-325) | **yes**. Capacity checked in list order |
| 24 | `groups_add_or_update` :1044 | List[GroupRecord] | Concat (group_update_merge.py:18) | pipeline_phases/groups.py:230; world_systems/groups.py:308 (groups) | After removes, by id LWW (apply_plan.py:159-162) | **yes**. LWW by id |
| 25 | `groups_add` :1045 | List[GroupRecord] | Concat. Never merged by id (group_update_merge.py:10,19) | military_conflict.py:341,356 (hashed id `stable_int31`, :340); groups.py:230 and world_systems/groups.py:308 (sequential from `state.next_group_id`, groups.py:36-41) | `resolve_group_adds`: the **first** add of an id wins and later adds are rejected and counted, with their members' `group_id_set` nulled (apply_plan.py:55-87) | **yes**. First wins |
| 26 | `next_group_id_set` :1046 | Optional[int] | **max** (group_update_merge.py:20-21) | groups.py:230; world_systems/groups.py:312 | `max(prior, set)`, never lowered (apply.py:90) | no |
| 27 | `groups_remove` :1047 | List[int] | set→list | groups.py:230 | Removes run before adds, so a same-tick re-add survives (apply_plan.py:159-162) | no |
| 28 | `maturity_set` :1048 | Optional[int] | LWW (:1233) | calamity.py:33; world_dynamics.py:255 | apply.py:359 | **yes**. LWW |
| 29 | `last_calamity_tick_set` :1049 | Optional[int] | LWW | calamity.py:50; world_dynamics.py:255 | apply.py:360 | **yes**. LWW |
| 30 | `grief_drained_tick_set` :1050 | Optional[int] | LWW | kernel.py:607,703 only, not a refine step | apply.py:361 | yes, but there is a single writer |
| 31 | `rng_checkpoint` :1051 | Any | LWW if truthy (:1239) | kernel.py:753 only | apply.py:362 | yes, single writer |
| 32 | `transaction_trace` :1052 | List[str] | Extend | economy.py:262 | Kept only in `audit_mode` (apply.py:347-351) | yes. Diagnostic order |
| 33 | `rejections_delta` :1053 | Dict[str,int] | Int sum (:1192-1193) | ~16 sites: trust, actor_validity, actions.py:239-294, movement.py:299, interaction.py:94,139, sabotage.py:49,58, economy.py:164,243, lodging.py:189,378, occupancy.py:161, capacity_enforcement.py:170; plus `resolve_group_adds` (apply_plan.py:85-86) | Summed into `rejection_registry` (apply.py:343-345) | no |
| 34 | `pressure_signals_set` :1054 | Optional[Dict] | LWW | **none** | apply.py:356 | latent |
| 35 | `current_mode_set` :1055 | Optional[RuntimeMode] | LWW | kernel.py:607 only | apply.py:357 | single writer |
| 36 | `current_policy_set` :1056 | Optional[GovernorPolicy] | LWW | kernel.py:611 only | **Not consumed by apply.** Read in refine by the compactor (compactor.py:49), movement (pipeline_phases/movement.py:206) and intelligence (intelligence.py:354,891,962) | no. Read-only input |
| 37 | `rejection_events` :1057 | List[RejectionEvent] | Extend | trust, actor_validity, actions.py, interaction.py:145, shop.py:86, economy.py:262, lodging.py:177-189, occupancy.py:161 | **Not consumed by `apply_generation`.** No reference in apply.py | yes. Diagnostic order only |
| 38 | `processed_transaction_ids` :1058 | List[str] | **set→list** (:1148, :1215, :1274). economy also emits `list(set ∪ set)` (economy.py:275) | economy.py:275 (resource_transactions, and again inside lifecycle) | `prior + update` with **no dedup across ticks** (apply.py:353-354) | **yes. Nondeterministic**: the order of a `set[str]` depends on PYTHONHASHSEED, and it is persisted into durable state |
| 39 | `next_node_id_set` :1059 | Optional[int] | **LWW** (:1236), not max | ecology.py:147 | apply.py:88 | **yes**. LWW could lower it. The group counter uses max |
| 40 | `next_entity_id_set` :1060 | Optional[int] | LWW (:1237) | world_dynamics.py:255 | Then bumped past `entities_add` (apply.py:89-91) | yes in principle. Self-healed by the bump |
| 41 | `next_item_instance_id_set` :1061 | Optional[int] | LWW (:1238) | **none** (only documented at core/inventory.py:240) | apply.py:92 | latent |
| 42 | `dirty_set` :1062 | Optional[DirtySet] | `DirtySet.merge` set unions (core/dirty.py:416-424). Rebuilt by `DirtySetBuilder` and replaced at pipeline.py:327-329, 356-357, 374-375, 389-390, 443-459 | pipeline only | Movement-cache invalidation (apply.py:382-385; apply_plan.py:136-137). `validate_dirty_set` in audit (apply.py:607-608). Not durable | no. Set union |
| 43 | `force_full_scan` :1063 | bool | **Not merged at all**: `merge_many` leaves it out and keeps `self`'s value | pipeline.py:49-52 | Read at pipeline.py:445 to widen dirty_set. Not durable | latent. `X.merge(u)` with a fresh `X` would lose it |
| 44 | `sub_phase_costs` :1064 | Dict[str,float] | Float sum (:1244-1246) | movement.py:299 | **Overwritten** wholesale by refine's `costs` (pipeline.py:467). Not durable | no. Telemetry |
| 45 | `metric_counters` :1065 | Dict[str,int] | Int sum (:1196-1198). Also a closure dict in refine that wins at the end (pipeline.py:98-101, 465-467) | cooperation/phase.py:270-272 (stores **wall-clock ms float**); world_emergence/phase.py:134; town_resolution.py:156; movement.py:299; intelligence.py:868 | Not durable | no. Telemetry, but it is non-deterministic data carried in the update |
| 46 | `world_events_add` :1066 | List[WorldEvent] | Extend (:1217) | actions.py:239-357; world_dynamics.py:185,336; ecology.py:147; world_emergence/services.py:301; cohort.py:428; military_conflict.py:352; economy.py:262; quest_opportunity_rewards.py:117; lifecycle.py:324; economy/vacancy.py:76; information_propagation and diplomatic_transitions (pipeline.py:251,282) | Appended, keep the last 500 (apply.py:389-392) | **yes**. Window order and truncation |
| 47 | `quest_registry_add` :1067 | List | Extend | world_emergence/phase.py:134 | **First** wins (`if opp.id not in`) (apply.py:395-397) | **yes**. First wins |
| 48 | `quest_registry_remove` :1068 | List[str] | Extend, no dedup | quest_opportunity_rewards.py:43,127; world_emergence/services.py:301 | Applied after add, so add+remove in one tick removes (apply.py:398-399) | no |
| 49 | `quest_status_updates` :1069 | Dict | dict.update LWW (:1220) | **none** | Applied after remove (apply.py:400-403) | latent |
| 50 | `quest_opportunity_reward_intents` :1070 | List | Extend | **none** | Not in apply. Read in refine at quest_opportunity_rewards.py:60 | latent |
| 51 | `information_providers_update` :1071 | Dict[int,InformationProviderState] | dict.update, **whole-object LWW** (:1222) | quests.py:246 (quest_rewards); lead_contradiction.py:295 | dict.update (apply.py:499-500) | **yes**. Whole replace |
| 52 | `faction_updates` :1074 | List[FactionUpdate] (:953-982) | Extend, filtered by `is_noop` (:1223-1225). No per-faction merge | military_conflict.py:352; FactionAwarenessService (pipeline.py:241); diplomatic (pipeline.py:282); FactionSentimentService (pipeline.py:434-438) | Sequential per record against the running `new_factions` (apply.py:406-474). Each record clamps `tension` [0,1] (:466), sentiment [-1,1] and familiarity [0,1] (:432-443), and pairwise [0,1] (:462-464). Within one record the decay set comes after the deltas (:448-453). Territory is set algebra. Relations dict LWW | **yes**. A clamp per record makes the sum order-dependent. Decay records come last (pipeline.py:434-435) and overwrite same-tick sentiment deltas on stale pairs (sentiment.py:102-123) |
| 53 | `clan_updates` :1076 | List[ClanUpdate] (:985-1002) | Extend, filtered by noop (:1226-1228) | groups.py:230; clan_lifecycle.py:93 | Sequential per record: membership `(old∪add)−remove`, leader/dissolved LWW, reputation clamped [0,2] per record (apply.py:477-493) | **yes**. Clamp per record, LWW on leader |

StateUpdate tally: 53 fields.

- **Order-sensitive (28):** #1, 5, 6, 7, 11, 13, 17, 19, 20, 21, 23, 24, 25, 28, 29, 30, 31, 32, 35, 37, 38, 39, 40, 46, 47, 51, 52, 53. Five of these (#30, 31, 35 have a single writer; #32, 37 are diagnostic) count only formally.
- **Weak, float only (1):** #22.
- **Not order-sensitive (13):** #2, 3, 8, 12, 14, 26, 27, 33, 36, 42, 44, 45, 48.
- **Latent (11):** #4, 9, 10, 15, 16, 18, 34, 41, 49, 50 have no refine writer today. #43 is latent because its merge drops the flag.

Counting strictly for durable state, excluding the diagnostic and single-writer fields: 23 order-sensitive StateUpdate fields.

## 3. Hidden mutations during refine (writes that bypass the StateUpdate)

### Tick-start `state`, or objects it shares by reference

- **Cooperation timeline.** `entity.timeline.append(...)` at src/domains/cooperation/phase.py:38, 47, 57 and 116.
  - The timeline `deque(maxlen=200)` is carried by reference into the next tick's EntityState (apply.py:789-793), so this durable history lives entirely outside the update.
  - It is gated only by `len(timeline) < 150` (phase.py:110, 158).
  - SHADOW mode cannot discard it, because run_phase only reverts update fields (pipeline.py:121-129).
  - observability/entity_timeline.py:77 also appends. Whether that runs inside refine is UNVERIFIED.
- **Movement claims.** `object.__setattr__(state, "_occupancy_map_cache", live_occ_map)` and `object.__setattr__(state, "transient_claims", live_claims)` at src/engine/pipeline_phases/movement.py:203-204 and :294-295.
  - Tick-start occupancy is overwritten with the post-move map.
  - Later steps that call `SpatialQueryService.get_occupancy_map(state)` therefore read the in-flight movement result through state, not through the update. This affects occupancy_resolution and lodging, though which callers are actually hit is UNVERIFIED per call site.
  - `transient_claims` is read by legality.py:121.
- **Occupancy snapshot.** `object.__setattr__(state, "occupancy_snapshot", ...)` at pipeline.py:65.
- **Movement cache, invalidated in place.** `state.movement_cache.invalidate_for_dirty(built_dirty)` at pipeline.py:331 (cache body: engine/movement_cache.py:110-122).
  - Plans are looked up and stored through `m_cache` in engine/movement.py:166-180.
  - The cache object is carried into the next state (apply.py:382-385, 544).
- **Route plans.** `object.__setattr__(state, "route_plans", RoutePlanStore())` at engine/route_search.py:149.
  - `store.paths[...] = ...` and the counters `plan_hits`, `searches`, `nodes_expanded`, `fallbacks` and `detours` are mutated, along with `store.prune(tick)`, at route_search.py:159-180.
  - The store is carried by reference into the next state (apply.py:545).
  - It is reached from MovementSystem (engine/movement.py:19). The exact steps are UNVERIFIED: movement_routing and probably action_routing.
- **Strategic cache flag.** `object.__setattr__(state, "_has_hostiles_or_dead_cache", ...)` at systems/strategic_systems/intelligence.py:347. Apply may carry it forward (apply.py:374-376, 542).
- **Lazy memo caches on state.** These are benign if pure, but they are still state writes:
  - spatial_query.py:121, 148, 157, 166, 215, 239, 253;
  - world_index.py:111 (`_index_hits` counter), :133-134 (`world_indexes`, `_index_misses`), carried forward at apply.py:546-549;
  - semantic_entity_index.py:135;
  - region_resolution.py:42;
  - engine/domain/view.py:49, 69;
  - world/environment.py:87.
- **Action-routing sliding state.** `sliding_state = replace(state, entities=working_entities)` (pipeline_phases/actions.py:204), then `object.__setattr__(sliding_state, ...)` (:344-348).
  - The proxy itself is a copy.
  - It still shares `movement_cache`, `route_plans` and `world_indexes` with tick-start `state` by reference, because the `apply.replace` copy (apply.py:9-27) copies field references and nulls only `*_cache` names.

### In-flight StateUpdate objects mutated in place (frozen dataclass, mutable dict)

- **world_dynamics.**
  - `update.world_updates[...] = ...` at engine/world_dynamics.py:128, 181, 219-221 and 272-274. The `world_updates` dict is the one shared with the incoming update. It is not copied until :312.
  - `update.entity_updates[eid] = ...` at :196. This one writes into the phase's own copy, made at :109.
- **evolution.** `update.entity_updates[e_id] = replace(...)` at engine/evolution.py:133, assigned while iterating the incoming `update.entity_updates` (:26). The previous step's returned object is mutated.
- **Consequences.** Both phases currently run without a feature flag, so SHADOW cannot apply to them. Even so, any rollback or diff that relies on "phase input is unchanged" is broken.

### Data computed outside `run_phase`, from the pre-step update or tick-start state

These are not hidden writes, but they are inputs the contract should name:

- `FactionDecisionPhase.execute` (pipeline.py:231);
- `_diplo_*` (pipeline.py:261-278);
- `_sentiment_updates` (pipeline.py:434-435);
- `EntityGenerator.for_state(state, update)` (pipeline.py:342).

### Generator spawn tiles

`EntityGenerator._claimed_tiles` (systems/world_systems/generator.py:80, 106-115) is per-instance state, not world state. There is only one generator per tick (pipeline.py:342).

## 4. Contention points

- **JOIN_PARTY acceptance.** src/domains/cooperation/phase.py:174-196.
  - The acceptor reads `offerer.strategic.contracts[contract_id]` from **tick-start** state (:177-180).
  - It promotes the contract via `ContractService.accept_contract` and merges a StrategicUpdate into the **offerer's** EntityUpdate (:190-196).
  - There is no in-phase reservation. Entities are walked in `state.entities` order (:105). If several acceptors touch the same offerer, they produce several `contracts_add_or_update` entries, which collapse at apply by contract id, last entry wins (patches.py:459-467, 486).
  - Whether one contract can be accepted by two entities depends on `find_pending_incoming_offer` addressing (:130). That is UNVERIFIED.
  - Group formation itself happens later, in `groups` (pipeline.py:411).
  - `new_groups_add` at :214 is assigned but never used.
- **Resource reservations.** engine/economy.py:49-51 (`reservations`), :53-54 (`in_tick_processed_ids`), :57 (`for e_id in sorted(...)`).
  - The lowest entity id wins a contested node, ground item or corpse (`_apply_world_effects` :347-386).
  - The same loop runs a second time inside the lifecycle step (pipeline.py:570-578), with a fresh `reservations` dict.
- **Action-routing sliding order.** pipeline_phases/actions.py:198-201 pre-applies the whole incoming update to `working_entities`. :203 walks actors in sorted eid order, and :340-348 applies each actor's effects before the next actor runs.
  - A lower-id attacker resolves first.
  - The defender's `CombatUpdate.attacker_id` is LWW (updates.py:146), so the highest-id hitter is recorded as the killer and `last_attacker_id` holder.
  - `outcome_kind` precedence is described at updates.py:150-151.
- **Movement claims.**
  - `live_claims` and `live_occ_map` are built from earlier `new_position` writes (pipeline_phases/movement.py:184-204) and extended per mover (:280-295).
  - The candidate budget is `MovementCandidateSelector.select(... budget=policy.movement_budget)` (:207-211).
  - Position swaps run first (pipeline.py:299).
  - Final arbitration happens in `occupancy_resolution` (pipeline_phases/occupancy.py:151-161), after `place_leavers` (lodging.py).
- **Lodging beds.** `grant_beds` runs before resource_transactions (pipeline.py:372; lodging.py:177-189). Bed capacity is contended, and the ordering rule is UNVERIFIED.
- **Spawn-id allocation.** systems/world_systems/generator.py:83-96 (`for_state`: the taken id is `max(next_entity_id−1, live ids, update.next_entity_id_set−1, update.entities_add ids)`) and :116-118 (`get_next_id`).
  - The generator is built once, after town_resolution (pipeline.py:342), and handed only to world_dynamics (pipeline.py:343).
  - All current `entities_add` producers sit under world_dynamics (see §2 #2).
  - Any future spawner in a later step that does not reuse this generator could collide. A collision raises `DuplicateEntityIdError` at apply (apply.py:73-78).
  - `next_entity_id_set` is LWW (updates.py:1237) but healed by apply.py:81-91.
- **Group-id allocation.** There are two schemes:
  - sequential `state.next_group_id` (world_systems/groups.py:36-41, 312);
  - hashed `stable_int31(region, attacker, tick)` (military_conflict.py:340-341).
  - On collision, `resolve_group_adds` keeps the first add in list order (apply_plan.py:55-87). military_conflict (pipeline.py:292) runs before groups (pipeline.py:411), so the hashed squad wins.
- **Node charges.** `charges_delta` is summed across steps (updates.py:817) and applied unclamped (apply_plan.py:239). The only over-harvest guard is economy's reservations.
- **Faction sentiment.** `derive_from_bond_updates` (sentiment.py:47-99) is followed in the same list by `decay_stale_sentiments` (sentiment.py:102-123). The decay is computed from tick-start `last_interaction_tick`, and apply processes the records in order (apply.py:427-453). So a same-tick interaction on a stale pair is overwritten by the absolute decay value. This is static only; runtime is UNVERIFIED.
- **Quest registry.** A duplicate `quest_registry_add` is resolved first-wins (apply.py:395-397). A same-tick add plus remove means removed (:398-399).

## 5. Surprises worth carrying into the spec

1. **Payload-only CombatUpdates vanish.** `CombatUpdate.is_noop` ignores every nested and flag field (updates.py:133-137). A CombatUpdate carrying only `wound_update`, `social_upd`, `equipment_upd`, `outcome_kind` or `hit_tick_set` is dropped by `CombatUpdate.merge` (:141-142), by the compactor (compactor.py:131-136), and through `EntityUpdate.is_noop` (:754). CombatPatch never applies those fields anyway (patches.py:322-348), so they only work when the producer unpacks them, which combat_actions.py:70-108 does.
2. **SocialUpdate merges inconsistently.** `familiarity_delta`, `debt_delta`, `fear_delta`, `salience_delta` and `rejection_increment` merge LWW per key, not by sum (updates.py:373-384), while `trust_delta` and `grudge_delta` sum. Two same-tick familiarity gains for one target keep only the last.
3. **`process_update` wipes rejection counts.** It rebuilds `rejection_count` from only the keys in this update (relationships.py:133). Every other key's history is lost on any social update.
4. **`processed_transaction_ids` is persisted in hash order.** It is round-tripped through `set` (updates.py:1148, 1274; economy.py:275) and then appended to durable state (apply.py:353-354). The order depends on PYTHONHASHSEED, and the list grows without bound.
5. **`force_full_scan` is not merged by `merge_many`.** `next_node_id_set` is LWW while `next_group_id_set` is max.
6. **Remove-then-resurrect.** `entities_remove` is popped before plan replacements are written back, so a removed entity with passive changes is re-inserted (apply.py:282-297). It is latent today because there are no producers.
7. **Set fields mask deltas from every step.** `WorldUpdate.trauma_score_set` / `retaliation_pressure_set` (apply_plan.py:181-182) and `BiologicalUpdate.*_set` (patches.py:129-130) silently discard deltas contributed by any step.
8. **In-place mutation of the incoming update.** world_dynamics (`world_updates`) and evolution (`entity_updates`) do this. Cooperation's timeline and movement's occupancy/claims writes go straight to tick-start state.
9. **Ten StateUpdate fields and one EntityUpdate field have no refine writer.** They are `entities_remove`, scar add/remove, `chest_add_or_update`, both item-instance fields, `quest_status_updates`, `quest_opportunity_reward_intents`, `pressure_signals_set`, `next_item_instance_id_set`, and `status_effect_update`.

### Method and limits

- Writers were found by an AST scan of keyword arguments in `EntityUpdate(...)`, `StateUpdate(...)` and `replace(...)` calls under the exported origin/main `src/`. Files were mapped to steps through a one-hop import closure from each step's module, with zero-writer fields cross-checked by `git grep`.
- Writers reached only through deeper call chains are attributed by import path and marked "via". This covers `engine/domain/*_actions.py` and `tactical*.py`, reached through `pipeline_phases/actions.py` and `domain_logic` / `engine/domain/cognition.py`.
- Writers that build the incoming worker update rather than a refine step (`tactical*.py`, `kernel.py`, `executor.py`, `worker_logic.py`) are Collection-phase producers. Their in-refine reachability is UNVERIFIED.
- Nothing was executed.
