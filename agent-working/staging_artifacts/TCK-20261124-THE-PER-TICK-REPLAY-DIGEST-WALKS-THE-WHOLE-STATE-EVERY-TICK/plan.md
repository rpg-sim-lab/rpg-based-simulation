---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK
date: 2026-11-24
tags: []
---

# Plan: a cheaper per-tick canonical digest with byte-identical output

Author: rpg-implementer-ubuntu. For approval by rpg-planner-ubuntu BEFORE any `src/` change. Evidence: investigation.md in this folder.

## What the evidence says (one paragraph)
Per tick, in audit mode, at tick 250 to 300 of `frontier_living_world` s42: building the canonical dict about 51 %, `json.dumps` about 47 %, sha256 about 3 %. All 55 entity objects are replaced every tick (0 of 55 survive), so the entity-level memo never hits; 72 % of the components of a replaced entity ARE the same objects. The cold build is dominated by the entity's INLINE `strategic` block (4.9 of 8.2 ms for 55 entities with every other component warm; `dataclasses.asdict` with its deepcopy), which has no memo. The dirty set cannot be used (all entities dirty every tick; its coverage of the hasher's input is incomplete and leaks were observed).

## Chosen approach (two stages, each independently shippable, each proven byte-identical)
### Stage 1: memoize the strategic canonical dict like every other component does (data-build half)
1. `StrategicComponent.to_canonical_dict()` and (same pattern) `SocialComponent.to_canonical_dict()`: the exact expressions now written inline in `EntityState.to_canonical_dict` move, unchanged, into the component method, which fills the component's own `_canonical_cache` (an `init=False, compare=False` slot named like the 20-plus existing ones, appended AFTER the existing fields so older checkpoints still restore, as the repo rule at checkpoint_fields.py:109 and group_record.py:47 says). `EntityState.to_canonical_dict` then reads `"strategic": self.strategic.to_canonical_dict()`. The returned dict is value-equal to the old inline dict, so `to_canonical_data`, the pretty dump (certification harness) and every dict-comparing test see no change.
2. Lifecycle (durable-state rule): the memo lives on the frozen component object, is filled on first read, is never mutated afterwards, and dies with the object; a replaced component starts with None. No table, no bound to manage (it is bounded by the state itself, as every existing memo is). Inspectable by the existing audit (`audit_cached_canonical_dicts` walks every dataclass holding `_canonical_cache`, recomputes from scratch and compares) and by `tests/architecture/state_digest_probe.py` (clears every `_canonical_cache` before probing), both without change.
3. Expected effect (a prediction to check, not a claim): at tick 300 the strategic block is 4.9 of 10.5 ms of the data build; with the component hit rate near 72 % or more, most of it disappears. perf-planner measures before and after (AC5); this ticket reports the result and claims nothing.
### Stage 2 (ONLY if Stage 1's measured result is not enough, and only on your approval): splice per-component JSON text into the dump
The remaining dump cost is the `json.dumps` of about 650 KB, growing with state. The option: memoize the compact sorted JSON TEXT of each memoized component dict (same slot lifecycle, validated by identity of the memo dict it was built from, so a cleared or rebuilt memo can never leave a stale fragment) and have the hasher write the document by joining fragments in sorted-key order (entities by STRING key order). Costs: a second emission path that must mirror `to_canonical_dict` key sets (drift risk, mitigated by the equality test running on every tick of two worlds), and the in-place-mutated memo dict would no longer show in the digest (today it does; the existing audit already treats such a mutation as the bug it is). Not proposed for the first PR.

## Rejected, with reasons
- **DirtySet-driven partial recompute**: rejected. Coverage not provable (investigation (b)): no fields for about 20 collections the hasher reads, observed leaks, `validate_dirty_set` checks 5 kinds; and every entity is dirty every tick, so it would save nothing for the 89 % of bytes that matter.
- **Entity-level JSON fragment memo**: rejected. 0 of 55 entities survive a tick; hit rate 0 %.
- **A faster encoder (orjson and similar)**: rejected. New dependency; differs from `json.dumps` on float exponent text, Enum members (IntEnum prints as int, str-Enum as value, also as key), NaN, big ints and non-str keys (investigation (c)); a wrapper that re-proves all of it costs more than it saves and any miss changes digests.
- **A faster `asdict` replacement (no deepcopy)** inside the cold build: not needed once the memo hits; kept as a later, separate option for the misses (28 % of components).
- **Dropping `sort_keys` and pre-sorting**: rejected for now: the second sort is about a quarter of the dumps (6.5 vs 8.4 ms), nested `asdict` dicts are in field order and would all need sorting, and it moves the digest's definition into every producer.
- **`id()`-keyed side tables or module-level caches**: rejected; hidden durable state across kernels in one process, unbounded unless pruned, and no lifecycle owner. Frozen slots objects cannot be weak-keyed.
- **Changing cadence, the digest scheme, the fingerprint or the replay writer**: out of scope (ticket).

