---
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20261116-BRAINSTORM-DOCUMENTS-WITHOUT-A-STATUS-GET-ONE
phase: open
date: 2026-11-16
tags: [documentation]
---

# TCK-20261116-BRAINSTORM-DOCUMENTS-WITHOUT-A-STATUS-GET-ONE

## Title
Fourteen docs/brainstorm documents carry no status, so search cannot rank them below current documents as the owner decided; give each one a status taken from the document itself

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Owner decision #715 6911224913, Q2: "Rank them lower (Recommended)". Historical plans and status-less brainstorm documents stay searchable but rank below current documents, and brainstorm documents get a status first. agent-working-planner drafted this as F5b in the main checkout's `.claude/handover/drafts/docs_truth_fold_in_and_filings.md`, section 2. `docs/brainstorm/**` routes to rpg (rpg-planner-ubuntu), so it is filed here.

The list of the 14 comes from agent-working's TCK-20261116-DOC-CLASSIFICATION-LIST, and that ticket lands first. Filing only. Dispatch needs an owner go.

## Scope
1. Take the 14 status-less documents from the classification list. Re-check at the dispatch base that each one still has no `status:`. docs/brainstorm has 32 files at db6b4579d.
2. Give each document a frontmatter `status` from the allowed set in docs/guidelines/frontmatter_schema.md. Base it only on what the document says: its own dates, "superseded by", "decided in", and whether a later doc or ticket it names carried it out.
3. If the document alone doesn't decide its status, leave it unchanged and list it in the Completion Summary with the reason. Never guess.
4. Each assigned status gets a one-line reason in Implementation Notes, citing the document line.

## Out of Scope
- Search ranking itself (agent-working's CONTEXT ticket).
- Rewriting, moving or archiving any brainstorm document.
- Documents that already have a status.

## Acceptance Criteria
1. Each of the 14 either has a valid `status` with a cited reason, or is listed as undecided with a reason.
2. `python3 tools/validate_frontmatter.py docs/brainstorm/` passes.
3. The diff touches only frontmatter `status:` lines, plus a frontmatter block where one is missing entirely, in its minimal valid form.
4. rpg-planner-ubuntu co-signs the assignments, since the documents are rpg's.

## Related Tickets
- TCK-20261116-DOC-CLASSIFICATION-LIST (agent-working; supplies the list, lands first)
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION (docs-truth plan)

## Related Docs
- docs/brainstorm/
- docs/guidelines/frontmatter_schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/validate_frontmatter.py

## Assumptions / Open Questions
- If any brainstorm document is cited by rpg-designer as live design input, ask rpg-designer before marking it historical.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
