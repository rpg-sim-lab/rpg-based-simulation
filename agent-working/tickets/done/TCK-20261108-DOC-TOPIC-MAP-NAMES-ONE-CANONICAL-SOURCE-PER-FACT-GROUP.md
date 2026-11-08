---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP
phase: done
date: 2026-11-08
tags: [documentation, architecture]
---

# TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP

## Title
A reviewer has no single page naming the canonical doc and normative source for each fact group, so reviews re-derive it from code

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This is batch F (P4) of `agent-working/lead/docs_as_review_source_plan.md` rev 3.2, approved by the owner on 2026-11-08 (#715 comment 6720445592). D25 (`docs/audits/D25_engine_docs_drift.md`) mapped canonical docs for only 4-5 topics. The plan asks for one topic map that a review starts from.

## Scope
- New `docs/architecture/doc_topic_map.md`, with one row per fact group. Fact groups: kernel phases, pipeline order, determinism and RNG, checkpoint and restore, API and read models, WebSocket, observability stream and DLQ, alerts, watchdog, content pipeline, economy and conservation, factions, the agent workflow, and the rest found during investigation.
- Columns:
  - the canonical doc;
  - its normative source, with the precedence from the plan's "Normative sources" section (world-rules catalog > Mechanics Bible > engine and architecture contracts > parity ledger and divergences);
  - the satellite docs that should link to it;
  - verification status, derived from P1's fields once batch C lands; until then the column reads "unverified (no P1 fields yet)".
- Only canonical docs appear (V6). Living-doc states belong to the drift report.

## Out of Scope
- D25's follow-up (contracts/ and matrices/ at full depth), which is batch G and rpg-owned.
- Editing satellites to link to the canonical doc, which rides with batches A, H and J3.
- The P1 fields, drift report and facts page (batches C and D, agent-working).

## Acceptance Criteria
- Every fact group lists exactly one canonical doc and its normative source.
- No row names a history doc as canonical.
- The verification column is derived or says unverified; it is never typed as "verified".
- `tests/docs/test_doc_path_existence.py` passes; the page is indexed by `make docs-registry`.

## Related Tickets
- TCK-20261108-KERNEL-CONCURRENCY-DIAGRAMS-SHOW-A-SEED-THE-PACKET-NO-LONGER-CARRIES (same PR)
- TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT (D25)

## Related Docs
- docs/audits/D25_engine_docs_drift.md
- agent-working/lead/docs_as_review_source_plan.md

## Related Stored Artifacts
To be created under `agent-working/staging_artifacts/TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP/` when work starts.

## Related Code Areas
None (docs only).

## Assumptions / Open Questions
- The page lives in `docs/architecture/` (plan X26, owner Q2).
- The fact-group list is a starting set; investigation may split or merge groups.

## Implementation Notes
- Wrote `docs/architecture/doc_topic_map.md`. It has the precedence of normative sources, the verification-status rule, a map of 30 fact groups (each with a canonical doc, normative level, satellites and confidence), six known conflicts (C1-C6), each with evidence and an owner, and a "Not covered" list.
- All five D25 rows are kept.
- Every canonical doc is marked unverified until the P1 fields exist.

## Test Summary
- `validate_frontmatter.py --content-type doc` reports no violations.
- `pytest -m "not slow" tests/docs`: 91 passed, 2 skipped, 1 xfailed.
- All relative links in the page resolve (shell loop).
- The website build was not re-run for this page; the heavy slot was in use, and `onBrokenLinks` is `warn`.

## Files Changed
- docs/architecture/doc_topic_map.md
- agent-working/staging_artifacts/ (investigation, plan, test_plan)

## Completion Summary
Done. The map names one canonical doc per fact group and states the precedence. The conflicts it found are not fixed here; C1, C2, C3 (doc), C5 and C6 go to rpg, and C3 (skill files) and C4 to agent-working, as findings. Known gap: canonical docs were picked from headers and frontmatter, not full bodies (confidence column).
