---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-FRESHNESS-STAMPS-REPORT-ONLY
phase: open
date: 2026-11-16
tags: [ai, governance]
---

# TCK-20261116-FRESHNESS-STAMPS-REPORT-ONLY

## Title
An optional freshness stamp on a Bible chapter or engine contract reports, without blocking, when a file the chapter cites has changed since the stamp.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Docs-truth track of the SDLC plan (`docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, "Docs-truth track" under Phase 4). Filed by agent-working-planner on 2026-11-16 from agent-working-designer's hand-off. The owner's decisions are on #715: 6911224913 (Q3: all four checks start report-only, none blocking) and 6911534263. The measurements and reasoning are in `agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md`. Filing only: dispatch needs a separate owner go. P3, behind RPG work (#715 6911759453). The owner's words for this check: freshness stamps, "dropped if noisy".

## Scope
1. First, read what the Bible's "Certified Level 1" already records, so the stamp is not a second source of truth. Record the finding.
2. An optional stamp format: `verified_at: <sha>` and `owner: <seat>`.
3. A report-only line when a file the chapter **cites** has changed since the stamp. Any other code change does not trigger it.
4. One worked example in a test fixture. Stamp nothing in the real documents in this ticket.

## Out of Scope
- Stamping real chapters (rpg's content).
- Blocking.

## Acceptance Criteria
1. The Certified Level 1 reading is recorded, with how the stamp relates to it.
2. A test shows the line fires on a change to a cited file and not on an uncited one.
3. The ticket says the check is dropped if, after the report-only window, it fires on most RPG PRs (owner: "dropped if noisy").

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-DOC-CITATION-RESOLVER-REPORT-ONLY (reuses its citation parse; runs after it is clean)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (Docs-truth track)
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Code Areas
- tools/gate_checks/
- docs/mechanics/ (read only)

## Assumptions / Open Questions
- Keying on cited files is design, not the owner's.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
