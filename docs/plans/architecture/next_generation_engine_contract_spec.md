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

- **Status: DRAFT 2**, 2026-11-11. The owner dispatched it (#715 6743047506). The ADR it implements is
  `docs/architecture/next_generation_engine_adr.md` (accepted, #715 6742854335).
- **Draft 2 adds child 2's access-audit report** (`next_generation_engine_access_audit_report.md`, merged as #863, main
  `5c6990e51`). It folds the report into §3.4, §5, §8 and §10, and gives every step a starting declaration in
  `next_generation_engine_step_declarations.md`.
- **Still missing: stage 0's re-measure.** The slice order for stage 4 waits on it (§10).
- **Labels:** **[S]** marks a static reading only. **[O]** marks something the audit observed on the two gate worlds (6 cells,
  5000 ticks each). An [O] that nothing was seen means only that the detector saw nothing; report, "What the detector cannot see".
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

The access audit (child 2) checked `writes` at runtime. Its reads are a static, entry-only scan (audit plan §5). Each of the 43
steps' starting values is in `next_generation_engine_step_declarations.md`. §3.4 says how a stage turns one into a final `StepDecl`.

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
| **C** | E4 `moved_this_tick` (OR); E10 `attributes` (integer sum; C **only** because the cap is applied once, at apply: `AttributePatch.apply` (`src/engine/patches.py:617/632`) calling `rpg_depth.enforce_attribute_caps` (`src/engine/rpg_depth.py:31`). A per-merge clamp would move it to O); E16 `reward` (sum) |
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
- `self_model_bundle_set` (E26) and `information_providers_update` (S51) get the same rule.
- **Decision (draft 2): the split is not part of v1. E26, E27 and S51 stay whole-object O.**
  - The audit answers A3 from source only (class S). That is not enough to gate a change whose failure mode is silently keeping
    changes that are dropped today.
  - Three of the inventory's nine E27 writers are flag-OFF on the gate worlds and were never exercised: memory_update,
    habit_bias_action_style and role_model_selection. A fourth, quest_rewards, was exercised but never seen writing the bundle.
    For E26, self_model is flag-OFF too.
  - Five E27 writers were seen writing it [O]: combat_engagement, action_routing, movement_routing, near_death_hardening and
    lifecycle. All five are in the inventory. The last four are missing from the audit's own declarations (†), and the
    attribution caveat applies (§3.4).
  - Nothing in stage 3 needs the split: `fused_strategic_pass` writes no bundle (§8).
  - **To reopen it:** a stage that needs the split cuts a ticket with rpg-planner for an observed-read proxy. That ticket carries
    its own hash proof and flag-ON cells for the unexercised writers. It is not filed now.

### 3.4 From the audit's declarations to a stage's StepDecl

What the audit showed [O]: **17 of the 35 exercised steps wrote buckets their declaration does not list.** 22 declared at least
one bucket that was never written in 30000 ticks. The heaviest gaps are action_routing (12 undeclared buckets) and
resource_transactions (16). The audit's declarations came from coarse sources: the phase graph's output domains, the feasibility
review's table, or the step's name. So most gaps are thin declarations, not steps writing outside their remit. The data cannot tell
the two apart.

Rules for every stage that converts a step:
1. **`writes` starts as observed ∪ declared**, the step's row in `next_generation_engine_step_declarations.md`.
2. **Each † bucket is settled before it is declared.** Is it a real write, or a re-copy or compaction of the input (the report's
   attribution caveat)? One way: rerun that step's audit with an input-identity check per bucket. A re-copy is not declared as a
   write, but the step must still not change it.
3. **A flag-OFF step is not converted.** The 8 steps behind OFF flags keep their serial position and whole-update access until a
   flag-ON audit cell exists for them. That cell is part of their own stage, not of v1.
4. **A ° bucket stays declared** if the source shows a writer. Never seen in 30000 ticks is not the same as never written; it may
   just not have happened on these two worlds. The declaration-coverage test (§6) catches an undeclared write, not an unused
   declaration.
5. **Reads stay class S.** The audit's read scan covers the entry function only. A stage lists its step's reads from its own
   transitive reading, and the undeclared-read guard (§1, layer 3) is what enforces them.

## 4. Cross-entity writes and contention

What the audit showed [O]: cross-entity work comes from a proxy, not a per-actor trace (report, "Cross-entity proxies"). The proxy
counts entries created for an id absent from the input update. It cannot tell a unit creating **its own** first entry from a unit
writing **another** entity's entry. The heaviest creators are cooperation (21564 ticks, up to 16 entries in a tick), world_dynamics
(21894, 14), movement_routing (14399, 20) and combat_engagement (12938, 9). Every rule below stays [S] until a stage settles its
own step's targets.


| Point | Today | Contract rule (Level A) |
|---|---|---|
| JOIN_PARTY acceptance (`cooperation/phase.py:174-196`) | acceptors walk `state.entities` order; each promotes the offerer's contract from tick-start state; duplicates collapse at apply, last entry per contract id wins (`patches.py:459-467`) | the declared unit order is `state_entities`; the cross-entity write goes to the offerer's E12 under O; **contention key** = contract id; winner = the last in commit-key order, as today. Whether one contract can be accepted twice is still open after the audit (§10, A5). Cooperation's stage settles it with a contention scenario test before converting the step |
| trust and grudge sums (`cooperation/phase.py:252-265`) | float additions across groups | O on E14, in commit-key order |
| combat witness tier | several fights folded into one witness's model in `entity_updates` insertion order | O; the unit order is the fight order today |
| economy reservations (`economy.py:49-57`) | lowest entity id wins; a second pass runs inside lifecycle with fresh reservations | `unit_order = ascending_id`; contention key = node, item or corpse id; the second pass is its own step (ordinal of `_resolve_death_transfers`) |
| action routing (`actions.py:198-348`) | sliding state in ascending id; the defender's attacker pair LWW, so the highest-id hitter is the killer | `sliding = True`, `unit_order = ascending_id`; O on E18. Parallelising this is Level B (ADR clarification 1) |
| movement claims (`pipeline_phases/movement.py:184-295`) | live claims and the occupancy map built from earlier `new_position` writes and **stored on state** | `sliding = True`; claims and the map move to a step-owned store (§5) |
| spawn ids (`generator.py:83-118`) | one generator per tick, handed to world_dynamics only | spawn requests are collected in commit-key order, then allocated from the counter; any future spawner must use the same allocator (else `DuplicateEntityIdError`) |
| group ids | sequential (`groups.py:36-41`) and hashed (`military_conflict.py:340-341`); first add wins | F on S25; military_conflict runs earlier, so its hashed id wins, as today |
| faction sentiment (`sentiment.py:47-123`) | deltas, then absolute decay records, in one list; a clamp per record | O on S52; decay records keep their place after the deltas |

## 5. State hygiene: writes that move off tick-start state

Layer 1 forbids these. Each one moves, keeping today's values at each read point. Observed tick counts are summed over the audit's
6 cells, out of 30000 per step (report, "Hidden mutations of tick-start state").

| Write (inventory §3) | Audit [O] | Moves to | Note |
|---|---|---|---|
| cooperation `entity.timeline.append` (`phase.py:38/47/57/116`), with the `< 150` gates reading it back (`:110`, `:158`) | seen, 3195 ticks (after the detector was fixed to see appends to a full deque) | a delta (timeline events on the entity's update); the gate reads the step's own pending events plus the tick-start length | the deque is carried by reference into the next tick (`apply.py:789-793`), so this is durable history outside the update; SHADOW cannot undo it |
| timeline elements edited in place | 0 edits in 300 samples (sampled every 100 ticks; 860 elements replaced, not edited) | **candidate:** make the timeline event models `frozen=True`. Their only `entity.timeline` writers append (`entity_timeline.py:77`, cooperation) | evidence, not proof, within the sampler's limits. A hygiene change for its own ticket with rpg-planner; not filed here |
| movement `transient_claims` and `_occupancy_map_cache` (`movement.py:203-204`, `:294-295`) | claims seen on 30000 ticks (movement_routing); map seen on 24403 (movement_routing) and 29994 (position_swaps) | a step-owned store, exposed to later steps through their declared `reads_deltas` | **real state outside the update, not a cache.** Readers (`legality.py:121`, occupancy, lodging) stay **[S, open]** (§10, A4). Movement's stage **removes the state attributes** instead of leaving them, so an undeclared reader fails loudly rather than reading a stale value |
| `route_plans` (`route_search.py:149-180`) | seen, 23822 ticks (movement_routing) | kernel-owned store with its own lifecycle, carried across ticks by the kernel | **real state, not a cache**, carried forward today (`apply.py:544-545`). The rule is "pure: same inputs give the same plan", proven in movement's stage by the equivalence compare |
| `occupancy_snapshot` (`pipeline.py:65`), `movement_cache` invalidation (`pipeline.py:331`) | not seen in any step: both are written outside `run_phase` | kernel-owned stores | written in the prologue or between steps, so the kernel owns them naturally |
| `_has_hostiles_or_dead_cache` (`intelligence.py:326-347`) | **not seen** (0 ticks), on the watch list | **no move needed at Level A.** It is set at state construction (`state.py:1490`); strategic writes it only when it is None, which does not happen on tick-start state; the clear at `actions.py:347` is on the per-actor sliding state, another object | draft 1 listed it as a write; the audit's reading and observation agree it is not one. §8's plan stage may still compute it as a derived value, for clarity only |
| lazy memo caches: `_corpse_map_cache`, `_ground_item_map_cache`, `_node_map_cache`, `_region_index_cache`, `_region_list_cache`, `_spatial_grid_cache`, `_building_map_cache`, `_building_region_map_cache`, `_readonly_entities_cache`, `world_indexes` | seen, filled on first read by whichever step reads first (up to 28055 ticks) | kernel-owned per-tick caches | benign only if pure. Which step fills a cache depends on step order, so each must give the same value whichever step fills it. That is a per-cache Level A test |
| index hit/miss counters `_index_hits`, `_index_misses` | Tier 2 hits: combat_engagement (30000 and 2337 ticks), strategic_intelligence (14204) | kernel-owned cache statistics, class T | counters only; nothing suggests decision state. Promoted to the watch list for any later audit run |
| world_dynamics and evolution mutating the **incoming update** in place (`world_dynamics.py:128,181,219-221,272-274`, `evolution.py:133`) | seen: evolution on eu:combat, eu:identity, eu:property_updates; world_dynamics on su:world_updates. **A lower bound**: an equal-length edit inside a bucket is not seen | copy-on-write: a step never mutates its input | proven per stage by its own test (§6), not by the audit's list |
| process globals (`_terrain_cache`, `runtime_content_source`, the two `common_knowledge_seed` catalogs) | no change seen; the list is from a source search and is not exhaustive | loaded once per process from a declared path, fingerprinted (ADR clarification 8) | **registries held on the kernel were not checked by the audit at all**, and those on state got only the identity-and-length check. The fingerprint must cover kernel-held registries too |

## 6. How each rule is proven (Level A)

- **Per class:**
  - C: a permuted-order unit test.
  - O and F: the serial executor's equivalence test.
  - K and T: none.
  - L: a declaration-coverage test.
- **Per converted step:**
  - a copy-on-write test: deep-compare the input update before and after compute; any change fails. The audit's in-place list is a
    lower bound, so it does not replace this test;
  - the declaration-coverage test, run through the audit recorder (`ENABLE_ACCESS_AUDIT`, hash-neutral) on the stage's worlds: an
    observed write outside `writes` fails.
- **Per stage PR**, ADR clarification 14:
  - a field-by-field state compare, which is primary. It treats S38 as a multiset, excludes T fields and E30, and compares
    `CausalMemory` entries by content, because the digest sees only their count (`cognition.py:252-256`). **A hash match alone
    is never claimed as equivalence** while F8 stands: it says nothing about CausalMemory content;
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

`run_phase("strategic_intelligence", …)` at `pipeline.py:394` (main `5c6990e51`), implemented in
`src/systems/strategic_systems/intelligence.py`. Line numbers below are at `5c6990e51`; #862 edited the file just before it.

**Entry condition, still current:** the file must leave the hands-off list first. It is held for
`TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE` (P2), which is still in
`agent-working/tickets/todos/` at `5c6990e51`. Rpg-planner owns the list and says when it clears.

**Two stages inside the step:**
1. **Plan (unit = world).** It reads tick-start state: every entity's `combat.alive` and faction, for the hostiles-or-dead flag
   (`:326-347`). It also reads `update.dirty_set`, `update.current_policy_set` (the budget) and the cadence. It produces the
   candidate list (`StrategicWorkQueue.build`) and the flag, both as per-tick derived values, not on state.
2. **Units (unit = entity, `unit_order = candidate_list`).** Each candidate reads:
   - its own tick-start entity;
   - its own earlier deltas: E11 `inventory` (to compute pending inventory), E12 `strategic`, and the existing entry;
   - `state.town_tiles` and `state.town_center`;
   - **other entities' tick-start state**, through `SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)` (`:447`)
     and `radius=3.0` (`:595`, `:917`, for salience);
   - **whole tick-start state**, through `evaluate_strategic_intent(state, temp_entity, …)` (`:618`),
     `RoutineService.evaluate_anchored_behavior(entity, state)` (`:589`, `:913`) and `ConcernIntakeSystem.evaluate_salience(…, state)`
     (`:596`, `:918`);
   - the lazy caches those calls fill (`_spatial_grid_cache`, `_region_list_cache`; §5).
   **This list is not complete.** Reads stay class S (§3.4, rule 5), and the callees above read further. What the contract needs
   is narrower, and it holds: **every read is of tick-start state or of the unit's own earlier deltas, never of another unit's
   delta from this step** [S, rpg-planner checked against `5c6990e51`]. The stage 3 exit checks it at runtime.

   It writes only its own entry: E20 `navigation`, E7 `interaction` (reset), E12 `strategic`, E9 `identity` (the craft-target
   clear), E29 `property_updates`, and T `metric_counters`. **No cross-entity write** [S, spot-checked].
   - **Audit [O]:** observed writes are eu:interaction, eu:navigation, eu:property_updates and eu:strategic. These match this list.
     The audit's own declaration lacked interaction and property_updates (†); this spec already had them. eu:identity was never
     seen in 30000 ticks (°), and stays declared because the source writes it. eu:task, in the audit's declaration, is not in this
     list and was never seen; it is not declared (rpg-planner agrees the declaration was wrong).
   - **Cross-entity proxy [O]:** entries were created for absent ids on 1011 ticks (up to 4 in a tick). The proxy cannot tell a
     candidate's own first entry from another entity's, so "no cross-entity write" stays [S]. The stage 3 exit adds a check.
   - **Hidden mutations [O]:** only lazy caches (`_region_list_cache`, `_spatial_grid_cache`) and the index hit counter.
     `_has_hostiles_or_dead_cache` was not mutated (§5).

| Declaration field | Value |
|---|---|
| `sliding` | **False.** Units read other entities' tick-start state, but no unit reads another unit's delta from this step |
| merge | O on every written field; commit key = candidate order |
| contention | none |
| state hygiene | no write to move (§5). The two lazy caches it fills become kernel-owned per-tick caches |
| fast path | the off-cadence fast path (`:375-410`) is part of the unit. #852 characterises it branch by branch; those tests are reused as Level A evidence |

**Fast-vs-slow disagreements that Level A reproduces and does not fix.** Each is today's behaviour; fixing it changes results and
belongs to its own ticket:
- **#852 row 6, `earlier_phase_target_set`**, still marked after #862.
- **Objective-status leniency.** The fast-path guard (`:395`) does not check `active_obj.status`, while the slow path (`:657`)
  requires `ObjectiveStatus.ACTIVE` (#862 disclosure 2; recorded on `TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE`).
- **Overwrite inconsistency** (`TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED`, scope note). When the unit has no entry, the fast path
  builds a new `EntityUpdate`. When it has one, it `replace`s it. The two branches drop different fields. **This bears directly on
  how the unit's delta is formed under O**: the stage must reproduce both branches exactly, and its field compare must cover an
  entity with and without an earlier entry.

**Stage 3 exit:**
- **primary:** the ADR's evidence standard (§6), the field-by-field compare, on the 3 gate worlds at seed 42 for 300 ticks, under
  the serial executor;
- **final-hash equality under the serial executor on the pinned 5000-tick set** that base cells already exist for:
  crowded_frontier s42-46, urban_political s44, frontier_living_world s45 (runner `PYTHONHASHSEED=0`, `72320cac`). Rare branches
  need the length: #862's defect changed no outcome in 7 × 5000-tick cells. Rpg-planner accepts these cells as RPG evidence. A
  hash match here is supporting evidence only (§6, F8);
- the declaration-coverage and copy-on-write tests (§6);
- a per-unit target check: every entry a unit writes is keyed by that unit's own entity id;
- a per-unit read check: no unit reads the running update for another entity id.

## 9. Findings for their owners (not fixed by the contract)

These are behaviours the contract **reproduces** at Level A. None is held for the contract: F3 is fixed independently under its own
ticket, `TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME`. Fixing any of them changes results, so each one is a separate ticket
for its owner, not a contract change. The inventory found them statically, and the items marked [rechecked] were confirmed by hand
on `1fb40ac76`.

| # | Finding | Where | Owner | Triage (rpg-planner, 2026-11-09, via lead-planner-u24) |
|---|---|---|---|---|
| F1 | `CombatUpdate.is_noop` ignores the nested and flag fields, so a CombatUpdate carrying only `wound_update`, `social_upd`, equipment, `outcome_kind` or `hit_tick_set` is dropped by merge, by the compactor and through `EntityUpdate.is_noop`. It works today only because `combat_actions.py:70-108` unpacks the payloads [partly rechecked] | `updates.py:133-142` | rpg-planner | no flight impact: every flight writer sets `hit_damage_set` with `attacker_id`/`damage_taken`, and CombatPatch applies `last_hit_damage` only on `hit_landed`. P3 latent, not filed |
| F2 | `SocialUpdate` merges `familiarity`, `debt`, `fear`, `salience` and `rejection_increment` as per-key LWW, while trust and grudge are summed; two same-tick gains for one target keep only the last | `updates.py:373-384` | rpg-planner | `rejection_increment` (should sum) rides F3's ticket; the other fields are merge semantics with no reader shown, so they stay with this contract (children 4/5); no RPG ticket unless a reader is shown |
| F3 | `RelationshipService.process_update` rebuilds `rejection_count` from only the keys in the current update, so **any social update wipes every other rejection count** [rechecked] | `src/systems/social_systems/relationships.py:133` | rpg-planner | **filed:** `TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME` (P1, rpg). Reader: `appraisal.py:125` (recruitment's social-fatigue penalty, which also gates loyalty); 5 writers in `core_actions.py`. The fix changes recruit outcomes, so it is paired-measured; priority with rpg-designer |
| F4 | `processed_transaction_ids` persists in hash-seed order and grows without dedup across ticks [rechecked]. Unhashed, membership only | `updates.py:1148/1274`, `economy.py:275`, `apply.py:353-354` | rpg-planner (perf if memory matters) | P3, not filed; this contract treats it as a multiset (§3.2, §6) |
| F5 | counter merges differ: `next_node_id_set` is LWW (could lower it), `next_group_id_set` is max; `force_full_scan` is not merged at all | `updates.py:1236`, `group_update_merge.py:20-21` | rpg-planner | no reader shown; stays with this contract (children 4/5) |
| F6 | `entities_remove` runs before replacements are written back, so a removed entity with passive changes is re-inserted. Latent: no producer | `apply.py:282-297` | rpg-planner | no live writer of `StateUpdate.entities_remove` at `1fb40ac76` (only the field, the merge and `dirty.py`); the merge also passes it through `set()`, the same ordering class as F4. P3, not filed |
| F7 | `*_set` fields (world trauma and retaliation, biological) discard deltas from every other step | `apply_plan.py:181-182`, `patches.py:129-130` | rpg-planner (may be intended) | no reader shown; stays with this contract (children 4/5) |
| F8 | the digest sees only `CausalMemory`'s count and capacity, not its entries (a digest blind spot) | `cognition.py:252-256` | perf (PERF-D5 owner) | with perf-planner (PERF-D5 owner), forwarded via ubuntu |

## 10. The audit's open items after draft 2

The questions draft 1 put to the audit, with what the report answered. "v1" is the audit as built: it observes writes and hidden
mutations, and reads only statically (no read proxy, plan §5).

| Item | Question | Status after the report | What settles the rest |
|---|---|---|---|
| A1 | §3's writer attribution at runtime, including the "via" rows | **partly answered [O]**: per-step observed writes are in `next_generation_engine_step_declarations.md`. The report does not attribute a write to a module, so the "via" rows and whether the `tactical*`, `kernel`, `executor` and `worker_logic` writers are reached inside refine stay [S] | each stage, for its own step (§3.4, rules 1 and 2) |
| A2 | every §5 hidden mutation, observed, with step, field and ticks | **answered [O]** (§5), within the detector's limits. `entity_timeline.py:77` appends to `entity.timeline` and is reached from `kernel.py:1027` (report, sampled-check limits). Whether that call is inside refine is not stated there, and is [S, open] | the timeline's own move to a delta (§5) |
| A3 | does each bundle writer read through? | **class S only**; 3 of the 9 E27 writers, and E26's self_model, unexercised | not needed for v1: the split is deferred (§3.3) |
| A4 | which later steps read movement's occupancy map and claims | **class S only** | movement's stage removes the state attributes (§5), so an undeclared reader fails loudly |
| A5 | can one JOIN_PARTY contract be accepted twice in a tick? | **not answered**: the proxy counts created entries, not acceptances | cooperation's stage: a contention scenario test before converting the step (§4) |
| A6 | the lodging bed ordering rule (`lodging.py:177-189`) | **not covered** by the report | the stage that converts lodging's step |
| — | the 8 flag-OFF steps | **no evidence**: never exercised (report, "Declared, not exercised") | not converted until a flag-ON audit cell exists, in their own stage (§3.4, rule 3) |
| — | in-place mutation of the input update | **a lower bound [O]**: evolution, world_dynamics | copy-on-write test per converted step (§6) |

**Debt carried from the audit, not to build on:** the recorder is passed through `state.feature_flags["ACCESS_AUDIT_SINK"]`, and a
checkpoint would pickle it. The declaration-coverage test (§6) may use the recorder as it is, flag on, in tests only. A kernel-owned
auditor, as audit plan §3 intended, comes before any stage depends on the recorder outside tests.

## 11. Before draft 3 (and before stage 3 is cut)

- **Stage 0's per-phase costs** (perf-planner) set the slice order for stage 4. Not in yet.
- **Rpg-planner's sign-off that §8 is complete enough to cut stage 3** (AC 3; ubuntu review A-n1). Draft 2 got four amendments (A-D, 2026-11-11), now in §8; the sign-off is on that hunk.
- **Checkpoint restore** (lead-planner-u24, 2026-11-10). `ScenarioCheckpointer.restore` builds its Kernel apart from
  `scenario_runtime._build_kernel`, and it has already drifted: it drops the governor and the `scenario_event_recorder`, which are
  telemetry only today, per rpg-planner. So:
  - `TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK` (filed by testing-planner, run after
    the RPG batch per #715 6757579399) must be green before any stage that changes Kernel construction or the state shape;
  - restore builds through the same builder as a fresh run;
  - typed deltas change the checkpoint schema, as the bundle split (§3.3) would if it were reopened. That needs a
    `checkpoint_fields` migration and a contract version in the run manifest (ADR item 16).
- **The CausalMemory blind spot (F8)** applies to restore as well as to equivalence: both rely on the proof digest, which does not
  hash CausalMemory content. §6 already requires the content compare; restore's test needs it too.
