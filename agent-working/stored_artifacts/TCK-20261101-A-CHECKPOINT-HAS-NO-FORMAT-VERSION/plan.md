---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION
artifact_type: plan
---

# Plan — TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION

Phase 1 plan; no code written. Items map to the dispatch's numbered list.

## 1. Fingerprint recorded at save, from the payload
New `src/engine/checkpoint_schema.py`: `_SchemaPickler(pickle.Pickler)` with `reducer_override` noting each dataclass type; `dump_with_schema(state) -> (payload_bytes, schema)`. `save()` uses it in place of `pickle.dumps`. Verified byte-identical on a real state (investigation.md). Lists slotted and non-slotted dataclasses alike.

## 2. Header shape and classification
Header gains `"schema": {"<module>.<qualname>": ["field", ...]}` (insertion order = first-write order; fields = `dataclasses.fields(cls)` names in order, including `init=False`). No separate integer version: the fingerprint is the version, and an integer would need a bump discipline this removes. (Say so if you want one.)

Per class in the header, saved S vs current C (class resolved by name; only `src.` modules are imported, nothing else, so a hostile header cannot import arbitrary modules):
- S == C: exact, accept.
- C == S + tail, and every tail field has a FIELD_RULES row whose `record` is this class: append, accept (fill later).
- C == S + tail, some tail field has no row: refuse (`appended field without a fill rule`).
- Anything else: refuse, named by kind: reordered (same set), inserted (extra current field not at the end), removed-or-renamed (a saved name absent now; names alone cannot tell the two).
- Class not importable / not a dataclass now: refuse (`removed or renamed class`).
- Class in current code but absent from the header: fine (cannot occur in that payload).

## 3. restore() order
open, read header -> spec_id check -> schema present? -> schema compare -> read payload -> `pickle.loads` -> `fill_missing_fields` -> `check_group_counter` -> rest unchanged. The spec check moves ahead of loads and stays ahead of the schema check (rpg-designer's order test).

## 4. Typed errors (all in checkpoint_schema.py, base `CheckpointSchemaError(ValueError)`)
`CheckpointSchemaMissingError` (no `schema` key; message: re-create on a current build) and `CheckpointSchemaMismatchError` (carries `classes`: list of `{class, change, saved, current}`). Test proves `pickle.loads` is never called (monkeypatch `pickle.loads` in the module to raise).

## 5. Tests re-pointed, not weakened
Shared helper `tests/unit/engine/checkpoint_helpers.py::write_checkpoint(path, blob, spec_id, schema)`, and `old_shape_schema(state, drop={cls: [fields]})` = current schema from the recorder minus the dropped trailing fields. Sites: test_checkpoint_group_fields.py :119, :146, :215, :224 and `_write_checkpoint` (:191) and the inline writers; test_scenario_checkpointer.py :55-73 (schema `{}` for its `{"dummy": True}` payload). Each keeps its exact assertion. Pickle-level :60-:109 untouched.
Disposition of the append-last pin (`test_every_rule_field_is_the_last_field...` in test_checkpoint_fields.py): the fingerprint now refuses an insert, so "must be last" is no longer a correctness rule, only a restorability rule. RECOMMEND retiring that test and replacing it with `every row's (record, field) is a real field of that class` plus the new insert-refused test; it is not weakened in effect (the hazard it guarded is now refused). Retirement needs your OK; otherwise I keep it as is.

## 6. API
Route adds `except CheckpointSchemaError as e: 400, detail=e.to_detail()` ahead of the generic ValueError: `{"error": "checkpoint_schema", "reason": "missing"|"mismatch", "message": str, "classes": [...]}`. Other ValueErrors stay a string. Tests extend the existing route tests (restore mocked to raise).

## 7. Docs and parity
- scenario_runtime_contract.md "Checkpoint Format": header line gains `schema`; Behaviour bullets for missing/mismatch refusal and the order; limits line (enum renames, types/defaults not covered).
- INFRA-215: ADD sentences only (header `schema`, refusals before unpickle, 400 shape). The sentence "reconstructs RNG via DeterministicRNG.set_state()" is NOT touched.
- Four comments (state.py:527, :1218, :1510, group_record.py:47) reworded: appending last keeps old checkpoints restorable (fill rule needed); an insert is refused by the schema check. Why/constraint/pointer only. Also the `checkpoint_fields.py` docstring ("no format version") and its trailing comment, which are false after this.
- Divergence entry: needed? Behaviour change (headerless checkpoints now refused). Proposing one `Hardened` entry with the unit test as Verification; tell me if the planner holds a number.

## 8. Signature
`restore(path, spec)` unchanged; parameters added later go keyword-only after `spec` (`*, observers=()` lands cleanly). Internals split into `_read_header` and `_read_state` helpers so D80C's edit stays inside `restore`'s Kernel construction.

## Commits and process
Ticket in inprogress/ (moved). Each commit: regenerate docs/REGISTRY.yaml, stage monitoring shards. Run entry + events via record_hand_orchestrated_closure at close. No push. Unit tests only.
