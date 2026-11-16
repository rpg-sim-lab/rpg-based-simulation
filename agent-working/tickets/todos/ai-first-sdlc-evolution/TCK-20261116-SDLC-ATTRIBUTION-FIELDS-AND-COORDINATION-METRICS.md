---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-SDLC-ATTRIBUTION-FIELDS-AND-COORDINATION-METRICS
phase: open
date: 2026-11-16
tags: [ai, agent-monitoring, observability]
---

# TCK-20261116-SDLC-ATTRIBUTION-FIELDS-AND-COORDINATION-METRICS

## Title
Monitoring rows carry their tool call and work item, events say whether they were derived or narrated, sessions record their end, and the retro shows coordination cost.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
SDLC Phase 3, filed by agent-working-planner on 2026-11-16 under the owner's OD decisions (#715 6910853925). Filing only: dispatch needs a separate owner go.

Plan §39 Phase 3, item 3 (the attribution half). The changes:
- events labelled `derived` or `narrated`;
- tool rows carry `tool_call_id` and an active work-item id;
- `session_role` always resolved;
- a SessionEnd span;
- coordination metrics (messages per close, owner touches per PR);
- the retro reads the evidence, regenerated from main.

Acceptance (plan): unattributed `session_role` below 5%, and coordination metrics in the retro.

## Scope
1. **Measure first, read-only.** For the current and previous weeks' shards, report:
   - the share of tool rows with no work item;
   - the share of rows with an unresolved `session_role`;
   - whether any row carries a tool-call id today.

   This is the baseline for AC1.
2. **Fields.** Add the optional fields below, with readers tolerating their absence (plan §39 Phase 3 rollback):
   - `tool_call_id` and `work_item_id` on tool rows;
   - `provenance: derived | narrated` on events;
   - `session_role` always resolved, or the literal `unattributed` with a reason.
3. **SessionEnd.** A SessionEnd hook writes one span row per session: session id, role, start and end, and counts. No message content, and no command lines or env. The `.claude/settings.json` hook entry is a governing change, so the exact diff goes to the owner before commit.
4. **Coordination metrics in the retro:** cross-session messages per close, and owner touches per PR (#715 decision comments that cite the PR). It counts messages; it never stores their text.
5. **Retro reads from main.** `generate_retro.py` regenerates its evidence sections from main's shards, not from the local checkout.

## Out of Scope
- The closure record and L2/L3: TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS.
- Native OTel export (plan: optional, user settings).
- A token or cost budget (OD-8, after a month of data).
- Rewriting past shards.

## Acceptance Criteria
1. The baseline from scope 1 and the after-measurement over one full week are both recorded. Unattributed `session_role` is reported against the plan's 5% target, without tuning the numbers to meet it.
2. The new fields are in `docs/agent-monitoring/schema.md`. A reader test passes on a shard without them.
3. The SessionEnd hook writes one row per session end in a test harness, and never fails the session if the write fails.
4. The retro shows the two coordination metrics for a test week.
5. Redaction is unchanged: a test shows that no message text, command line or env value reaches a row.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS
- TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION (redaction to keep)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (§29, §39 Phase 3)
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/ (tool hook, record_events.py, generate_retro.py)
- tools/sessions/session_start_hook.py
- .claude/settings.json (hook entry; governing)

## Assumptions / Open Questions
- Whether Claude Code exposes a tool-call id to the PostToolUse hook payload is to be checked first. If it doesn't, the row records that the id is unavailable, and that is stated as a gap.
- The read-row path truncation at 120 chars is a known, documented limit. It is not changed here.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
