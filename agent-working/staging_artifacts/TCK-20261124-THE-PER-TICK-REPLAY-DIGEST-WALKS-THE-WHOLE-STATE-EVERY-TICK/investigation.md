---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK
date: 2026-11-24
tags: []
---

# Investigation: where the per-tick replay digest spends its time, and what may be cached

Author: rpg-implementer-ubuntu. Tree: origin/main cef537d29. Method: a real `frontier_living_world` s42 kernel (`tools/test_architecture/rpg_gate_run.build_kernel`, audit_mode on, so the replay digest is taken every tick), ticks 1 to 300, on a loaded VM, `systemd-run -p MemoryMax=3G`, one process, cpus not pinned (nothing heavy; the numbers are SHARES, not absolute speeds, as perf's own 74.3 ms at tick 2000 is provisional too). Probe scripts are in the session scratchpad only; run dirs were removed by run id.

## (a) Where `get_hash` time goes
`get_hash` = `to_canonical_data` (dict build) + `json.dumps(sort_keys=True, separators=(",", ":"))` + `sha256`. Timed in place, inside the kernel's own call, on the cold state of each tick:

| tick window | to_canonical_data | json.dumps | sha256 | JSON size |
|---|---|---|---|---|
| 1 to 50 | 5.5 ms | 5.7 ms | 0.5 ms | 378 KB (tick 5) |
| 250 to 300 | 10.5 ms | 9.4 ms | 0.5 ms | 656 KB (tick 300) |

So per tick: data build about 51 %, dumps about 47 %, sha about 3 % (the sha is not worth touching). Both grow with the state (JSON +73 % over 300 ticks, cost about x2).
- 89 % of the JSON bytes are the 55 entities (556 KB of 626 KB); then town_tiles 25 KB, groups 12 KB, recent_world_events 8 KB, regions 7 KB, factions 7 KB.
- A WARM `to_canonical_data` (all memos filled) takes 1.0 ms. The 10 ms in the run is therefore COLD rebuild work: **every one of the 55 entity objects is a new object every tick** (identity unchanged in 0 of 55 entities on each of 60 sampled ticks; min and mean both 0.0), so each entity's own `_canonical_cache` memo misses every tick. Of the components of those replaced entities, 71.7 % are the SAME objects as last tick (their component memos hit).
- cProfile of the cold build (ticks 250 to 300): `dataclasses.asdict` / `_asdict_inner` (with its `deepcopy`) is the biggest cost (about 590 k inner calls and 55 k `asdict` calls over 50 ticks, about 1100 per tick). It comes from `EntityState.to_canonical_dict` (src/core/state.py:925), which builds the `strategic` and `social` blocks INLINE, with `asdict(v)` per project, lead, concern, directive, hypothesis, belief and so on, not through a component method with its own memo.
- Direct timing, tick 300, entity memo cleared but every component memo warm: re-assembling all 55 entity dicts costs 8.2 ms; of that the strategic block alone costs 4.9 ms and the social block 0.2 ms. Every other component (`interaction`, `identity`, `attributes`, `inventory`, `combat`, `biological`, `lifecycle`, `navigation`, `self_model`, `cognition`) already memoizes its own `to_canonical_dict`.
- `json.dumps` with `sort_keys=False` takes 6.5 ms against 8.4 ms sorted at tick 250: the second sort is about a quarter of the dumps, not the main cost; the encode of 650 KB is.

## (b) Dirty-set coverage: it cannot be used for this
- `DirtySet` (src/core/dirty.py) is derived from a tick's `StateUpdate` and is meant to filter pipeline domains (movement, groups, shop...). `CanonicalStateHasher.get_hash(state)` takes only the state; the dirty set is not reachable from it except via `state._apply_time_dirty_set`.
- It has no discriminating power for entities: on 39 sampled ticks all 55 entities were replaced AND all 55 were in the apply-time dirty set every tick.
- Coverage of the hasher's input is incomplete: `DirtySet` has fields only for entities, groups, regions, resource nodes, buildings, chests, ground items, corpses and camps. It has none for `places`, `local_scars`, `home_storage`, `owed`, `factions`, `clans`, `information_providers`, `item_instances`, `quest_registry`, `recent_world_events`, `region_loyalty_pressure`, `region_culture_states`, `entity_legend_facts`, `information_source_profiles`, `entity_belief_institutions`, `event_fidelity`, `global_resources`, `blocked_tiles`, `town_tiles`, `building_tiles`, `rng_checkpoint` or the scalars.
- Observed leak (not just a gap): over the 39 sampled ticks `up to 4 `factions` entries were replaced in a single tick and `DirtySet` has no faction field to record them, and a `corpses` entry changed without being in `corpse_ids` on at least one tick (max 1).
- `AuthoritativeState.validate_dirty_set` (audit only, state.py:1593, called at apply.py:608) raises `DirtySetLeakError` only for entities, resource nodes, buildings, regions and groups (identity `is not` against the prior state). It does not check corpses, ground items, chests, camps or any other keyed collection the hasher reads.
**Conclusion: coverage cannot be shown, so the plan does not use the dirty set** (ticket Assumptions: "if it can't be shown, the design must not rely on the dirty set").

## (c) What the output depends on in `json.dumps`
Census of the canonical data of the run above (`to_canonical_data` result, tick 300): str 7687, int 7408, float 4698 (2885 integral, e.g. `1.0`), tuple 410, list 1537, bool 709, None 1768, plus Enum MEMBERS as values: EntityRole 55 and Faction 57 (both `IntEnum`), GoalKind, ObjectiveKind, ObjectiveStatus, DirectivePriority, ConcernKind, RiskLevel, RelationshipRole, LeadCertainty, ReasonCode, ProjectKind, BlockerKind (str mixins). Dict key types: str 29700, plus Enum keys ProjectKind (3) and GoalKind (1) (str mixins). Not seen in this sample, but not excluded: NaN or infinite floats, ints beyond 2^53, int or tuple dict keys (the hasher string-converts the keys it builds, but `_plain`, `asdict` and `dict(sorted(...))` pass keys through), exponent-form floats; 3 non-ASCII strings occur (so `ensure_ascii` escaping matters).
Behaviours the output depends on and a replacement encoder must reproduce exactly:
- float: `float.__repr__` (`1.0`, `1e-05`, `1e+16`, `-0.0`); NaN / Infinity print as `NaN`, `Infinity`, `-Infinity` (`allow_nan=True`).
- int-mixin Enum: printed as the integer (`int.__repr__`), so EntityRole and Faction print as digits; str-mixin Enum: printed as the str value, also as a dict key.
- tuple prints as a list; bool as `true`/`false`; None as `null`.
- `ensure_ascii=True`: every non-ASCII character is `\uXXXX`, including surrogate pairs.
- `sort_keys=True` sorts the ORIGINAL keys before coercion (mixed key types raise `TypeError`); for str keys that is code-point order, so entity ids are ordered as STRINGS (`"10"` before `"2"`).
- separators `(",", ":")`, no spaces.
- A different encoder (for example orjson) differs on float exponent text, Enum and key handling, NaN and big ints: not acceptable without a wrapper that re-proves all of the above.

## (d) Every caller
- `CanonicalHashScheduler.compute_digest` / `get_hash`: src/engine/kernel.py:1113 (`_phase_persistence`, reason "replay"), kernel.py:1184 (final hash at shutdown), src/certification/harness.py:238 (certification evidence).
- `CanonicalStateHasher.get_hash` direct: src/worldbuilding/compiler.py:932 (world build hash); tools/rpg_measure/{arm_child.py:127,138, person_attack_spy.py:511, subject_trace_spy.py:272} (final hash of a measurement run).
- `to_canonical_data` direct: src/certification/harness.py:254 (written PRETTY with `indent=2`, a different dump of the same data); `to_canonical_json(pretty=True)` uses `json.dumps(sort_keys=True, indent=2)`. These two outputs (the pretty one) must not change either.
- Tests: 76 test files mention `CanonicalStateHasher`, `to_canonical_json`, `to_canonical_data`, `compute_digest` or `compute_hash`; those that compare dicts depend on `to_canonical_data` returning the same dicts, so the plan keeps `to_canonical_data` and every component `to_canonical_dict` result unchanged (equal by value).
- `tests/architecture/state_digest_probe.py` and `tests/unit/engine/test_proof_digest_contract.py` (audit of cached canonical dicts, with a "guard the guard" in-place poison test) already audit every object holding a `_canonical_cache`, found by walking dataclass fields; a new memo with the same attribute name is covered by both without change.
- `tools/perf/hash_callsite_inventory.py` and docs/performance/hash_callsite_inventory.{md,json} list the call sites; a check test pins them (tests/tools/test_hash_callsite_inventory.py), so adding or moving a call site changes them.

## Other findings the plan relies on
- Every record that appears in the canonical data already has an object-identity memo named `_canonical_cache` (built lazily, rebuilt when the object is replaced, set to None by apply.py:726, 761, 799 for the hand-copied identity component and in `__post_init__` at state.py:1032). The project's invariant is "a memo is never mutated in place"; `test_proof_digest_contract.py` enforces it by recompute.
- A grep of src for in-place writes into `.strategic.*` / `.social.*` containers (`[k] =`, `.append`, `.update`, `.pop`, ...) finds none, so a memo on those two components is as safe as the memos the other components already carry.
- Entities, components and records are `@dataclass(frozen=True, slots=True)`: no `__weakref__`, so an external weak-keyed cache is not possible; any cache must be a slot on the object (the existing pattern) or an `id()`-keyed table that holds a strong reference.
- Prior art: TCK-20260514-PERSISTENCE-OPT (working_log) says component-level caching took the hasher from about 200 ms to under 1 ms on the then-small state; the component memos in use today are that design. The remaining cold cost is the inline `strategic` / `social` assembly and the monolithic `json.dumps`.
