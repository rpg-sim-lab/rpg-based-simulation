---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-CHANGED-CODE-CHECK-REPORT-ONLY-WITH-PROOF-ESCAPE
phase: open
date: 2026-11-16
tags: [ai, governance]
---

# TCK-20261116-CHANGED-CODE-CHECK-REPORT-ONLY-WITH-PROOF-ESCAPE

## Title
The mechanism changed-code check runs report-only in CI, and a 'no behaviour change' claim for `implemented_by` code must carry proof.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Docs-truth track of the SDLC plan (`docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, "Docs-truth track" under Phase 4). Filed by agent-working-planner on 2026-11-16 from agent-working-designer's hand-off. The owner's decisions are on #715: 6911224913 (Q3: all four checks start report-only, none blocking) and 6911534263. The measurements and reasoning are in `agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md`. Filing only: dispatch needs a separate owner go. P3, behind RPG work (#715 6911759453). The tool is agent-working's. Its content (`registries/mechanisms.yaml`) is rpg-planner's.

## Scope
1. Run `tools/mechanism_registry/mechanism_registry_changed_code_check.py` in CI as a report-only step: one finding per file, with the mechanisms that cite it, and a count of findings per PR.
2. **The proof escape.** A "no behaviour change" claim for code a mechanism lists as `implemented_by` must carry proof. That much is the owner's decision; the forms below are design, not the owner's:
   - (a) hash-neutral: the pinned cells, world, seed and ticks, with both final hashes equal. This self-certifies.
   - (b) an annotation-, docstring- or rename-only change, with rpg-designer's sign-off on the ticket. rpg-planner checks the proof.

   A bare reason is reported as "unproven".
3. **RPG priority** (#715 6911759453). While the check is report-only, the proof check never delays an RPG PR. An unproven claim is counted, not waited on.
4. Report-only for at least 2 weeks (proposed, not owner-decided), with counts of how often it fires and why.

## Out of Scope
- Editing `registries/mechanisms.yaml`. That file is rpg-planner's, and any change comes as an exact before/after.
- Making the check blocking: a later owner decision.

## Acceptance Criteria
1. The CI step reports findings per file with their mechanism lists and never fails the PR. Tests cover a finding, a proven escape of each form, and an unproven escape.
2. The counts over the report-only window are recorded.
3. The workflow-file diff goes to the owner before commit.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE (the existing advisory)
- TCK-20261116-DOC-CITATION-RESOLVER-REPORT-ONLY (runs clean first)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (Docs-truth track)
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Code Areas
- tools/mechanism_registry/mechanism_registry_changed_code_check.py
- .github/workflows/test.yml

## Assumptions / Open Questions
- Evidence that it fits: rpg-planner's replay over the last 150 merges found that 14 of the 36 `src`-touching merges would fire, with 1-12 findings each. That is rpg-planner's number, not re-run here.
- Order: after the citation resolver has run clean.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
