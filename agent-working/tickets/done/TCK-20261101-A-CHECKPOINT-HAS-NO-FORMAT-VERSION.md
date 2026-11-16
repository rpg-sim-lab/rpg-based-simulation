---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION
phase: done
date: 2026-11-01
tags: []
---

# TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION

## Title
A scenario checkpoint has no format version, so a checkpoint older than a slotted state record's newest field loads without error and fails later on first read.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
rpg-designer asked for this ticket (ruling word for word in TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS): "A checkpoint-format version in the header, refusing an unknown or older version BEFORE unpickling, is its own ticket, P2".

`ScenarioCheckpointer` (`src/engine/scenario_checkpoint.py`) writes a JSON header (`tick`, `spec_id`, `rng_checkpoint`) and a pickle of the whole `AuthoritativeState`. Restore never checks a format. State records are frozen and slotted, and unpickling does not run `__post_init__`, so a field added after the checkpoint was written is an unset slot: no error on load, AttributeError on first read. Shown on a toy dataclass of the same shape, 2026-11-01; not yet on a real checkpoint. Worse, slotted dataclasses unpickle positionally (`zip(fields(self), state)`, `dataclasses._dataclass_setstate`, Python 3.13): a field inserted mid-class takes the next field's old value silently, and every later field shifts. A real case was caught on the group branch (`next_group_id` before `next_item_instance_id`). Until there is a version check, new fields must be appended last. Any field added to a slotted state record has this hazard: `next_group_id` and `contract_holder_id` in the group batch, and, per the designer, F3's `lodged_in` and beds on the u24 rpg side.

Restoring also runs `pickle.loads` on the file, which is outside this ticket's question but is the reason to refuse before unpickling.

## Scope
Raised to P1 and shape lean given by rpg-designer (below); its fifth bullet is withdrawn by ruling (a), 2026-11-16. F3 and the churn fix have landed.
1. A schema fingerprint in the header: the ordered field names of every slotted state record.
2. Restore's accept and refuse rules per the lean, before any value is used.
3. Every check runs on the header before `pickle.loads`. A checkpoint without a fingerprint header is refused with a typed error (rpg-designer ruling (a), 2026-11-16, below). The spec_id check also moves before `pickle.loads` and stays ahead of the fingerprint check, so a checkpoint of another scenario is still refused for that reason (the contract of `test_checkpoint_group_fields.py:224`).
4. FIELD_RULES rows in `src/engine/checkpoint_fields.py` stay the fill step. The field-order pin from the group batch may be retired by this; say whether.
5. A guard that the fingerprint covers every slotted state record: recorded at save from the payload (re-scope below), checked by a unit test.
6. Tests that restore a hand-written checkpoint are re-pointed, never weakened (ruling below).
7. Docs and parity in the same change: `docs/engine/scenario_runtime_contract.md` "Checkpoint Format" (header fields and the refusal rule), the INFRA-215 row in `docs/parity_ledger/infrastructure.yaml`, and the route's client-error shape.

## Out of Scope
- The group batch's own restore step (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS).
- Migrating old checkpoints.
- Replacing pickle.

## Acceptance Criteria
1. An insert, reorder, rename or removal is refused with a typed error before any value is used; fields appended at the end and named in FIELD_RULES are accepted and filled; a checkpoint without a fingerprint header is refused with a typed error before unpickling (test proves pickle.loads is not called) (tests for each).
2. A current checkpoint round-trips byte-equal (test).
3. The API routes report the refusal as a client error, in a shaped response.
4. Docs for the checkpoint format are updated, and the parity entry if one exists.

## Related Tickets
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (found here)
- TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP (`next_group_id`)

## Related Docs
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/engine/scenario_checkpoint.py
- src/api/routes/scenarios.py
- src/core/state.py

## Assumptions / Open Questions
- No checkpoint files found tracked in git or under data/, so refusing old ones is expected to cost nothing; a running service's `checkpoints/` directory was not searched. (2026-11-16: none on the ubuntu host either; see the re-scope.)
- Not dispatched. The F3 ordering is settled (both landed); the remaining questions are in the re-scope below.

