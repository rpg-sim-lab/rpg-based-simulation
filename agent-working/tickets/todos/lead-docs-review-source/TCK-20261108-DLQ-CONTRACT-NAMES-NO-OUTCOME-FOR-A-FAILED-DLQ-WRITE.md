---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261108-DLQ-CONTRACT-NAMES-NO-OUTCOME-FOR-A-FAILED-DLQ-WRITE
phase: open
date: 2026-11-08
tags: [documentation, observability]
---

# TCK-20261108-DLQ-CONTRACT-NAMES-NO-OUTCOME-FOR-A-FAILED-DLQ-WRITE

## Title
The observability hot-path contract says an exhausted message is routed to the DLQ and ACKed, but names no outcome when the DLQ write fails or the source entry is gone

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
This is batch A (lead part) of `agent-working/lead/docs_as_review_source_plan.md` rev 3.2, approved on 2026-11-08 (#715 comment 6720445592).

`docs/architecture/observability_hot_path_safety_contract.md:124` and `:143` say an exhausted message is "routed to the DLQ and ACKed". The contract is silent on two cases:
- a failed DLQ write. Today the code ACKs anyway (`src/observability/stream/consumer.py:157-164`): that's defect TCK-20261107-AN-EXHAUSTED-STREAM-MESSAGE-IS-ACKED-WHEN-ITS-DLQ-WRITE-FAILS;
- a source entry that can no longer be read.

Per the plan, the normative doc states the intent and is never edited to match the defective code.

rpg-planner-ubuntu, the src owner of the fix, gave the intended behaviour on 2026-11-08:
- a failed DLQ write is not ACKed; it stays in the PEL and the next reclaim sweep retries;
- the failure is logged at error level and counted on the consumer;
- there is no bounded give-up;
- if the source entry is gone, the consumer writes a DLQ tombstone and ACKs only if that write succeeds.

The code fix ships in rpg's PR on branch rpg-ubuntu-review-defect-fixes.

## Scope
- `:124`: the exhausted-message row says the ACK happens only after a successful DLQ write.
- Two new failure-table rows: one for a failed DLQ write, one for a source entry that is gone (the tombstone).
- `:143`: says the same, pointing to the table.

## Out of Scope
- The code fix, which is rpg's (see Related Tickets).
- A limits line. rpg ships the fix in its current PR, so a line would be stale on landing (rpg-planner-ubuntu, 2026-11-08).

## Acceptance Criteria
- The contract names an outcome for a failed DLQ write and for an unreadable source entry.
- No sentence says the ACK happens regardless of the DLQ write.
- `tests/docs/test_doc_path_existence.py` passes.

## Related Tickets
- TCK-20261107-AN-EXHAUSTED-STREAM-MESSAGE-IS-ACKED-WHEN-ITS-DLQ-WRITE-FAILS (code fix, rpg)
- TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP (same PR)

## Related Docs
- docs/architecture/observability_hot_path_safety_contract.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
src/observability/stream/consumer.py

## Assumptions / Open Questions
- If this PR merges before rpg's fix, the contract briefly states intent that the code doesn't meet yet. That's accepted: the defect ticket is open and cited here.

## Implementation Notes
Edited `:124` and added two rows after it. Reworded `:143` to say the ACK happens only after a successful DLQ write, with a pointer to the table. The behaviour is as rpg-planner-ubuntu stated it.

## Test Summary
- `pytest -m "not slow" tests/docs`: 91 passed, 2 skipped, 1 xfailed.
- `tests/tools/test_observability_skill_content.py` and `tests/architecture/test_phase19_hot_path_safety_contract.py` (the two tests that reference this contract): 10 passed.

## Files Changed
- docs/architecture/observability_hot_path_safety_contract.md

## Completion Summary
