---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261107-AN-EXHAUSTED-STREAM-MESSAGE-IS-ACKED-WHEN-ITS-DLQ-WRITE-FAILS
phase: open
date: 2026-11-07
tags: [observability, bug]
---

# TCK-20261107-AN-EXHAUSTED-STREAM-MESSAGE-IS-ACKED-WHEN-ITS-DLQ-WRITE-FAILS

## Title
The stream consumer's reclaim sweep ACKs a message that has used up its delivery attempts even when the dead-letter write failed, so the message is lost silently

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
The owner asked, via personal-career on 2026-11-07, that this defect be ticketed. It is review row R-obs F1 (lead-planner draft `agent-working/lead/review_followups_2026-11-07.md`, Batch 1). Verified at origin/main a7f1bb3df:
- In `RedisStreamConsumer._reclaim_pending` (`src/observability/stream/consumer.py:126-166`), an entry at `times_delivered >= MAX_DELIVERY_ATTEMPTS` is sent to the DLQ (`:158-163`) and then always ACKed (`:164`).
- `_send_to_dlq` returns False on a failed XADD (`:76-89`), but the result is ignored.
- If the source entry is no longer readable (`xrange` empty, `:156-157`), it is ACKed with no DLQ entry at all.
- The contract says exhausted messages are "routed to the DLQ stream and ACKed off the source stream" (`docs/architecture/observability_hot_path_safety_contract.md:124,143`).

## Scope
- ACK only when `_send_to_dlq` returned True.
- On failure, leave the message pending for the next sweep, and log or count the failure.
- Decide and document the `xrange`-empty case.
- Regression test: with a fake client whose XADD raises, the message is not ACKed and a later successful sweep does ACK it.
- Update the contract line if the empty-entry behaviour is kept.

## Out of Scope
Other telemetry run-change items in the same review batch: per-tick `law_id`, the watchdog baseline and the anomaly dedup key.

## Acceptance Criteria
- The test above passes and fails on a7f1bb3df.
- The existing consumer tests pass.
- The contract and the code agree.

## Related Tickets
- TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC (done; built the DLQ and reclaim)

## Related Docs
- docs/architecture/observability_hot_path_safety_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
src/observability/stream/consumer.py, tests for the stream consumer

## Assumptions / Open Questions
- A permanently failing DLQ would leave the message pending forever. Is that acceptable, or does it need a bounded give-up with a counter? This is for the owning planner.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
