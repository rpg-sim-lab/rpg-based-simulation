---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261108-FOUR-ENGINE-AND-OBSERVABILITY-DOC-CLAIMS-NO-LONGER-MATCH-THE-CODE
phase: open
date: 2026-11-08
tags: [documentation, engine, observability]
---

# TCK-20261108-FOUR-ENGINE-AND-OBSERVABILITY-DOC-CLAIMS-NO-LONGER-MATCH-THE-CODE

## Title
Four rpg-owned engine and observability doc claims no longer match the code: the packet seed, what a worker receives, whether Canonical exists, and the hard-law count

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
This is batch A (rpg part) of `agent-working/lead/docs_as_review_source_plan.md` rev 3.2, committed on lead-planner's local branch `lead-docs-review-source` at d1fa1263c. The owner approved the plan (#715 comment 6720445592) and dispatched this batch to rpg-planner-ubuntu ("yes", logged at #715 comment 6720661924). rpg-planner-ubuntu re-read each claim at origin/main 297494469:

1. `docs/engine/contracts/simulation_kernel_contract.md:65-73` says `WorkerPacket.seed` is "dead", only written and never read. Since #837 (531010a9a), `src/engine/executor.py:301` builds the packet with `seed=state.seed`, the world seed, and the code comment there says `context.seed` means the same under either executor. The paragraph after it ("Disposition — deferred, not removed") is built on the dead-seed premise.
2. `docs/engine/deterministic_execution.md:149` (Rule 3) says workers receive `AuthoritativeState.readonly_view()`. Under the concurrent executor, workers get a `WorkerPacket` (#837).
3. `docs/engine/deterministic_execution.md:69` says the Canonical contract "has no implementation yet (`PERF-M1`)", and `:182` says Canonical's proxies are "pending `PERF-M1`". `:71` of the same doc describes Canonical as implemented and opt-in (`CanonicalSignalSource`, `signal_contract=CANONICAL`, INFRA-426).
4. `docs/observability/hard_law_monitor.md:16` and `:49` say "eight laws". `src/observability/hard_law_monitor.py` emits nine `law_id`s; the ninth, `LAW-POSITION-IN-WORLD`, was added 2026-10-10.

## Scope
- Item 1: state what the packet seed is now (the world seed) and where it is read. Grep the readers at the fix commit; do not assume them. Rewrite or remove the "Disposition — deferred, not removed" paragraph so it no longer rests on the dead-seed premise. Link to `docs/engine/deterministic_execution.md` instead of restating the RNG derivation.
- Item 2: Rule 3 says what each executor gives a worker: the sequential path and the concurrent `WorkerPacket` path. Verify both in `src/engine/executor.py` at the fix commit.
- Item 3: `:69` and `:182` say Canonical exists, opt-in, and name only what is still pending. Before writing what `PERF-M1` still owes, ask rpg-planner-ubuntu, who confirms it with perf-planner. `docs/performance/**` is perf's: do not edit it.
- Item 4: correct the count to nine in both places, and check that the doc's law list names `LAW-POSITION-IN-WORLD`.
- Optional (planner accepts it, cheap): cross-reference divergence 2.147 and the long sequential/concurrent equivalence test from `docs/engine/known_limitations.md:88` and `docs/engine/deterministic_execution.md:36,179`. Read 2.147 first; add the link only if it really bears on those lines.
- Rule from the plan: a normative doc is never edited to match defective code. If any claim turns out to describe intended behaviour that the code breaks, stop and report it to rpg-planner-ubuntu as a defect; do not edit the doc.

## Out of Scope
- `docs/engine/contracts/substrate_baseline_contract.md:27` ("6 phases"). The plan lists it as wrong, but it is not: `:40` of the same file explains that these are the 6 authoritative phases, and that with the PERSISTENCE hook they make the 7 in `kernel.md`. No edit. Reported back to lead-planner.
- Limits lines in `docs/engine/known_limitations.md` for the three defects fixed in this same PR (restore seed, DLQ ACK, harvest). A limits line for a defect fixed in the same change would be stale when it lands. A line is added only if one of them ships unfixed (for example, the harvest ruling says "intended").
- Limits lines for the watchdog reset, dirty tag and shutdown success defects. No ticket exists for any of them at 297494469, so there is nothing to cite. Asked lead-planner to file them or point to them.
- `docs/architecture/kernel_concurrency_design_philosophy.md` diagrams (lead's TCK-20261108-KERNEL-CONCURRENCY-DIAGRAMS-SHOW-A-SEED-THE-PACKET-NO-LONGER-CARRIES).
- `docs/architecture/observability_hot_path_safety_contract.md` (lead-owned; lead adds the DLQ failure row).
- The restore-seed code comment in `src/engine/scenario_checkpoint.py` (it rides with TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0).
- Any code change.

## Acceptance Criteria
- Each of items 1-4 matches the code at the fix commit, with a file:line citation the reviewer can re-check.
- No edit in a lead-owned or perf-owned file.
- `make knowledge-index-update` has been run; frontmatter is valid.

## Related Tickets
- TCK-20261108-KERNEL-CONCURRENCY-DIAGRAMS-SHOW-A-SEED-THE-PACKET-NO-LONGER-CARRIES (lead part of batch A)
- TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP (batch F; checks its kernel and determinism rows after this lands)
- TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0, TCK-20261107-A-HARVEST-IS-REJECTED-ONE-CHARGE-EARLY-WITHIN-A-TICK, TCK-20261107-AN-EXHAUSTED-STREAM-MESSAGE-IS-ACKED-WHEN-ITS-DLQ-WRITE-FAILS (same PR)

## Related Docs
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/deterministic_execution.md
- docs/engine/known_limitations.md
- docs/observability/hard_law_monitor.md
- docs/guidelines/intentional_divergences.md (2.147)

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/executor.py, src/core/worker_protocol.py, src/engine/signal_source.py, src/observability/hard_law_monitor.py

## Assumptions / Open Questions
- What `PERF-M1` still owes after Canonical landed: perf's answer, asked through rpg-planner-ubuntu.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
