---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION

## Title
A scenario checkpoint has no format version, so a checkpoint older than a slotted state record's newest field loads without error and fails later on first read.

## Status
OPEN

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
Raised to P1 and shape lean given by rpg-designer (below). Lands soon after the second of F3 and the churn fix; blocks neither.
1. A schema fingerprint in the header: the ordered field names of every slotted state record.
2. Restore's accept and refuse rules per the lean, before any value is used.
3. Whether the header check can run before unpickling, which the first ruling asked for: comparing a fingerprint needs only the header, but a headerless checkpoint's shape can only be judged from its pickle. Say how.
4. FIELD_RULES rows in `src/engine/checkpoint_fields.py` stay the fill step. The field-order pin from the group batch may be retired by this; say whether.
5. A guard that the fingerprint covers every slotted state record. If it belongs in tests/architecture, ask testing-planner.

## Out of Scope
- The group batch's own restore step (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS).
- Migrating old checkpoints.
- Replacing pickle.

## Acceptance Criteria
1. An insert, reorder, rename or removal is refused with a typed error before any value is used; fields appended at the end and named in FIELD_RULES are accepted and filled; a headerless checkpoint is accepted only if its shape matches the pre-fingerprint schema (tests for each).
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

### Re-scope against main 789f0f729 (rpg-planner-ubuntu, 2026-11-16)
What changed since filing:
- The designer's precondition is met: F3 and the churn fix both landed. FIELD_RULES (`src/engine/checkpoint_fields.py`) now has 9 rows: lodged_in, beds (refuse), cleared_since, next_group_id, the three group fields, and the last_hit pair. Scope item 4: FIELD_RULES stays the fill step, unchanged in shape.
- The field-order "pin" is four comments, not a test: `src/core/state.py:527`, `:1218`, `:1510` and `src/core/group_record.py:47`. Once a fingerprint refuses inserts, appending last stops being a correctness rule and only keeps old checkpoints restorable; those four comments are reworded to say that (they are lines this ticket touches).
- #936 (restore run id) changed the Kernel run_id only; the header and payload are unchanged.
- The hazard is reproduced on the project's Python 3.13.7, still on a toy: a field inserted mid-class takes the next field's saved value and the last field is unset. Not yet shown on a real AuthoritativeState; the tests in AC1 do that.
- No `.ckpt` file exists on the ubuntu host (searched /data/vboxuser/Work and /home/vboxuser). The API writes `checkpoints/<scenario>/<name>.ckpt` under the service cwd. u24's host was not searched.
- The restore route already answers 400 on a ValueError (`GroupCounterBehindStoreError` relies on it), so AC3 needs a typed ValueError subclass and a shaped detail, not a new route branch.

Scope item 5, recommendation: record the fingerprint at save from the payload itself, not from a static walk of type hints. A `pickle.Pickler` subclass whose `reducer_override` notes the type of each dataclass it writes gives exactly the classes in that payload, so the header covers every record by construction. A static walk misses fields typed `Any` or `object`, and a sample-based walk (like `tests/architecture/state_digest_probe.py`) only sees what the sample contains. With save-time recording, the guard is an ordinary unit test (the classes met on load equal the header's) and nothing goes to tests/architecture, so no ask to testing-planner. On 3.13.7 it saw nested slotted frozen dataclasses, including one inside a dict (toy, 2026-11-16; not yet on a real state, where memoised repeats and custom `__reduce__` methods need checking). If it misses any on a real state, fall back to the type walk and send the ask.

Scope item 3, the headerless (today's) checkpoint, needs a choice. A fingerprint is compared from the header alone. A checkpoint with no fingerprint can only be judged from its payload. Options:
- (a) Refuse every checkpoint without a fingerprint, before unpickling, with a typed error saying to re-create it on a current build. Simplest, and fully before-unpickle. It departs from the lean's fifth bullet. Costs nothing on this host (no checkpoints).
- (b) Read the payload's opcodes with `pickletools.genops`, which does not run the pickle, and accept only if each class's saved field count equals the pre-fingerprint schema (main's shape when this lands); otherwise refuse. Keeps the lean and stays before-unpickle. Limit: a count cannot tell an insert from an append, so it accepts only an exact-count match and fills nothing. Memo references make the scan more code than (a).
- (c) Unpickle and then compare. Rejected: it runs `pickle.loads` on a file of unknown shape, which the first ruling asked to avoid.
Recommendation: (a), because no checkpoint exists to keep and (b)'s check is weaker than its wording suggests. This needs rpg-designer's yes, since it changes a bullet of the lean. If the answer is (b), AC1's third clause stands as written; if (a), it reads "a checkpoint without a fingerprint is refused before unpickling (test)".

Out of scope still: non-slotted dataclasses unpickle by name, so they cannot shift. The fingerprint may still list them for renames and removals; the implementer says which.

Before dispatch: ask u24 (lead to lead) whether its F3-checkpoint restore-randoms branch touches `scenario_checkpoint.py` (it is not on origin here), and claim the files on #634. Dispatch is standard tier, owner go needed.
- 2026-11-16, lead-planner: lead-planner-u24 says u24's F3-checkpoint fix (rpg-checkpoint-restore-randoms d690c808a, unpushed) does edit `src/engine/scenario_checkpoint.py`. lead-planner proposed that F3-checkpoint lands first (a HARD repair before the M1-base record) and this ticket rebases after it. Hold the #634 claim and the dispatch ask until u24 answers.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
