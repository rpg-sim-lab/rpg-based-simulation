---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-SDLC-RETIRE-PIPELINE-WORKFLOWS
phase: open
date: 2026-11-16
tags: [ai, governance, delivery]
---

# TCK-20261116-SDLC-RETIRE-PIPELINE-WORKFLOWS

## Title
`implement-ticket.js`, `implement-epic.js` and the skill imitation are removed together, once the close check has run two weeks with both OD-5 lines.

## Status
BLOCKED

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
SDLC Phase 4, filed by agent-working-planner on 2026-11-16 from agent-working-designer's OD-5 hand-off.

The owner decided OD-5 by AskUserQuestion in lead-planner's session, recorded at #715 6911091662:
- Q1, option A: retire in Phase 4. Remove `implement-ticket.js` only after the OD-4 close check has run 2 weeks AND carries (1) a mechanical test-scope floor and (2) an architecture verdict on `src`-touching PRs. Tags make it recoverable.
- Q2: `implement-epic.js` and the skill imitation follow the same outcome and are removed together.
- Neither condition is waived.

The evidence is `agent-working/stored_artifacts/sdlc-decisions/od5_evidence_pack.md`. The record is `docs/plans/agent_infrastructure/SDLC_DECISION_RECORD.md`, section "2026-11-16 (later)".

**BLOCKED** until every gate condition below holds. Dispatch then still needs a separate owner go.

## Gate (all must hold, each with evidence written into this ticket before any removal)
1. **Two weeks with both lines.** TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB is merged. Its gate job carries both the test-scope floor line and the architecture-verdict line. It has run for at least 2 weeks counted from the first day it carried both: a check that runs without them does not start the clock. Evidence:
   - the first step summary showing both lines, with its PR and date;
   - two weeks of runs after it;
   - the floor and verdict counts from that window.
2. **Plan Phase 4 prerequisites** (plan §39 Phase 4 item 6). These are plan prerequisites, not owner conditions: OD-5 named only the two lines and the 2-week run, so the owner may drop any of them, for example if Phase 3 stalls.
   - Phase 2 is in force (gate 1).
   - Phase 3 has landed (TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS is closed).
   - The R0 tags exist: the four `baseline/sdlc-*` tags, shown by `git ls-remote --tags origin 'baseline/*'`.
   - The `sdlc-pipeline-workflows-20261031` tag covers both workflow files and the skill imitation. If any of them is missing from it, the owner adds a tag first, on its own ask. This ticket never creates or moves a tag.
3. **Decisions.** OD-5 is decided (as above). OD-6 is decided the other way: the Codex track is kept and marked legacy (TCK-20261116-SDLC-CODEX-TRACK-MARKED-LEGACY), so it is out of this removal.

## Scope (only after the gate)
1. Remove:
   - `.claude/workflows/implement-ticket.js` and `.claude/workflows/implement-epic.js`;
   - the skill imitation (the `implement-ticket` and `implement-epic` skills, which hand-run the pipeline's phases);
   - the pipeline-only gate call sites;
   - the source-pinned tests (about 61, the plan's figure; re-measure it).
2. Before deleting any test, record what it pins, and check that no test also covers a function the hand path uses. Keep any such test, moved if needed.
3. Update the docs that describe the pipeline as a path (`docs/ai/*`, `docs/guides/delivery_process.md`, `.claude/agents/test-scoper.md` and others), so they point to the hand path and the tags. CLAUDE.md text about the pipeline is a governing edit: the exact diff goes to the owner, who approves it directly.
4. E7: measure LOC, test files and CI minutes, before and after.

## Out of Scope
- The Codex / provider-neutral track (OD-6: kept).
- `create-tickets.js` and the simulation-lab workflows (plan Phase 4, "Preserved").
- Creating, moving or deleting any tag.

## Acceptance Criteria
1. The ticket records the gate evidence for all three conditions, dated, before the removal commit.
2. The listed files are gone, and CI is green on the removal PR.
3. A table lists every deleted test with what it pinned, plus every kept or moved test with the reason.
4. The E7 before and after numbers are recorded.
5. Rollback is shown to work: reverting the removal commit restores the files, and the baseline tags are unchanged on both the tag-object SHA and the peeled commit.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB (gate 1)
- TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS (gate 2)
- TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS (the tags)
- TCK-20261115-SDLC-BASELINE-TAG-RULESET (tag protection)
- TCK-20261116-SDLC-CODEX-TRACK-MARKED-LEGACY (OD-6, excluded)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (§32a, §39 Phase 4)
- docs/plans/agent_infrastructure/SDLC_DECISION_RECORD.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/od5_evidence_pack.md
- agent-working/stored_artifacts/sdlc-phase-0/r0_inventory_record.md

## Related Code Areas
- .claude/workflows/implement-ticket.js, .claude/workflows/implement-epic.js
- .claude/skills/ (implement-ticket, implement-epic)
- tests/tools/ (the source-pinned tests)

## Assumptions / Open Questions
- Rollback: revert the removal commit. The baseline tags stay the recovery path.
- The removal goes through the normal PR and the owner's merge. It needs no extra ask unless the gate evidence is thin.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