### rpg-designer's raise and shape lean
Word for word in TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS ("on the two corrections", point 1). F3 found the same defect: BuildingState.beds inserted before _canonical_cache, moved last with an old-shape test.

### rpg-designer ruling on headerless checkpoints, 2026-11-16 (u24; relayed by lead-planner-u24 and lead-planner). In substance, as relayed:
"Ruling (a): refuse EVERY checkpoint without a fingerprint, with a typed error, before pickle.loads.
Why: no committed .ckpt or checkpoint blob exists (git ls-files), so none is a kept artifact; (b) can't tell an insert from an append, which is the exact hazard (next_group_id, beds); (c) breaks refuse-before-unpickle; (a) is the simplest (6698958617), and its cost (pre-fix checkpoints can't be restored) is acceptable since none is kept.
The lean's 5th bullet ("headerless accepted only if its shape matches") is WITHDRAWN. AC1's last clause becomes: "a checkpoint without a fingerprint header is refused with a typed error before unpickling (test proves pickle.loads is not called)."
Tests, with no weakening. Two tests in tests/unit/engine/test_checkpoint_group_fields.py restore a HEADERLESS old-shape blob through restore(): test_restore_refuses_a_bound_group_checkpoint_before_building_a_kernel (:119) and test_restore_fills_an_old_shape_checkpoint_before_the_kernel_is_built_and_reads_it (:146). RE-POINT both to an old-shape checkpoint WITH a fingerprint header listing the pre-append field order, so the FIELD_RULES fill and the bound-group refusal stay tested through restore(). Don't delete them or turn them into header-refusal tests. The pickle-level tests (:60-:109) are unaffected. ADD a separate headerless-refusal test.
Docs/parity in the same change: scenario_runtime_contract.md "Checkpoint Format" (header fields plus the refusal rule), its INFRA-215 ledger row, and the API route's client-error shape (AC3)."

