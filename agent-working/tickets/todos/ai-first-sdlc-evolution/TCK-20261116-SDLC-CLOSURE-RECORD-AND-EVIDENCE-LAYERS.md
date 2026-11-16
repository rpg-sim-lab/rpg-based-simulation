---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS
phase: open
date: 2026-11-16
tags: [ai, agent-monitoring, observability]
---

# TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS

## Title
Every ticket close writes one closure record, and a derived view links ticket, sessions, PR, CI and decision, with no database.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
SDLC Phase 3, filed by agent-working-planner on 2026-11-16. Filing only: dispatch needs a separate owner go.

The owner chose OD-11, three linked layers with no database, by accepting the designer's recommendation (#715 6910853925). Plan:
- §29a: the evidence lifecycle, L1/L2/L3;
- §39 Phase 3: the objective that every close links ticket → sessions → PR → CI → decision, validated by E5.

Phase 3 can run in parallel with Phase 2. When this lands, the close check's condition 6 ("a closure record exists") switches on.

## Scope
1. **L1, the closure record.** One record per ticket close, written in the PR's tree. It holds:
   - the ticket id and tier;
   - the session ids and roles that worked it;
   - the run ids;
   - the gate verdict ids and their outcomes;
   - the owner-approval comment ids it cites.

   The binding to the PR and head SHA is derived later and not stored (§28 condition 6). The record is written by the same entry point as the closure tool, and by `work close` once that exists.
2. **L2, the derived view.** A read-only generator joins L1 with the monitoring shards, the working log and GitHub PR and CI data, giving ticket → sessions → PR → CI → decision. It is regenerated from main, never hand-edited.
3. **L3, the append.** Week close (or the retro batch PR) appends the merged PR and CI result to each record closed that week. That is never done by a post-merge bot. This holds with or without M1.
4. **Turn on condition 6** in the close check from TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB, still report-only.
5. **Schema.** Add the record to `docs/agent-monitoring/schema.md`, with a compatibility reader: closes from before this ticket have no record, and readers tolerate that.
6. **E5.** Reconstruct 10 closes made after this lands end to end. Zero missing links is the target. Record each gap found.

## Out of Scope
- Attribution fields on tool rows, event labels, SessionEnd and coordination metrics: TCK-20261116-SDLC-ATTRIBUTION-FIELDS-AND-COORDINATION-METRICS.
- A database or external store (OD-11 B and C, not chosen).
- Back-filling records for past closes.
- Native OTel export.

## Acceptance Criteria
1. A close made with the closure tool writes exactly one L1 record, and a second write for the same close is refused. Shown by tests.
2. The L2 generator rebuilds the same view twice from the same inputs, byte for byte. A test covers a close with no record from before this ticket.
3. Week close appends L3 for the week's closes. Shown by a test on a temp week.
4. E5 over 10 new closes is recorded as a stored artifact, with each missing link named. The plan's acceptance target is at least 95% complete chains; the result is reported, not tuned to hit the target.
5. The close check's condition 6 reports for a PR without a record. It stays report-only.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB
- TCK-20261116-SDLC-WORK-CLOSE-CLI
- TCK-20261116-SDLC-ATTRIBUTION-FIELDS-AND-COORDINATION-METRICS

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (§29, §29a, §39 Phase 3)
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/agent-monitoring/ (week close, generate_retro.py)
- tools/agent-monitoring/gate_ledger.py

## Assumptions / Open Questions
- Where L1 lives (a per-week shard or one file per close) is the implementer's design choice. Bring it to agent-working-planner before code. Watch for the shard merge-conflict patterns already known for the per-week files.
- GitHub reads for L2 use `gh` read-only, with no token in any record.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
