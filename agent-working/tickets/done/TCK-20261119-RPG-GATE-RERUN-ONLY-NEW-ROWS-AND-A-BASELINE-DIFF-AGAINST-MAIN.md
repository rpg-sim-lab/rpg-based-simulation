---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN
phase: done
date: 2026-11-19
tags: [process-improvement]
---

# TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN

## Title
The rpg gate reruns only the (world, seed) runs behind a fail or drift row that main's latest gate report does not already carry, and writes its own "new vs main" diff

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Owner approval: YES to a targeted CI optimisation of `rpg-gate-report`, logged on #715 as 6998726529 (in the u24 session, routed through lead-planner). Two changes; neither weakens a check.

1. **Rerun only what is new.** The step "Evaluate (rerun once on a fail or drift, 2 workers, bounded)" calls `rpg_gate_report.build_report`, which reruns every (world, seed) behind ANY fail or drift row. Main carries an inherited red row (#955's V3 flw/42 e55), so every gate run pays the full rerun of all 15 (world, seed) runs. In run 44366629746 the shards took 13-35 min and Evaluate took 57 min. Change: rerun only the runs behind a fail/drift row that is NOT in main's latest gate report (or the known list). A new row still gets its confirming rerun.
2. **A baseline diff the gate writes itself.** The report states "new vs main: none", or the new rows verbatim, in the job summary AND somewhere API-readable (the report JSON, which is an artifact, and the log). This retires lead-planner's manual artifact diff and u24's 403 workaround (#715 6983736199).

Owner conditions: tooling only (`tools/test_architecture` + `.github`); no metric, oracle or baseline change; `rpg_gate_known.yaml` is NOT edited (adding a row stays the owner's call); it lands outside the M1 segments as non-measurement tooling, with testing-planner review; u24 PRs keep the full read until it merges.

## Scope
Design decisions fixed here (lead-planner's two, plus those the investigation must settle):

- (a) **Which main report.** The newest COMPLETED run of `rpg-gate-report.yml` on main that has a readable `rpg-gate-report-<sha>` artifact with a `verdict` field. "Completed" is the run status, not a green conclusion: main's own gate run is red on the inherited row, and its report is exactly the baseline wanted. Runs that are in progress, cancelled, gate-skipped or never reached the report are passed over. The summary states the run id and head sha of the report used. The job gains `actions: read` for the artifact fetch (job-level permissions drop everything not listed).
- (b) **Missing or unreadable.** Fall back to today's behaviour, the full rerun, never to "no rerun". Covers no main run found, no artifact (retention is 30 days), a download error, JSON that does not parse, a report without the expected fields, and a report from a harness or config the current run cannot compare to. The summary says which fallback applied and why.
- (c) **Row identity.** The key and what counts as "the same row" (world, seed, metric id and state; whether a changed state such as drift to fail, or a changed value, makes a row new) is decided in the investigation and written into the report module's docstring. The conservative default: a row is "in main" only if key AND state match; anything else is new and gets its rerun.
- (d) **Instability detection.** A row skipped from the rerun keeps its first-pass state and cannot be marked `unstable`. State this in the report ("not rerun: in main's report, run <id>") so the loss is visible, not silent. The verdict logic is otherwise unchanged.
- (e) **Where the diff lands.** Job summary, report JSON (new field), and a log line, so it is readable without the artifact download.

Proof (owner condition): replay recorded gate reports with the same inputs and get an identical verdict, rows and pass/fail. Recorded copies are kept by lead-planner at `/data/vboxuser/gate-reports/<run id>/` (44281112176, 44316977936, 44339505504, 44353267564, 44366629746). The replay includes cases for: no new row (no rerun, "new vs main: none"), one new row (rerun of its pairs only), main report missing (full rerun), main report unreadable (full rerun), and a row in main that changed state (rerun).

### Selection rule (testing-planner decisions, as folded into the PR)

1. Events: both `schedule` and `workflow_dispatch` runs count. The conclusion does not matter; only "completed" does.
2. "Main" is matched by the branch name `main` (`gh run list --branch main`) AND by sha equality: the report's `sha` must equal the run's head sha, so the report was made from the commit the run is on. A dispatch whose `ref` input points elsewhere is passed over. Ancestry in main's history is deliberately NOT used, because the report job has a depth-1 checkout: a known limit.
3. A dispatch on main whose `ref` input equals main's head at dispatch time DOES count (for example run 44452967207: head a30847030, ref input a30847030). The workflow's "evidence only, not a baseline source" label belongs to `rebaseline` (the baseline candidate) and is unrelated to this rule; it is not an exclusion.
4. Branch runs never count (`--branch main`). A gate-skipped or artifact-less run is passed over; the newest run that has an artifact decides, and if its report is unreadable the answer is the fallback, never an older report.
5. Staleness: a main report whose run `createdAt` is older than `main_report_max_age_days` is not used; the answer is the fallback ("main's newest gate report is N days old, bound B"), never an older report. The bound lives in `tools/test_architecture/rpg_gate_main_report.yaml` (testing-owned, not hashed by the harness; deliberately not rpg's hashed `tests/simulation_quality/rpg_gate/config.yaml`, whose edit would stale the baseline). A missing file, missing key or a value that is not a positive integer is also the full-rerun fallback. The scheduled run is daily, so 3 days tolerates a missed weekend day's schedule drop plus a gate-skipped day without going stale; staleness only ever gives a fuller rerun. The summary line prints "run <id> (<event>, <head8>, <N>d old, bound <B>d)".

## Out of Scope
- Any metric, oracle or baseline change; any edit to `tests/simulation_quality/rpg_gate/baselines` or `rpg_gate_known.yaml`.
- Changing what the verdict means (red only for an unowned or expired fail, or an unstable metric).
- Changing shard count or the shard step.
- Anything in `src/`.
- The `rpg-gate-report.yml` post-merge checks from #588 (download-artifact v8, non-empty per-world docs, report artifact files); they stay open on #631.

## Acceptance Criteria
1. The report names the main report it compared against (run id and head sha), or names the fallback and its reason.
2. With a fail/drift row that is also in main's report and no other, no rerun is performed and the summary reads "new vs main: none".
3. A fail/drift row not in main's report gets its confirming rerun, and appears verbatim in the diff.
4. A missing or unreadable main report gives the full rerun of every pair behind a fail or drift, as today.
5. The diff is present in the job summary, in the report JSON and in the log.
6. Replaying the recorded reports listed above reproduces the verdict, the rows and pass/fail of those runs; the replay is a committed test.
7. `rpg_gate_known.yaml`, the baselines and every metric definition are unchanged (diff shown).
8. The workflow change is validated against the CI-shape tests; `permissions` gains only `actions: read` on the report job.
9. The first real run on main after merge is read and its result recorded: the main report found, the run id used, the time saved. SPLIT OUT (testing-planner review, B2): AC9 can only be read after merge, so this ticket closes on AC1-8 with the PR and AC9 is a post-merge check recorded on #631, as the #588 post-merge items were. It is not dropped.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN (the rerun this narrows)
- TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW
- TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
- TCK-20261118-SLOW-REGRESSION-LANE-RED-SIX-UNOWNED-FAILURES-SINCE-M1 (a separate lane)

## Related Docs
- Owner approval: #715 6998726529. Routed by lead-planner 2026-11-19. u24's 403 workaround: #715 6983736199.
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`
- `.github/workflows/rpg-gate-report.yml`

## Related Stored Artifacts
- Recorded gate reports (lead-planner's copies, not in git): `/data/vboxuser/gate-reports/<run id>/{report,gate-docs-rerun}`. The replay test needs a trimmed, committed fixture of the report JSON, not the host path.

## Related Code Areas
- `tools/test_architecture/rpg_gate_report.py` (`build_report`, `_apply_rerun`, `_harness_rerun`)
- `.github/workflows/rpg-gate-report.yml` (job "RPG gate report")
- `tests/` for the report module and the workflow shape

## Assumptions / Open Questions
- GITHUB_TOKEN with `actions: read` can download another run's artifact via `actions/download-artifact` (`run-id` + `github-token`) or `gh api`; the investigation confirms which, and whether the same-repo token has the access u24's workaround lacked (a 403 outside the workflow).
- Row identity (c) and the treatment of a row whose value moved but whose state did not.
- RESOLVED (owner, #715 6998774083, "Main's report only (Recommended)"): only main's latest COMPLETED gate report decides the rerun skip, matching key AND state. The known list keeps its current ownership/verdict role and does NOT exempt rows from the rerun.

## Durable state, lifecycle and clocks
None: a CI report and workflow change. The new report field is a read model in the gate's JSON artifact (30-day retention).

## Implementation Notes
Dispatch to testing-implementer; testing-planner reviews the PR. Push and PR go through lead-planner's check and the owner. Does not land inside an M1 segment.

## Test Summary
tests/unit/tools/test_rpg_gate_rerun_only_new_rows.py (replay of 5 recorded PR-run reports against main run 44323101062, no-new-row, one-new-row, main missing, main unreadable x5, state changed, value changed, gone rows, known list not exempting, harness/baseline mismatch, CLI, fetch module) plus the workflow-shape test; existing rpg_gate report/candidate/workflow-support/shape tests green (200 passed).

Investigation notes (token access): `gh run list` and `gh run download -n rpg-gate-report-<sha>` fetch another run's artifact; the same-repo GITHUB_TOKEN needs `actions: read` for both. Verified locally only with a user token (main run 44323101062 was downloaded and parsed). The workflow-token path is verified by the first real run (AC9); every failure there is a fallback to the full rerun, so a 403 cannot skip a rerun.
Row identity (c): finding_key (world, scope, id, group, key, tick, seed) AND state. A changed value with the same key and state is not new.
Selection (a): newest completed run with a readable artifact whose report sha equals the run head sha (a dispatch with a ref input is passed over). The newest run that has an artifact decides, so an unreadable one is a fallback, never an older report.

## Files Changed
tools/test_architecture/rpg_gate_report.py, rpg_gate_main_report.py (new), .github/workflows/rpg-gate-report.yml, tests (unit, static, fixtures/rpg_gate_replay), the baseline-format reference doc. rpg_gate_known.yaml, baselines and metrics unchanged.

## Completion Summary
AC1-8 met in the PR. AC9 is split out to a post-merge check on #631 (it needs the first real run on main). The first real run also settles whether the workflow GITHUB_TOKEN with `actions: read` can download main's artifact; any failure there is the full rerun, never a skipped one.
Review changes folded in: a carried row whose pair the rerun covers anyway is read from the second pass (unstable on a mismatch); the main report's age is bounded by `main_report_max_age_days` in a testing-owned YAML (see the Selection rule); the selection rule is stated in the module docstring, here and in tests. Open risk (report docstring): main fixed a row after its last report and the PR re-breaks it within the bound reads as "in main" until main's next report; the verdict still reads first-pass state.
