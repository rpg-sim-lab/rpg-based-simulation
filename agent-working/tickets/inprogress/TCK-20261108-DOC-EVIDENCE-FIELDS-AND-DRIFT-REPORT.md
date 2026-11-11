---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT
phase: inprogress
date: 2026-11-08
tags: [ai, documentation, governance, frontmatter, agent-monitoring]
---

# TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT

## Title
Behaviour docs can carry evidence and a verification baseline, and an advisory drift report says which ones need re-verifying.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Batch C, plus E2 and Q5 (plan origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), P1, P5 "When code is read" and "Critical invariants", acceptance criteria 2 and 3, owner question Q5). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. Lands in PR 2, after PR 1 (batch B) merges.

## Scope
1. P1 frontmatter fields (all optional): `evidence_paths` (files, not directories), `verified_by` (ticket or PR), `verified_at` (code SHA read), plus `reviewed_by` (batch J: triaged, no staleness found; weaker than verified, never shown as verified). Add them to `docs/guidelines/frontmatter_schema.md` and `tools/validate_frontmatter.py` (shape checks: paths exist at write time, SHA shape, ticket ID shape).
2. Drift report tool, reusing the `tools/mechanism_registry/mechanism_registry_changed_code_check.py` pattern and the shared search from batch B. Baseline: the commit that last changed the doc's `verified_by` line (or `reviewed_by`), derived from git history so it survives squash merges. Flags "needs re-verify" when an evidence path changed, was deleted or renamed after the baseline, or the doc's own text changed after it. Lists unverified, reviewed_by, verified_by and needs-re-verify states. No stored state besides the fields.
3. Runs at close: pipeline Finalize (`implement-ticket.js`) and the hand-close checklist, advisory, never blocks.
4. Q5: the weekly run is a script step inside `tools/agent-monitoring/week_close.py` (called by `make agent-monitoring-close-week`), report-only; the retro gets 2-3 spot checks (a retro-template line; the retro itself is u24's).
5. E2: delivery_process.md gains the P5 rules that cite P1 (the "when code is read" triggers on verified_by and drift; critical invariants need a verified doc plus an independent test).

## Out of Scope
- Setting verified_by on any doc (batch H). AC 2 of the plan: no seed doc gets the fields without a ticket that records the claims checked.
- The J1 detection mode (TCK-20261108-STALE-DOC-DETECTION-PILOT), though it reuses this tool.
- Any blocking behaviour.

## Acceptance Criteria
1. Plan AC 2: a doc without verified_by shows as unverified in the report (test).
2. Plan AC 3: a changed, deleted or renamed evidence path, and a doc-text edit after the baseline, each produce "needs re-verify" in a test fixture; the baseline survives a squash-merged fixture history.
3. validate_frontmatter rejects malformed fields and accepts docs without them.
4. week_close.py runs the report without changing its own exit behaviour (test).
5. tests/tools/ passes in a lead slot; paths-guard tests run before push.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE
- TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH (shared search)
- TCK-20261108-STALE-DOC-DETECTION-PILOT (same PR)
- TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE (pattern)

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/guidelines/frontmatter_schema.md
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/validate_frontmatter.py, tools/mechanism_registry/mechanism_registry_changed_code_check.py
- tools/agent-monitoring/week_close.py, .claude/workflows/implement-ticket.js (Finalize)

## Assumptions / Open Questions
- The CLAUDE.md After Work line for running the report at a hand close is a governing-file edit: owner's direct OK on the diff, as in E1.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
