---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS
phase: done
date: 2026-11-01
tags: [agent-monitoring, governance]
---

# TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS

## Title
A hand close's Review can be recorded after the fact, once the planner's PR review comment exists; CLAUDE.md's closure example names that command

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
This follows TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW (#807, merged c9b9a50f4).
agent-working-designer-u24 found the gap in its #807 review. A hand close is recorded at ticket close, before its PR exists, so
`record_hand_orchestrated_closure.py --review-ref` can't be given in the normal order (close -> PR -> review). Every
standard hand close therefore still records Review `skipped`/`no_hand_tool`, which is the gap #807 was meant to close.

The owner held the CLAUDE.md line for `--review-ref` (PR #808, closed unmerged) and chose to fold it into this follow-up:
"the follow-up's CLAUDE.md line names the append command, which works in the normal close order" (#715 issuecomment-6546624296).

## Scope
- A post-review recorder, e.g. `tools/agent-monitoring/record_review.py --ticket-id <TCK-ID> --review-ref <PR#>#<comment id>`.
  It's run by the domain planner, or by the implementer on the planner's word, after the review comment exists. It follows
  the pattern of `gate_ledger.py outcome`, which adds an outcome to an existing verdict after the fact:
  - It finds the ticket's existing hand-close run and refuses with nothing written when there's none.
  - It refuses for a tier with no Review step (hotfix), for a malformed ref, and for a run whose Review is already `ok`.
    Use #807's `_REVIEW_REF` and the `full_phases` check.
  - It writes an append-only record and never rewrites the existing events row. Choose, and justify in plan.md, between:
    (i) appending a new Review `ok` event for the same run_id, with a fresh seq and a `supersedes` link to the folded
    skipped event; or (ii) a separate small record kind, keyed by run_id, that the readers overlay, as gate outcomes are.
    Either way, it lands in the current week's shard.
- Readers (`path_report.py`, `generate_retro.py` Phase Status): a run with a recorded post-review counts Review as ran,
  exactly once. A run without one is unchanged.
- `docs/agent-monitoring/schema.md` (the new field or record) and `docs/agent-monitoring/README.md` ("Recording coverage for a
  hand-orchestrated closure"): the normal order, close then PR then review, then `record_review.py`.
  `--review-ref` at close stays valid, for the rare case where the review already exists.
- **CLAUDE.md** (owner-approved in substance, #715 6546624296): one line after the closure example. Wording to put to the
  owner with the PR diff: "  After the planner's PR review comment exists, record it:
  `python3 tools/agent-monitoring/record_review.py --ticket-id <TCK-ID> --review-ref <PR#>#<comment id>` (standard tier;
  without it Review stays skipped)." The local commit 3bb1ed023 (the held `--review-ref` line) is superseded, not reused.
- Tests in `tests/tools/`: append works; each refusal writes nothing; Review is counted once (a run with both the folded
  skip and the post-review counts as ran, not as both); a run without a post-review is unchanged; a W44-shaped sample is
  shown before and after.

## Out of Scope
- Backfilling earlier runs' Reviews (the owner may ask for it separately).
- Architecture-Verify (it stays `skipped` unless a reviewer records an architecture verdict).
- Making Review blocking, or changing tiers or `implement-ticket.js`.

## Acceptance Criteria
1. `record_review.py` appends as scoped and refuses as scoped, and every refusal leaves the shards byte-identical.
2. The readers count Review exactly once for a run with a post-review, and output for runs without one is byte-identical.
3. `pytest tests/tools -k "review or hand_orchestrated or path_report or retro" -p no:randomly` passes, run serially.
4. The PR body shows the CLAUDE.md diff separately, for the owner's confirm, and a before/after Phase Status sample.
5. The first real use: after this PR's own review comment, its planner runs `record_review.py` for this ticket. That
   happens after merge, as a monitoring-only commit in the next agent-working PR.

## Related Tickets
- TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW (#807)
- TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION (the after-the-fact outcome pattern)

## Related Docs
- docs/agent-monitoring/README.md, docs/agent-monitoring/schema.md
- CLAUDE.md "After Work" (owner's file; one line, shown in the PR for the owner)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py (`review_ref_event`, `_REVIEW_REF`)
- tools/agent-monitoring/gate_ledger.py (pattern), path_report.py, generate_retro.py, run_dedup.py

## Assumptions / Open Questions
- Design (i) vs (ii) is the implementer's to propose in plan.md. The designer reviews it before Implement.
- Dispatch: standard tier, so an owner go through lead-planner-u24 is needed.

## Implementation Notes
Design (i), designer-reviewed with two amendments (both folded in): a Review `ok` event with `supersedes: <seq>`, and one read overlay `run_dedup.drop_superseded_events` applied in `generate_retro._load_runs_and_events`. `record_review.py` also checks read-only that the comment exists on the named PR (WARNING and still write when `gh` is unavailable). README states the row rides the closer's next batch PR by default.

## Test Summary
tests/tools/test_record_review.py (30 tests, new). `pytest tests/tools -k "review or hand_orchestrated or path_report or retro" -p no:randomly`: 432 passed, 10 skipped, 1 xfailed.
Phase Status, Review row, fixture run: before `skipped 1`; after the post-review with overlay `ok 1`; both rows without the overlay `skipped 1, ok 1`.

## Files Changed
tools/agent-monitoring/{record_review.py (new), run_dedup.py, generate_retro.py, record_events.py, record_hand_orchestrated_closure.py (help text)}; tests/tools/test_record_review.py (new); docs/agent-monitoring/{README,schema}.md; CLAUDE.md (one line, owner confirm in the PR).

## Completion Summary
record_review.py records a hand close's Review after the PR review comment exists, append-only, and the retro counts it once. Backfill, Architecture-Verify and the pipeline are untouched. First real use is this ticket's own review, after merge.
