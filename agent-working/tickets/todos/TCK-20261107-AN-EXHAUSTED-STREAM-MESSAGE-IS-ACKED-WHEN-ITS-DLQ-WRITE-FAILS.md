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
Planner scope (rpg-planner-ubuntu, 2026-11-08; owner dispatch "yes", logged at #715 comment 6720661924). This answers the open question and is the intended behaviour:
- Re-verified at origin/main 297494469: `consumer.py:164` ACKs unconditionally after `_send_to_dlq` (`:76-89`, returns False on a failed XADD).
- DLQ write fails: do not ACK. The message stays in the PEL and the next reclaim sweep retries the DLQ write; it is still exhausted, so it goes straight back to the DLQ path. Log at error level and count the failure on the consumer (a typed counter attribute next to the existing failure counters, readable by the pending/lag metrics code).
- No bounded give-up. A permanently failing DLQ leaves the entry pending, which the PEL-size metric (TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS) already makes visible. A visible pending entry is preferred over a silent loss.
- Source entry gone (`xrange` empty, e.g. trimmed by MAXLEN): write a DLQ tombstone entry (`dlq_source_id`, `dlq_reason="source entry no longer readable"`, `dlq_delivery_count`, `dlq_failed_at`, no payload) and ACK only if that write succeeded. Every exhausted message then leaves a DLQ record.
- Tests: XADD raises means no ACK and the counter is bumped; a later sweep with XADD working ACKs; empty xrange writes a tombstone then ACKs; tombstone write fails means no ACK.
- The contract row in `docs/architecture/observability_hot_path_safety_contract.md:124,143` is lead-owned. rpg-planner-ubuntu sends lead this behaviour; the implementer does not edit that file.

## Test Summary

## Files Changed

## Completion Summary
