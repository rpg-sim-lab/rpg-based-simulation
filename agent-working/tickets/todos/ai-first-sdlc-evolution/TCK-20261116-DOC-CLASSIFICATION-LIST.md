---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-DOC-CLASSIFICATION-LIST
phase: open
date: 2026-11-16
tags: [ai, governance]
---

# TCK-20261116-DOC-CLASSIFICATION-LIST

## Title
A read-only script lists every non-archive document with its status, last change, dead-path count and any document that restates it.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Docs-truth track of the SDLC plan (`docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, "Docs-truth track" under Phase 4). Filed by agent-working-planner on 2026-11-16 from agent-working-designer's hand-off. The owner's decisions are on #715: 6911224913 (Q3: all four checks start report-only, none blocking) and 6911534263. The measurements and reasoning are in `agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md`. Filing only: dispatch needs a separate owner go. P3, behind RPG work (#715 6911759453). It supplies the list for rpg-planner's brainstorm-status edit (F5b in the hand-off), because `docs/brainstorm/**` routes to rpg.

## Scope
1. A script that lists each document under `docs/` (not `docs/archive/`), with:
   - its status;
   - its last-touched commit date;
   - its dead-path count (the designer's path measure, `docs_truth_plan.md` section 6);
   - whether another document restates its subject.

   The output is a list for the owner, never a change.
2. The list names the 14 `docs/brainstorm` documents with no status, for rpg-planner's status edit.

## Out of Scope
- Changing any document's status or location.

## Acceptance Criteria
1. The script runs read-only and its output is committed as a stored artifact at a named commit.
2. The 14 status-less brainstorm documents are listed, and the list is sent to rpg-planner-ubuntu.
3. The "restates its subject" column states its method and its limits.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY (search ranking needs the statuses)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (Docs-truth track)
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Code Areas
- tools/ (new script)

## Assumptions / Open Questions
- The restatement column is a heuristic. Say so in the output.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
