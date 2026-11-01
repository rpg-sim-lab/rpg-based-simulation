---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS
artifact_type: plan
phase: done
date: 2026-11-01
tags: [agent-monitoring, governance]
---

# Plan

1. **`tools/agent-monitoring/record_review.py`** (new). CLI `--ticket-id`, `--review-ref <PR#>#<comment id>`, `--agent` (default `claude`). Steps, all read-only until the last:
   - Validate the ref with `record_hand_orchestrated_closure._REVIEW_REF`.
   - Load runs and events from the data shards (`load_data_glob`); pick the ticket's runs with `execution_mode == "hand"` and `workflow == "implement-ticket"`; take the latest execution (`run_dedup`). None found: refuse.
   - Read-only check of the ref (designer amendment 2): `gh api repos/ttnhan18062000/rpg-based-simulation/issues/comments/<id>` must exist and its `issue_url` must end in `/<PR#>`; a missing comment or a PR mismatch refuses with nothing written. If `gh` or the network is unavailable, print a WARNING and still write, so a monitoring write never fails because of the check.
   - Refuse when `Review` is not in `full_phases(run.tier)` (hotfix), when the run already has a Review event with status `ok` (including one from an earlier post-review), or on any malformed input.
   - Build one event: run_id, execution_id, provider, ticket_id, phase `Review`, status `ok`, agent, `seq` = max seq of the run + 1, `ts` now, a summary reusing `review_ref_event`'s wording, and `supersedes` = seq of the folded skipped Review event when one exists (absent when the run has no Review event).
   - Validate with `record_events.validate_record`, then append to `resolve_write_target("events")` with `writer.write_line` + `stamp_session_role`. Every refusal prints `ERROR: ...; nothing was written.` and exits 1 with the shards untouched.
2. **`record_events.validate_record`**: `supersedes`, when present, is a positive integer.
3. **`run_dedup.drop_superseded_events(events)`**: drops an event when another event of the same `(run_id, execution_id)` and the same phase has `status ok` and `supersedes == event.seq`. Applied in `generate_retro._load_runs_and_events` on both return paths. `path_report` needs no counting change; a test pins that it reads Review as ran once.
4. **Docs**: `docs/agent-monitoring/schema.md` (the `supersedes` field and the overlay) and `README.md` "Recording coverage for a hand-orchestrated closure" (order: close, PR, review, `record_review.py`; `--review-ref` at close stays valid). The README says where the appended row is committed (designer amendment 1): the row is created after the PR head is pinned, and pushing it to that PR changes the head (a fresh owner ask and re-review), so by default it rides the closer's NEXT batch PR or a monitoring-only PR (like #805); adding it to the same PR is the exception. schema.md adds one line: a retro already published for a closed week keeps its skipped count; only a regenerated one picks up the overlay. Update the `record_hand_orchestrated_closure.py` docstring/`--help` of `--review-ref` to point at the new tool.
5. **CLAUDE.md** (owner's file): one line after the closure example, wording per the ticket, shown separately in the PR for the owner's confirm.
6. **Tests** in `tests/tools/` per test_plan.md.

Out of scope: backfill, Architecture-Verify, making Review blocking, `implement-ticket.js`.
Review: agent-working-designer-u24 reviews this plan before Implement.