Planner note (rpg-planner-ubuntu, applying the ruling's no-weakening rule): three more tests write a headerless checkpoint and call restore(), and the ruling did not name them. Each is re-pointed the same way, keeping what it asserts:
- `tests/unit/engine/test_checkpoint_group_fields.py:215`, a pre-F3 checkpoint refused for the missing `beds`. It gets a fingerprint header listing BuildingState without `beds`, so the FIELD_RULES refusal is still reached through restore().
- `:224`, a pre-F3 checkpoint of another scenario raising the spec_id error and not the field error. Same header; the spec check stays first.
- `tests/unit/engine/test_scenario_checkpointer.py:55-73`, the spec_id mismatch on a dummy payload. It gets a valid fingerprint header so it still tests the spec check.
`_write_checkpoint` (`:191`) and the inline header writers at `:124` and `:164` are the places to change; a shared helper that writes an old-shape header is the natural form. The API tests mock restore() and are unaffected. The integration tests save with the real writer and are unaffected.

### rpg-designer on the planner extension, 2026-11-16 (u24; relayed by lead-planner). In substance, as relayed:
"NO objection to extending ruling (a). Re-pointing :215, :224 and test_scenario_checkpointer.py:55-73 to old-shape fingerprint headers, with each assertion kept, is the same rule. The order spec_id check -> fingerprint check -> pickle.loads is right; spec_id is in the JSON header, so moving it ahead tightens before-unpickle. One non-blocking ask: add a test pinning the order, so a headerless checkpoint whose spec_id also mismatches gets the spec_id error."
Taken into scope: that order test is part of item 6.

### File claim, final (2026-11-16, rpg-planner u24 via lead-planner-u24 and lead-planner, checked against origin/main)
This ticket LANDS FIRST; both u24 overlaps rebase onto it. The claimed files may be edited.
1. LIVE, not dispatched: rpg-d80b/rpg-d80c add `observers=()` to `ScenarioCheckpointer.restore(path, spec, ...)`, passed to `Kernel(...)` and `ScenarioRuntimeService(spec, observers=...)`, and the route calls `restore(..., observers=default_observer_factories())`. Keep `restore()`'s signature easy to extend (keyword parameters after `spec`; no positional reshuffle).
2. LIVE, unpushed: rpg-planner-seat-8 (0584db7ee) edits the same INFRA-215 row. Ask: do not rewrite the sentence "reconstructs RNG via DeterministicRNG.set_state()". Add the fingerprint and refusal text as new sentences. If that sentence must change, say so in the PR body so rpg-planner folds its base-seed clause into the new wording.
3. STALE: rpg-sleeper-lodges (squash-merged as #823).

### File claim and overlap (2026-11-16, superseded by the final answer above)
Dispatched to investigate and plan only. No edit to the claimed files until u24's final claim answer arrives via lead-planner. Preliminary answer from lead-planner-u24: u24's D80C branch (rpg-d80c, TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE) is likely live and edits `src/engine/scenario_checkpoint.py` and `src/api/routes/scenarios.py`. Measured by rpg-planner-ubuntu at origin/rpg-d80c 74fcae318 (2026-10-20, 235 commits behind main): 8 added and 3 removed lines over the two files. It adds an `observers` parameter to `restore()`, passes it to `Kernel` and `ScenarioRuntimeService`, and adds one import. rpg-d80b carries the same two-file change. Still being checked by u24: rpg-sleeper-lodges (scenario_checkpoint.py, checkpoint_fields.py; possibly merged) and rpg-planner-seat-8's infrastructure.yaml row. If D80C is live, the plan says which lands first and how small the overlap is in each file.

### Re-scope against main 789f0f729 (rpg-planner-ubuntu, 2026-11-16)
What changed since filing:
- The designer's precondition is met: F3 and the churn fix both landed. FIELD_RULES (`src/engine/checkpoint_fields.py`) now has 9 rows: lodged_in, beds (refuse), cleared_since, next_group_id, the three group fields, and the last_hit pair. Scope item 4: FIELD_RULES stays the fill step, unchanged in shape.
- The field-order "pin" is four comments, not a test: `src/core/state.py:527`, `:1218`, `:1510` and `src/core/group_record.py:47`. Once a fingerprint refuses inserts, appending last stops being a correctness rule and only keeps old checkpoints restorable; those four comments are reworded to say that (they are lines this ticket touches).
- #936 (restore run id) changed the Kernel run_id only; the header and payload are unchanged.
- The hazard is reproduced on the project's Python 3.13.7, still on a toy: a field inserted mid-class takes the next field's saved value and the last field is unset. Not yet shown on a real AuthoritativeState; the tests in AC1 do that.
- No `.ckpt` file exists on the ubuntu host (searched /data/vboxuser/Work and /home/vboxuser). The API writes `checkpoints/<scenario>/<name>.ckpt` under the service cwd. u24's host was not searched.
- The restore route already answers 400 on a ValueError (`GroupCounterBehindStoreError` relies on it), so AC3 needs a typed ValueError subclass and a shaped detail, not a new route branch.

Scope item 5, recommendation: record the fingerprint at save from the payload itself, not from a static walk of type hints. A `pickle.Pickler` subclass whose `reducer_override` notes the type of each dataclass it writes gives exactly the classes in that payload, so the header covers every record by construction. A static walk misses fields typed `Any` or `object`, and a sample-based walk (like `tests/architecture/state_digest_probe.py`) only sees what the sample contains. With save-time recording, the guard is an ordinary unit test (the classes met on load equal the header's) and nothing goes to tests/architecture, so no ask to testing-planner. On 3.13.7 it saw nested slotted frozen dataclasses, including one inside a dict (toy, 2026-11-16; not yet on a real state, where memoised repeats and custom `__reduce__` methods need checking). If it misses any on a real state, fall back to the type walk and send the ask.

Scope item 3, the headerless (today's) checkpoint. RESOLVED 2026-11-16: rpg-designer chose (a), recorded above. A fingerprint is compared from the header alone. A checkpoint with no fingerprint can only be judged from its payload. Options:
- (a) Refuse every checkpoint without a fingerprint, before unpickling, with a typed error saying to re-create it on a current build. Simplest, and fully before-unpickle. It departs from the lean's fifth bullet. Costs nothing on this host (no checkpoints).
- (b) Read the payload's opcodes with `pickletools.genops`, which does not run the pickle, and accept only if each class's saved field count equals the pre-fingerprint schema (main's shape when this lands); otherwise refuse. Keeps the lean and stays before-unpickle. Limit: a count cannot tell an insert from an append, so it accepts only an exact-count match and fills nothing. Memo references make the scan more code than (a).
- (c) Unpickle and then compare. Rejected: it runs `pickle.loads` on a file of unknown shape, which the first ruling asked to avoid.
Recommendation: (a), because no checkpoint exists to keep and (b)'s check is weaker than its wording suggests. This needs rpg-designer's yes, since it changes a bullet of the lean. If the answer is (b), AC1's third clause stands as written; if (a), it reads "a checkpoint without a fingerprint is refused before unpickling (test)".

Out of scope still: non-slotted dataclasses unpickle by name, so they cannot shift. The fingerprint may still list them for renames and removals; the implementer says which.

Before dispatch: ask u24 (lead to lead) whether its F3-checkpoint restore-randoms branch touches `scenario_checkpoint.py` (it is not on origin here), and claim the files on #634. Dispatch is standard tier, owner go needed.
- 2026-11-16, lead-planner: lead-planner-u24 says u24's F3-checkpoint fix (rpg-checkpoint-restore-randoms d690c808a, unpushed) does edit `src/engine/scenario_checkpoint.py`. lead-planner proposed that F3-checkpoint lands first (a HARD repair before the M1-base record) and this ticket rebases after it. Hold the #634 claim and the dispatch ask until u24 answers.
- 2026-11-16, correction (u24, verified by lead-planner and by rpg-planner-ubuntu): the F3-checkpoint fix (restore draws from seed 0) is already on main by #848 (66d08dd56, TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0, in done/); origin/main `src/engine/scenario_checkpoint.py:94` is `DeterministicRNG(base_seed=state.seed)`. u24's d690c808a is a duplicate. Nothing to order behind. This ticket now waits only on rpg-designer's (a)/(b)/(c) ruling on headerless checkpoints (relayed by u24), then the #634 claim and the owner dispatch ask.

### Rulings recorded during implementation (2026-11-16; rpg-planner-ubuntu relaying rpg-designer u24, in substance)
- Retiring the append-last position asserts is NOT a weakening, on conditions: (1) the refusal test covers insert, reorder, rename AND removal as four separate cases, each asserting the typed error and that `pickle.loads` is never called; (2) "FIELD_RULES covers lodged_in and beds" survives, and a fingerprinted checkpoint missing an appended field with NO row is refused through `restore()`; (3) the `cleared_since` last-field assert in the project-restore test may go, the restore half stays.
- Divergence 2.160, class Hardened (re-checked at merge; main's highest was 2.157).
- Finding: `CombatComponent.last_hit_attackers` and `last_hit_damages` are declared before `_canonical_cache` (#933), so a checkpoint lacking them is an INSERT, not an append. Between #933 and this ticket a headerless pre-#933 checkpoint would have unpickled shifted on main (the pair taking the old cache slot); no checkpoint exists on this host or in git. rpg-designer ruled: DELETE the two last_hit FIELD_RULES rows and their fill functions, no by-name exemption, field order stays; KEEP the test that a pre-#933-shaped header is refused as an insert, the limits line and the PR-body disclosure. Divergence 2.148 Disclosed item (2) is rewritten to match.

## Implementation Notes
- New `src/engine/checkpoint_schema.py`: `_SchemaPickler` (reducer_override notes each dataclass; output bytes equal `pickle.dumps`), `dump_with_schema`, `read_header`, `check_schema`, and `CheckpointSchemaError(ValueError)` with `CheckpointHeaderError`, `CheckpointSchemaMissingError`, `CheckpointSchemaMismatchError` (`to_detail()` is the route's 400 body). Classes are resolved only under `src`.
- `ScenarioCheckpointer.save` writes `schema` into the header; `restore` order is now header, spec_id, schema, `pickle.loads`, fill, counter check. Signature unchanged (keyword parameters go after `spec`).
- `FieldRule` gained a defaulted `record` (class qualname); every row sets it. The two last_hit rows and their fill functions are removed (ruling above).
- Route: `except CheckpointSchemaError` ahead of `ValueError`, 400 with the shaped detail.
- Field-order comments reworded in `src/core/state.py` (3), `src/core/group_record.py` (1), `src/engine/checkpoint_fields.py` (docstring and trailing comment). `CombatComponent` untouched.
- Docs: `scenario_runtime_contract.md` "Checkpoint Format", INFRA-215 (sentences added; the set_state() sentence untouched, only the closing `convenience.` line now continues and `v2_evidence` lists checkpoint_schema.py), divergence 2.160 (new) and 2.148 Disclosed (2) (rewritten).
- `tests/unit/tools/test_mechanism_registry_completeness_check.py` pins moved with the new src file: scope_files 369 -> 370, unbound_files 262 -> 263.

## Test Summary
Unit: `tests/unit/engine/test_checkpoint_schema.py` (new), `test_checkpoint_group_fields.py`, `test_checkpoint_fields.py`, `test_scenario_checkpointer.py`, `test_group_hit_records_every_attacker.py`, `tests/unit/social/test_group_id_allocation.py`, `tests/unit/tools/test_mechanism_registry_completeness_check.py`, `tests/api/test_scenario_runtime_api.py`, `tests/tools/test_generate_registry.py`, `tests/tools/test_agent_working_paths_guard.py`: 207 passed. Real-writer: `tests/unit/engine/test_scenario_checkpointer.py` + `tests/integration/scenarios/test_scenario_runtime_service.py` under the 3G/cores 4-5 cap, PYTHONHASHSEED=0: 34 passed (54 s).

## Files Changed
See the branch diff against origin/main.

## Completion Summary
Checkpoints now carry a schema fingerprint and are refused, typed and before `pickle.loads`, unless it matches (an append named in FIELD_RULES is filled). Headerless checkpoints, insert/reorder/rename/removal and unreadable headers answer 400 with a shaped detail.
- Removed position asserts and their replacements: `test_checkpoint_fields.py` `test_every_rule_field_is_the_last_field_of_its_record...` (:33 `lodged_in` last, :34 `beds` last) replaced by `test_lodged_in_and_beds_have_field_rules_naming_their_record` plus the four refusal cases (insert, reorder, rename, removal) and `test_every_field_rule_names_a_record_and_a_real_field_of_it` in `test_checkpoint_schema.py`; the `cleared_since` last-field assert (:94) is dropped, the restore half stays.
- Deleted test: `test_group_hit_records_every_attacker.py::test_a_checkpoint_that_predates_the_record_restores_one_attacker_holding_the_whole_blow` (it exercised the deleted last_hit rows); replaced by `test_a_pre_933_shaped_combat_header_is_refused_as_an_insert`.
- Re-pointed, assertions unchanged: `test_checkpoint_group_fields.py` (:119, :146, :215, :224) and `test_scenario_checkpointer.py` (:55-73), through `tests/unit/engine/checkpoint_helpers.py`.
- Disclosure: between #933 and this ticket a headerless pre-#933 checkpoint would have unpickled shifted on main (`CombatComponent.last_hit_attackers`/`last_hit_damages` take the old cache slot). No checkpoint exists on the ubuntu host or in git.
- Not measured: hot-loop timing (save now runs a Python-level `reducer_override` per object; perf pause #715 6556861718). Not run: any simulation beyond the short checkpoint round-trip tests.
