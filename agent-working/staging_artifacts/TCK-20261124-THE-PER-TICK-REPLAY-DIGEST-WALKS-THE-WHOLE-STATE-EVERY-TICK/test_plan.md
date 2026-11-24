---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK
date: 2026-11-24
tags: []
---

# Test plan

All new tests are in one module, tests/unit/engine/test_canonical_digest_equals_reference.py. No heavy run in the test suite: states come from short kernel runs (under 300 ticks) and hand-built states.

## AC1: old-vs-new equality (the reference is the current build, kept verbatim in the test)
| id | case | assertion |
|---|---|---|
| E1 | `frontier_living_world` s42, ticks 1 to 120, EVERY tick, audit_mode on | digest, compact JSON, pretty JSON and the data dict equal the reference, on a warm state and again after clearing every `_canonical_cache` |
| E2 | a second world (the movement or resource scenario already used by test_proof_digest_contract, plus one more real world) every tick for a short run | same |
| E3 | non-audit path (FULL richness policy and `reason="certification"`) | same, through `CanonicalHashScheduler.compute_digest` |
| E4 | partial dirty set, `force_full_scan` on and off | same digests (the hasher ignores the dirty set; the test pins it) |
| E5 | spawn and death: ticks where an entity appears or is removed; a corpse added | same |
| E6 | collection insert and delete (ground item, chest, group, faction, quest record) on a hand-built state | same |
| E7 | a strategic component with every container filled (projects, directives, blockers, leads, concerns, zones, hypotheses, trust, contracts, turning points, intentions, beliefs, marriages) and a social component with bonds and betrayal records | memoized component dict equals the old inline dict by value and by dump |
| E8 | encoder-sensitive values (float exponent forms, -0.0, NaN, non-ASCII, IntEnum and str-Enum values and keys, tuple values) inside a state's canonical data | digest equal to the reference (the dump call itself is unchanged in Stage 1; this pins the output) |
| E9 | PLANTED in-place mutation: after hashing, mutate the memoized strategic dict in place | the existing `audit_cached_canonical_dicts` reports the mismatch (as the existing poison test does for any cached holder); and the hasher's digest equals the reference (in Stage 1 the memo is the dict, so both see the mutation). If Stage 2 is approved: the fragment is invalidated by identity and the audit extended to compare the fragment with `json.dumps` of the memo |
| E10 | a replaced strategic component (same values, new object) | memo empty on the new object, digest unchanged |

## Mutation proofs (each reverted afterwards, failing test names reported)
M1: drop one key from the memoized strategic dict. M2: make the memo return a stale dict after the component is replaced (copy the memo to the new object). M3: sort one inner dict in the wrong order. M4: change `social` bonds key conversion. Each must fail E1/E7/E10.

## AC3 and regression runs (before and after, must be equal)
tests/unit/engine/test_kernel_digest_via_scheduler.py, test_hash_scheduler.py, test_proof_digest_contract.py, test_checkpoint_fields.py, test_checkpoint_schema.py; tests/unit/kernel/test_replay_pressure.py, test_replay_overflow.py; tests/unit/core/test_operational_flags.py, test_entity_integrity.py; tests/unit/perf/test_profile_tick_contract.py; tests/architecture/test_state_digest_covers_every_field.py; tests/perf/test_dirty_set_integrity.py, test_dirty_parity.py; tests/integration/kernel (determinism, replay fidelity, checkpoint reproducibility); tests/tools/test_hash_callsite_inventory.py; the pre-push set (tests/tools, tests/static, tests/architecture) once at the end.

## AC2 (not in the suite; under a lead GO later)
Two arms, merge base and branch, `frontier_living_world` s42, 2000 ticks, replay on, audit_mode, fresh git-archive trees, record set: per-chunk sha256 of every chunk_*.json and the final hash equal. The perf reference c12afb16a10d is context only.

## AC5
perf-planner measures before and after with its own GO; this ticket reports.

## ADDENDUM: tests added by the conditions
| id | case | assertion |
|---|---|---|
| E11 | a caller mutates the returned canonical dict (pop a key, or assign a key, in the memoized strategic or social dict, or in a dict reachable from it) | `audit_cached_canonical_dicts` reports the mismatch (as it does for the existing poison test), and the test shows the digest of the mutated state differs from a cleared-memo recompute |
| E12 | pin: the replay form and the fingerprint of a state are byte-equal before and after the change | `StateFingerprinter.get_fingerprint` and the TICK_END payload equal the reference |
| E13 | pin (option B only): the pickle of a state differs from the reference only by the appended slot; an old checkpoint (without the slot) restores through the new FIELD_RULES rows and hashes equal | checkpoint_schema and checkpoint_fields tests updated |
| E14 | pin (option A only): the memo is bounded by the live component count after a digest; entries for replaced components are gone; it holds no component after the entity is removed | size equals live components |
| E15 | `dataclasses.replace` of a component whose memo is populated gives a component with memo None (option B), or a new key with no entry (option A) | equal digest |

Worlds for AC1: `frontier_living_world` and `crowded_frontier` (bonds on 293 and 287 of 300 ticks; trust_history on 68 and 181 ticks); betrayal, nemesis and marriage are hand-built only (no world produced one in 300 ticks).
