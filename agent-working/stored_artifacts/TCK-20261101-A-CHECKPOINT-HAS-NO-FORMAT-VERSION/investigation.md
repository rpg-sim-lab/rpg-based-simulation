---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION
artifact_type: investigation
---

# Investigation — checkpoint schema fingerprint

## Probe: save-time recording on a REAL AuthoritativeState (2026-11-16, origin/main 789f0f729, py 3.13.7)
State: `tests/unit/engine/lodging_kernel.kernel([hero(...)], beds=1)` `_state` (entity, building, regions, strategic block). A `pickle.Pickler` subclass whose `reducer_override` notes `type(obj)` for each dataclass instance, returning `NotImplemented`.
- Output bytes equal `pickle.dumps(state, protocol=HIGHEST_PROTOCOL)` (asserted): swapping the writer changes no checkpoint byte.
- Truth set = every `(module, name)` an `Unpickler.find_class` is asked for while loading those bytes (the classes load really needs). 52 dataclasses in the stream; the reducer saw the same 52; missed 0, extra 0.
- Memoised repeats: seen once per first write (the memo short-circuits repeats), the class set is unaffected.
- Enums (11, e.g. Faction, GoalKind, LifeStage, MovementMode): not dataclasses, pickled by name; not listed. A member rename fails at `find_class`; that is a different hazard (see Limits).
- Non-dataclass containers: `collections.deque`, `src.core.state.ReadOnlyDict`; their contents are still walked by the pickler, so dataclasses inside them are seen (the dict-inside case from the toy also holds).
- Custom reduce: slotted dataclasses carry generated `__getstate__/__setstate__` (positional); `reducer_override` runs before them and does not suppress them.
- Non-slotted dataclasses in this payload: 0. The recorder lists any dataclass, slotted or not: a rename or removal on a non-slotted one still changes `__dict__`-by-name loading, so it is cheap to cover and costs a line. Positional shift is the slotted-only hazard; the classifier treats both alike (stricter, simpler).
- Result: no fallback to a type walk; no tests/architecture ask.

Limit: the sample has no `GroupRecord` (no groups) so the probe does not show it. The unit test builds a state with groups, a bound group and a building and asserts classes-met-on-load == header, so the guard is checked against a payload containing them.

## Current restore (src/engine/scenario_checkpoint.py)
`pickle.loads` runs first, then the spec_id check, then `fill_missing_fields`, `check_group_counter`. The header is read before the payload but only `tick` and `spec_id` are used.

## API
`src/api/routes/scenarios.py:99-103`: `FileNotFoundError` -> 404, `ValueError` -> 400 with `detail=str(e)` (a plain string, not shaped). Confirmed. `CheckpointFieldMissingError` and `GroupCounterBehindStoreError` already ride this branch. Only the route calls save/restore (`grep` of src/ and tools/).

## Other facts
- FIELD_RULES rows are keyed by field name and a record selector (a function), not by class; the classifier needs the class, so rows gain a defaulted `record` (class qualname). Shape stays (new defaulted field last).
- `tests/unit/engine/test_checkpoint_fields.py::test_every_rule_field_is_the_last_field...` is the only test pinning append-last. See plan for its disposition.
- No `.ckpt` on this host (planner searched); refusing headerless costs nothing here.

## Limits to state in docs
Enum member renames, changed field *types/defaults*, changed `__post_init__` and a field that keeps its name but changes meaning are NOT detected (names and order only). Truncated file (<4 bytes) raises `struct.error`, not a ValueError; out of scope, noted.
