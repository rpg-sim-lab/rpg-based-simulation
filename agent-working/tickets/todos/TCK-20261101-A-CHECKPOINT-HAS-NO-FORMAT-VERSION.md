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
- No checkpoint files found tracked in git or under data/, so refusing old ones is expected to cost nothing; a running service's `checkpoints/` directory was not searched.
- Not dispatched. Order against the u24 side's F3 fields to be agreed with rpg-planner.

### rpg-designer's raise and shape lean
Word for word in TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS ("on the two corrections", point 1). F3 found the same defect: BuildingState.beds inserted before _canonical_cache, moved last with an old-shape test.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
