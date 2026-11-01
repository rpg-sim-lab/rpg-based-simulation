---
status: active
layer: engine
authority: P2
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
P2

## Request Summary
rpg-designer asked for this ticket (ruling word for word in TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS): "A checkpoint-format version in the header, refusing an unknown or older version BEFORE unpickling, is its own ticket, P2".

`ScenarioCheckpointer` (`src/engine/scenario_checkpoint.py`) writes a JSON header (`tick`, `spec_id`, `rng_checkpoint`) and a pickle of the whole `AuthoritativeState`. Restore never checks a format. State records are frozen and slotted, and unpickling does not run `__post_init__`, so a field added after the checkpoint was written is an unset slot: no error on load, AttributeError on first read. Shown on a toy dataclass of the same shape, 2026-11-01; not yet on a real checkpoint. Any field added to a slotted state record has this hazard: `next_group_id` and `contract_holder_id` in the group batch, and, per the designer, F3's `lodged_in` and beds on the u24 rpg side.

Restoring also runs `pickle.loads` on the file, which is outside this ticket's question but is the reason to refuse before unpickling.

## Scope
1. A format version in the header, written on save.
2. Restore reads the header and refuses an unknown, older or absent version with a typed error, before unpickling.
3. Say how the version is bumped when a slotted state record gains a field, and how that is enforced, if it can be, by a check proportionate to the risk.
4. How the post-unpickle step from the group batch relates to this: a version check may retire it.

## Out of Scope
- The group batch's own restore step (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS).
- Migrating old checkpoints.
- Replacing pickle.

## Acceptance Criteria
1. A checkpoint with an older, unknown or absent version is refused with a typed error, and the pickle is not loaded (test).
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

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
