---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS
artifact_type: test_plan
phase: done
date: 2026-11-01
tags: [agent-monitoring, governance]
---

# Test plan

New `tests/tools/test_record_review.py` (temp data root, `--basetemp`), plus additions to `test_path_report.py` and `test_generate_retro.py`. Run serially: `pytest tests/tools -k "review or hand_orchestrated or path_report or retro" -p no:randomly`.

- Append works: a standard hand run with the folded skip gets one new Review `ok` event, fresh seq, `supersedes` = the skip's seq, same run_id/execution_id, in the current week's shard; the existing rows are byte-identical (append-only).
- Run with no Review event at all: appended without `supersedes`.
- Refusals, each asserting the shards are byte-identical and exit 1: no hand run for the ticket; hotfix tier; malformed ref (`12`, `12#`, `0#5`, `a#b`); Review already `ok` (folded-with-ref or an earlier post-review, i.e. a second run of the tool).
- Latest execution wins when a ticket has two hand runs.
- `validate_record`: `supersedes` of `0`, `-1`, `"3"`, `True` rejected; a positive int accepted.
- `drop_superseded_events`: drops only the matching skip; keeps a skip when the superseding row is not `ok`, in another run, or another phase; order preserved; no-op (same list contents) on data with no `supersedes`.
- Retro Phase Status: a run with skip + post-review counts Review 1 ok / 0 skipped (not 1+1); a run without a post-review is unchanged (byte-identical table section). Before/after sample of a W44-shaped fixture is captured for the PR body.
- `path_report`: a run with both rows counts Review `ran` once; a run without is unchanged.
- Cross-week: the run is in an earlier week than the append; week-close conservation still passes.
- Existing `test_record_hand_orchestrated_closure.py` and `test_path_report.py` stay green.
- Ref check (mocked `gh`): comment missing, comment on a different PR: refuse, shards byte-identical; `gh` unavailable: WARNING and the row is still written.