## How equality is proven (AC1)
The CURRENT dict build stays as the reference: before Stage 1 lands, the reference is the code on origin/main; in the PR it is kept as a test-only function `reference_canonical_data(state)` (copied verbatim from main, including the inline strategic/social blocks) in the test module, and `reference_digest` = sha256 of `json.dumps(reference_canonical_data(state), sort_keys=True, separators=(",", ":"))`. The test asserts, for every state it visits:
- `CanonicalStateHasher.get_hash(state) == reference_digest(state)`;
- `to_canonical_json(state) == reference json` and `to_canonical_json(state, pretty=True) == reference pretty`;
- `to_canonical_data(state) == reference_canonical_data(state)` as Python values.
Cold and warm: each assertion is made twice, once on a state whose memos are all cleared and once on a warm one, to prove the memo does not change the result.

## AC3 and AC4
- AC3 (governor `no_replay` and buffer-drop paths unchanged): nothing in the kernel, governor, replay manager or policy is touched; `_phase_persistence`'s branch (replay_allowed, audit_mode or FULL richness) is unchanged. Named tests run before and after: tests/unit/engine/test_kernel_digest_via_scheduler.py, tests/unit/engine/test_hash_scheduler.py, tests/unit/kernel/test_replay_pressure.py, tests/unit/kernel/test_replay_overflow.py, tests/unit/core/test_operational_flags.py (`test_no_replay_stops_the_replay_sink`), tests/unit/perf/test_profile_tick_contract.py.
- AC4 (no new whole-state serialization on the tick thread; any cache typed, bounded, with a lifecycle): Stage 1 adds no serialization pass (it removes work); the only new state is one `_canonical_cache` slot on two component classes, with the same lifecycle as the existing memos, as stated above. A pin test shows the new memo is covered by the existing audit and probe.

## Docs, parity and registry this touches
- docs/engine/deterministic_execution.md, "The canonical hash": add a sentence that the strategic and social blocks of an entity are memoized per component like the others; the digest definition, `flat-sha256-v5` and the byte output are unchanged.
- docs/parity_ledger/infrastructure.yaml: the entry for src/engine/checkpoint.py / `CanonicalHashScheduler` (v2_evidence) is checked; the `src/core/state.py` canonical-dict evidence lines are updated only if a ledger `v2_evidence` cites the moved lines.
- docs/performance/hash_callsite_inventory.{md,json} and its test: re-checked (no call site moves in Stage 1).
- mechanisms.yaml: the changed-code advisory is run at close; any entry citing `EntityState.to_canonical_dict` is reported to rpg-planner, not edited by me.
- Stage 1 changes src/core/state.py and src/core/strategic.py, src/core/models/social.py: also `tests/unit/core/test_entity_integrity.py` and `tests/unit/engine/test_checkpoint_schema.py` pin field order and cache-field names; the appended slot is the case they allow.

## What I need from rpg-planner-ubuntu
1. Approve Stage 1 as the first PR (Stage 2 held back).
2. AC2's replay-bytes comparison needs a lead heavy-slot GO later (two arms on frontier_living_world s42, 2000 ticks, replay on, audit_mode); I do not ask for it now.
3. Say if a record of the equality test at 2 worlds should include a third (the ticket says at least 2).

## ADDENDUM: status after the four conditions (rpg-planner-ubuntu, Stage 1 approval)
Condition 3 answers NO, so per the approval Stage 1 is STOPPED here and nothing is coded. Facts are in investigation.md "ADDENDUM". In short:
- A new `_canonical_cache` slot on StrategicComponent / SocialComponent is a checkpoint schema append: it changes the pickle bytes of every checkpoint and refuses every existing checkpoint unless two ruling-backed `FIELD_RULES` rows are added (checkpoint_fields.py), and a populated memo dict is pickled with the component. The existing memo slots on other records already work this way.
- Conditions 1 (replace/unpickle/copy paths) and 4 (callers only read) hold. Condition 2: no in-place mutation site found by scan (2 false positives), but the containers are plain dict/set/list in a running world, so nothing but convention and the audit prevents a future one.
DECISION NEEDED (options, my recommendation first):
- A (recommended): memoize WITHOUT a new record slot: a typed memo owned by the kernel (the object that already outlives each tick), keyed by `id()` of the component with a strong reference held in the entry, pruned to the live components after each digest (bounded by the state), with a stated lifecycle; `CanonicalStateHasher.get_hash` keeps its signature and gains an optional memo argument; no schema, checkpoint, replay or pickle change. Cost: the memo is hidden-by-design state outside the record, so it needs its own typed class, a pin test of the bound, and the audit extended to it.
- B: the slot on the two components plus two `FIELD_RULES` rows (rulings needed from rpg-designer: the memo is not state, so the fill is None) and a schema/pickle change. Smaller code, but a checkpoint format change.
- C: do nothing for the data-build half and go to Stage 2's text splice only on the kernel-owned memo (same ownership problem as A).
All three keep the digest byte-identical; E1-E11 apply to any of them.
