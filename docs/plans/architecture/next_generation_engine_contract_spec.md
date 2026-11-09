---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, engine, determinism, planning]
---

# Contract spec (DRAFT): phases, merge rules and state hygiene for the next-generation engine

The spec for `TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC`, child 4 of `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`. Written by
architecture-planner-u24, 2026-11-09.

- **Status: DRAFT 1.** The owner dispatched it now (#715 6743047506). The ADR it implements is
  `docs/architecture/next_generation_engine_adr.md` (accepted, #715 6742854335).
- **Inputs it does not have yet:**
  - child 2's access-audit report, which confirms or corrects §3 and §5 at runtime;
  - stage 0's re-measure.
  Everything marked **[S]** below is static only, and §10 lists what the audit must settle.
- **Evidence:** `next_generation_engine_merge_inventory.md`, a field-by-field static read of `main` `1fb40ac76`. Rows are cited as
  **E#** (EntityUpdate field) and **S#** (StateUpdate field) from its §1 and §2.
- **No code, no runs, no Level B change.** Where today's behaviour looks wrong, §9 hands it to its owner as a finding. The contract
  reproduces it exactly.

## 1. The contract in four layers

The four layers are from the ADR, Decision 5.

| Layer | Contract | Today (what changes) |
|---|---|---|
| 1. tick-start state | `AuthoritativeState` as the tick began. **Nothing writes to it during refine.** | Writes do happen today: §5 lists them |
| 2. step view | tick-start state plus the **declared** earlier deltas. The kernel builds it. A step that declares `sliding` reads the deltas as they accumulate, unit by unit, in its declared order | Every step today sees the whole `StateUpdate` so far (`pipeline.py:103-135`) |
| 3. compute | `compute(view, unit) -> Delta`. It writes nothing outside its delta and raises `UndeclaredAccessError` on an undeclared read (modelled on `PacketFieldMissingError`, `src/core/worker_protocol.py:15`) | Steps return `replace(u, …)` or `u.merge(X)` (inventory §0) |
| 4. merge and commit | The kernel folds deltas with the §2 rules in commit-key order, then runs today's validate and single-writer apply unchanged | `merge_many` (`updates.py:1112-1298`), then `ApplyPath.apply_generation` |

### 1.1 The step declaration

Every step registered with the kernel carries:

```
StepDecl(
  name,                       # today's run_phase name, e.g. "strategic_intelligence"
  ordinal,                    # its position in today's refine order (the commit key's first part)
  feature_flag,               # today's flag, or None
  unit,                       # "world" | "entity" | "group" | "region" | "resource"
  unit_order,                 # how units are ordered: "ascending_id" | "state_entities" | "candidate_list" | "declared"
  reads_state,                # tick-start fields read (paths, e.g. "entities.*.strategic")
  reads_deltas,               # earlier delta fields read, each with the step ordinals it may come from
  sliding,                    # True if unit k reads the deltas of units < k in this step
  writes,                     # delta fields produced, each with its own-entity / cross-entity scope
  owned_stores,               # kernel- or phase-owned stores it may use (§5), never state
)
```

The access audit (child 2) checks `reads_state`, `reads_deltas` and `writes` against what the step does. The `writes` check is
runtime. Reads are static in v1 (audit plan §5).

### 1.2 The delta

A delta is today's `EntityUpdate` / `StateUpdate` shape, restricted to the step's declared `writes`. **No new update types at Level
A.** The one structural change is §3.3: the whole-object bundles become sub-field deltas. That change needs its own Level A proof.

## 2. Commit key and merge classes

**Commit key** = `(step ordinal, unit position, emission index)`:
- **step ordinal:** today's `run_phase` order in `refine`.
- **unit position:** today's iteration order inside the step, declared per step. Examples: ascending id (economy, `economy.py:57`;
  action_routing, `actions.py:203`), `state.entities` order (cooperation, `cooperation/phase.py:105`), the candidate list
  (strategic, §8).
- **emission index:** the order the unit produced its records in.

For a serial executor, the commit key **is** today's order, so every rule below reproduces today's result by construction. For any
other executor, the kernel sorts by the key before folding.

Every field is in exactly one class:

| Class | Rule | Level A argument | Proof |
|---|---|---|---|
| **C**, commutative | any order | the merge is order-free (OR, integer sum with one later cap, set union, max) | a permuted-order unit test |
| **O**, ordered | fold in commit-key order with today's merge function | it is today's order and today's function | the serial executor's equivalence test, field-by-field compare |
| **F**, first wins | the first record in commit-key order wins; later ones are rejected and counted, as today | today's apply rule | contention scenario test |
| **K**, kernel-owned | not produced by any refine step; written by the kernel only | single writer | — |
| **T**, telemetry | not durable; excluded from the state compare; merged as today | outside state | — |
| **L**, latent | no refine writer today; a new writer must declare a class first | — | a declaration-coverage test fails on an undeclared writer |

**Float sums are O, never C.** Re-association changes the low bits (E5 `readiness_delta`, S22 `resource_updates`). They become C only
through a versioned change to integers or fixed point, which is Level B.

## 3. Merge rule for every field

### 3.1 EntityUpdate (30 fields)

| Class | Fields (inventory row) |
|---|---|
| key | E1 `entity_id` |
| **C** | E4 `moved_this_tick` (OR); E10 `attributes` (integer sum, one cap); E16 `reward` (sum) |
| **O** | E2 `kind_set`; E3 `new_position`; E5 `readiness_delta` (float); E6 `active`; E7 `interaction`; E8 `resource_transfers` (list order decides reservations and clamps); E9 `identity`; E11 `inventory` (capacity in list order); E12 `strategic` (last occurrence per id wins; `pipeline.py:395-401` depends on it); E13 `biological` (a set masks deltas); E14 `social` (mixed sum and per-key LWW, §9 F2); E15 `quest`; E17 `lifecycle`; E18 `combat` (attacker pair LWW, outcome precedence, the `is_noop` short-circuit, §9 F1); E19 `equipment`; E20 `navigation`; E21 `task` (action_routing replaces it whole); E22 `stamina_update`; E23 `wound_update`; E25 `group_id_set`; E28 `intent_results` (tuple order); E29 `property_updates` (per-key LWW) |
| **O, split** (§3.3) | E26 `self_model_bundle_set`; E27 `cognition_bundle_set` |
| transient | E30 `pending_action_intent`: never applied (no patch); it is a delta read by `information_intent_execution`. Ordered, excluded from the state compare |
| **L** | E24 `status_effect_update` |

### 3.2 StateUpdate (53 fields)

| Class | Fields (inventory row) |
|---|---|
| **O** | S1 `entity_updates` (per entity, §3.1); S5 `nodes_add`; S6 `node_updates`; S7 `ground_items_add_or_update`; S11 `corpses_add_or_update`; S13 `owed_add_or_update`; S17 `chest_updates`; S19 `building_updates`; S20 `camp_updates`; S21 `world_updates` (a set masks deltas from every step); S22 `resource_updates` (float); S23 `home_storage_updates`; S24 `groups_add_or_update`; S28 `maturity_set`; S29 `last_calamity_tick_set`; S39 `next_node_id_set` (LWW, §9 F5); S40 `next_entity_id_set` (healed by apply); S46 `world_events_add` (window order and truncation); S51 `information_providers_update` (whole-object replace); S52 `faction_updates` (a clamp per record); S53 `clan_updates` (a clamp per record) |
| **F** | S25 `groups_add` (`resolve_group_adds`, `apply_plan.py:55-87`); S47 `quest_registry_add` (`apply.py:395-397`) |
| **C** | S2 `entities_add` (a collision is fatal); S3 `entity_spawn_sources`; S8 `ground_items_remove`; S12 `corpses_remove`; S14 `owed_remove`; S26 `next_group_id_set` (max); S27 `groups_remove`; S33 `rejections_delta`; S42 `dirty_set`; S48 `quest_registry_remove` |
| **O, hash-seed order** | S38 `processed_transaction_ids`: round-trips through `set[str]` (`updates.py:1148`, `:1274`; `economy.py:275`), so its persisted order follows `PYTHONHASHSEED` [rechecked]. It is unhashed and only tested for membership, so behaviour does not depend on the order. **The state compare must treat it as a multiset.** Sorting it is §9 F4 |
| **K** | S30 `grief_drained_tick_set`; S31 `rng_checkpoint`; S35 `current_mode_set`; S36 `current_policy_set` (a read-only input to refine) |
| **T** | S32 `transaction_trace`; S37 `rejection_events`; S44 `sub_phase_costs`; S45 `metric_counters` (carries wall-clock ms from cooperation, `cooperation/phase.py:270-272`) |
| **L** | S4 `entities_remove` (§9 F6); S9, S10 item instances; S15, S16 scars; S18 `chest_add_or_update`; S34 `pressure_signals_set`; S41 `next_item_instance_id_set`; S49 `quest_status_updates`; S50 `quest_opportunity_reward_intents` |
| special | S43 `force_full_scan`: `merge_many` drops it (§9 F5). It becomes a kernel-owned per-tick flag, read only at `pipeline.py:445` |

### 3.3 Splitting the whole-object bundles

`cognition_bundle_set` (E27) is written by nine steps (inventory E27). Each one reads the current bundle through
`core/cognition_write.py`, then replaces the whole object.
- **Rule:** each writer emits sub-field deltas (memory, habit, role model, self model, combat memory, and so on). The kernel applies
  them in commit-key order onto the tick-start bundle.
- **Level A holds only if every writer reads through.** If one writer starts from tick-start state instead of the running bundle, a
  whole replace drops earlier writers' changes today, and a sub-field merge would keep them. That is a Level B change.
- **The audit must show, per writer, that it reads through** (§10, A3). Until it does, E26, E27 and S51 stay whole-object O, and the
  split is not done.
- `self_model_bundle_set` (E26) and `information_providers_update` (S51) get the same rule.

## 4. Cross-entity writes and contention

| Point | Today | Contract rule (Level A) |
|---|---|---|
| JOIN_PARTY acceptance (`cooperation/phase.py:174-196`) | acceptors walk `state.entities` order; each promotes the offerer's contract from tick-start state; duplicates collapse at apply, last entry per contract id wins (`patches.py:459-467`) | the declared unit order is `state_entities`; the cross-entity write goes to the offerer's E12 under O; **contention key** = contract id; winner = the last in commit-key order, as today. Whether one contract can be accepted twice is open (§10, A5) |
| trust and grudge sums (`cooperation/phase.py:252-265`) | float additions across groups | O on E14, in commit-key order |
| combat witness tier | several fights folded into one witness's model in `entity_updates` insertion order | O; the unit order is the fight order today |
| economy reservations (`economy.py:49-57`) | lowest entity id wins; a second pass runs inside lifecycle with fresh reservations | `unit_order = ascending_id`; contention key = node, item or corpse id; the second pass is its own step (ordinal of `_resolve_death_transfers`) |
| action routing (`actions.py:198-348`) | sliding state in ascending id; the defender's attacker pair LWW, so the highest-id hitter is the killer | `sliding = True`, `unit_order = ascending_id`; O on E18. Parallelising this is Level B (ADR clarification 1) |
| movement claims (`pipeline_phases/movement.py:184-295`) | live claims and the occupancy map built from earlier `new_position` writes and **stored on state** | `sliding = True`; claims and the map move to a step-owned store (§5) |
| spawn ids (`generator.py:83-118`) | one generator per tick, handed to world_dynamics only | spawn requests are collected in commit-key order, then allocated from the counter; any future spawner must use the same allocator (else `DuplicateEntityIdError`) |
| group ids | sequential (`groups.py:36-41`) and hashed (`military_conflict.py:340-341`); first add wins | F on S25; military_conflict runs earlier, so its hashed id wins, as today |
| faction sentiment (`sentiment.py:47-123`) | deltas, then absolute decay records, in one list; a clamp per record | O on S52; decay records keep their place after the deltas |

## 5. State hygiene: writes that move off tick-start state

Layer 1 forbids these. Each one moves, keeping today's values at each read point.

| Write (inventory §3) | Moves to | Note |
|---|---|---|
| cooperation `entity.timeline.append` (`phase.py:38/47/57/116`), with the `< 150` gates reading it back (`:110`, `:158`) | a delta (timeline events on the entity's update); the gate reads the step's own pending events plus the tick-start length | the deque is carried by reference into the next tick (`apply.py:789-793`), so this is durable history outside the update; SHADOW cannot undo it |
| movement `_occupancy_map_cache` and `transient_claims` (`movement.py:203-204`, `:294-295`) | a step-owned store, exposed to later steps through their declared `reads_deltas` | later readers (`legality.py:121`, occupancy, lodging) must declare it; per call site this is **[S, open]** (§10, A4) |
| `occupancy_snapshot` (`pipeline.py:65`) | kernel-owned per-tick store | written in the prologue, so the kernel owns it naturally |
| `movement_cache` invalidation (`pipeline.py:331`), `route_plans` (`route_search.py:149-180`) | kernel-owned stores with their own lifecycle, carried across ticks by the kernel | both are carried forward today (`apply.py:544-545`); they are caches, so the rule is "pure: same inputs give the same plan", proven by the audit |
| `_has_hostiles_or_dead_cache` (`intelligence.py:347`) | a per-tick derived value computed once by the strategic step's plan stage (§8) | |
| lazy memo caches (spatial query, world index, semantic index, region resolution, view, environment) | kernel-owned per-tick caches | benign only if pure; the audit lists any that are not |
| world_dynamics and evolution mutating the **incoming update** in place (`world_dynamics.py:128-274`, `evolution.py:133`) | copy-on-write: a step never mutates its input | breaks any rollback or diff that relies on the input staying unchanged |
| process globals (registries, content catalog, terrain cache, observability config) | loaded once per process from a declared path, fingerprinted (ADR clarification 8) | |

## 6. How each rule is proven (Level A)

- **Per class:**
  - C: a permuted-order unit test.
  - O and F: the serial executor's equivalence test.
  - K and T: none.
  - L: a declaration-coverage test.
- **Per stage PR**, ADR clarification 14:
  - a field-by-field state compare, which is primary. It treats S38 as a multiset, excludes T fields and E30, and compares
    `CausalMemory` entries by content, because the digest sees only their count (`cognition.py:252-256`);
  - the final hash under the current proof scheme (`PROOF_DIGEST_SCHEME`);
  - the `TICK_END` trail;
  - the existing gate and paired evidence.
- **For a non-serial executor**, add ADR clarification 18: several `PYTHONHASHSEED` values, permuted arrival, workers 1, 2 and 4,
  and failure cases. Reuse the subprocess pattern of `tests/unit/engine/test_set_order_follows_no_hash_seed.py`.

## 7. Fit with the distributed-workers experiment

- The experiment's seam is the explicit Collection executor (`kernel.py:193-198`). This contract is the Resolution side. They share
  one principle: pure compute over a declared input, with the kernel committing. Neither changes the other.
- ADR clarification 11 (a lost unit is recomputed from the same inputs; a raised unit is a FAILURE no-op) matches the experiment's
  proposed dead-worker rule (local recompute, design §10 choice 1).

## 8. The prototype slice: `fused_strategic_pass`

`run_phase("strategic_intelligence", …)` at `pipeline.py:393`, implemented in
`src/systems/strategic_systems/intelligence.py`. Stage 3 also has to wait for that file to leave the hands-off list (the
COMBAT-RETREAT P2).

**Two stages inside the step:**
1. **Plan (unit = world).** It reads tick-start state: every entity's `combat.alive` and faction, for the hostiles-or-dead flag
   (`:336-347`). It also reads `update.dirty_set`, `update.current_policy_set` (the budget) and the cadence. It produces the
   candidate list (`StrategicWorkQueue.build`, `:353-358`) and the flag, both as per-tick derived values, not on state.
2. **Units (unit = entity, `unit_order = candidate_list`).** Each candidate reads:
   - its own tick-start entity;
   - its own earlier deltas: E11 `inventory` (to compute pending inventory), E12 `strategic`, and the existing entry;
   - `state.town_tiles` and `state.town_center`.
   It writes only its own entry: E20 `navigation`, E7 `interaction` (reset), E12 `strategic`, E9 `identity`, E29
   `property_updates`, and T `metric_counters`. **No cross-entity write** [S, spot-checked].

| Declaration field | Value |
|---|---|
| `sliding` | False: no unit reads another unit's delta from this step |
| merge | O on every written field; commit key = candidate order |
| contention | none |
| state hygiene | the flag moves off state (§5) |
| fast path | the off-cadence fast path (`:375-410`) is part of the unit; #852 characterises it branch by branch and lists the known fast-vs-slow disagreements; those tests are reused as Level A evidence |

**Stage 3 exit:** the ADR's evidence standard (§6) on the 3 gate worlds at seed 42 for 300 ticks, under the serial executor, plus
the audit showing observed writes equal the declaration.

## 9. Findings for their owners (not fixed by the contract)

These are behaviours the contract **reproduces** at Level A. Fixing any of them changes results, so each one is a separate ticket
for its owner, not a contract change. The inventory found them statically, and the items marked [rechecked] were confirmed by hand
on `1fb40ac76`.

| # | Finding | Where | Owner |
|---|---|---|---|
| F1 | `CombatUpdate.is_noop` ignores the nested and flag fields, so a CombatUpdate carrying only `wound_update`, `social_upd`, equipment, `outcome_kind` or `hit_tick_set` is dropped by merge, by the compactor and through `EntityUpdate.is_noop`. It works today only because `combat_actions.py:70-108` unpacks the payloads [partly rechecked] | `updates.py:133-142` | rpg-planner |
| F2 | `SocialUpdate` merges `familiarity`, `debt`, `fear`, `salience` and `rejection_increment` as per-key LWW, while trust and grudge are summed; two same-tick gains for one target keep only the last | `updates.py:373-384` | rpg-planner |
| F3 | `RelationshipService.process_update` rebuilds `rejection_count` from only the keys in the current update, so **any social update wipes every other rejection count** [rechecked] | `relationships.py:133` | rpg-planner |
| F4 | `processed_transaction_ids` persists in hash-seed order and grows without dedup across ticks [rechecked]. Unhashed, membership only | `updates.py:1148/1274`, `economy.py:275`, `apply.py:353-354` | rpg-planner (perf if memory matters) |
| F5 | counter merges differ: `next_node_id_set` is LWW (could lower it), `next_group_id_set` is max; `force_full_scan` is not merged at all | `updates.py:1236`, `group_update_merge.py:20-21` | rpg-planner |
| F6 | `entities_remove` runs before replacements are written back, so a removed entity with passive changes is re-inserted. Latent: no producer | `apply.py:282-297` | rpg-planner |
| F7 | `*_set` fields (world trauma and retaliation, biological) discard deltas from every other step | `apply_plan.py:181-182`, `patches.py:129-130` | rpg-planner (may be intended) |
| F8 | the digest sees only `CausalMemory`'s count and capacity, not its entries (a digest blind spot) | `cognition.py:252-256` | perf (PERF-D5 owner) |

## 10. Open items for the access audit (child 2) and for draft 2

- **A1.** Confirm the §3 writer attribution at runtime, especially the "via" rows: action modules reached through `domain_logic`.
  Also check whether the `tactical*`, `kernel`, `executor` and `worker_logic` writers are reachable inside refine (inventory, method
  and limits).
- **A2.** Every §5 hidden mutation: observed, with the step, field and tick count. Check also whether
  `observability/entity_timeline.py:77` appends inside refine.
- **A3.** For each `cognition_bundle_set` and `self_model_bundle_set` writer: does it read through? This gates §3.3.
- **A4.** Which later steps read movement's occupancy map and claims through state.
- **A5.** Whether one JOIN_PARTY contract can be accepted by two entities in a tick (`find_pending_incoming_offer`, `phase.py:130`).
- **A6.** The lodging bed ordering rule (`lodging.py:177-189`).
- **Draft 2:**
  - folds in A1 to A6;
  - assigns every step its `StepDecl` (one table over all ~45 `run_phase` calls);
  - takes stage 0's per-phase costs, for the slice order of stage 4.
