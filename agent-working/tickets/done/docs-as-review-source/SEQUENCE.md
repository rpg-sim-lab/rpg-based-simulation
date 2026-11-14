# Implementation Sequence: docs-as-review-source

Epic `TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE`, filed by agent-working-planner, 2026-11-08, on the owner's dispatch. Plan: origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), "Seed work and effort estimate". Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08.

## Order

1. PR 1 (dispatched 2026-11-08):
   - TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH (standard)
   - TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY (standard)
   - TCK-20261108-DOC-STEP-ON-HAND-CLOSES-AND-REVIEW-RULES (hotfix; needs B; CLAUDE.md diff gets the owner's direct OK)
2. PR 2, after PR 1 merges, on the owner's dispatch:
   - TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT (standard; carries E2 and Q5)
   - TCK-20261108-STALE-DOC-DETECTION-PILOT (standard; J1-J2 only)
3. PR 3, on the owner's dispatch: TCK-20261108-PROJECT-FACTS-PAGE-GENERATED (standard). It has no dependency and may move earlier.

## Rules

- Cite the plan; never copy it into tickets (define-once).
- Pushes and merges are the owner's yes.
- J3 is not approved: nothing here edits a doc found stale by J1.
