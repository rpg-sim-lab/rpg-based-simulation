---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN
phase: done
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN

## Title
Run one small ticket through the native implement-ticket and verify gate outcomes

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES.

## Scope
Epic AC1 and AC3: no `bash(` in implement-ticket.js and one native run of a small ticket with correct gate outcomes (including a deliberately failing gate). Requires the user's own Workflow opt-in at dispatch time.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. `tools/workflow_bash_sites.py` reports 0 real sites. **MET** (0 at 3d1a05c36 and at e2986e03a).
2. One native run completes with correct pass and fail outcomes, recorded as evidence in `.jsonl`/`.md`. **PARTLY MET**: the fail path and the plan gate behaved correctly, but no run completed end to end (see the Test Summary).
3. The orchestrator backstop agrees with the run's gate verdicts. **MET for the sites reached** (see the Test Summary); Parity, Verify and Finalize were not run natively.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (parent epic)
- TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN (outcome: adopt for gates only, plus backstop)

## Related Docs
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.md`
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/`
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- None beyond the parent epic's.
- **2026-10-06, blocked by the environment, not run.** The owner approved this run on 2026-10-06 (answering "Run it"). Two attempts never reached Scope: the named workflow resolved the main checkout's `implement-ticket.js` (no attested sites) and returned the old `NATIVE_GATE_SITES_UNPORTED` refusal; a `scriptPath` run of the worktree file died with `agent type 'ticket-scoper' not found`, because the session was launched from `/mnt/data/Working` and the repo's `.claude/agents` were not registered. About 240k tokens were spent; no gate was reached and no repo state changed. A rerun needs a session started in a repo worktree, after the PR that lands `TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES` merges, with `scriptPath` pointing at that tree's `implement-ticket.js`. The refusal run rows stay in the monitoring shard as a true record.

## Implementation Notes
**Run plan v3 (agent-working-planner, 2026-11-15; supersedes the 10-09 plan's vehicle, landing and environment lines).**
- Owner: resume (#715 6889470987). Vehicle chosen, with the cost stated (#715 6889489078). **The Workflow opt-in is not given yet.** It is asked in the implementer session immediately before the fail run; the pass run is a second ask unless the owner covers both in that one answer. The 10-06 and 10-09 opt-ins do not carry over.
- Vehicle: TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT (standard, P2), a real one-function fix in tools/search_mcp.py and tools/knowledge_search.py with tests. Standard tier, so every gate site is reached.
- Preconditions, checked at the run's base by the implementer and reported before the opt-in ask:
  1. `python3 tools/workflow_bash_sites.py .claude/workflows/implement-ticket.js` reports 0 sites. True at origin/main 0f1c35206.
  2. The run starts from the agent-working-implementer session, launched in its own repo worktree, so `.claude/agents` resolve (the 10-06 `ticket-scoper not found` failure).
  3. `scriptPath` is that worktree's `.claude/workflows/implement-ticket.js`, on a branch cut from origin/main, `git diff origin/main -- .claude/workflows/` empty. Never use the named workflow; it resolves the main checkout (10-06 failure 1).
  4. The run branch is cut from origin/agent-working-planner-next (dbb360234 or later), so the PR also carries the SDLC rescope commits and the shard rows the implementer carried (its local ba1f5d013, rebased). No other session runs a Workflow, perf run or heavy test run on ubuntu at the same time; lead-planner gives the slot. The pipeline's Test phase ran 4,691 tests in tests/tools in the 10-09 run, outside the usual 3G cap, so lead decides whether that is acceptable or the run waits for a quiet host.
  5. No project_sync --apply (HOLD-v4); the run doesn't need one.
- Fail run: add the unregistered tag `native-run-probe` to the vehicle's frontmatter, uncommitted, in the run worktree. Run with `ticket_id` = the vehicle. Expected: `Scope:tag_registry.check_tags_registered` FAIL through `shAttested('tag_check')`, `TAGS_NOT_REGISTERED`, Scope only. 10-09 measured 293,821 tokens and 81.9 s. If the scoper drops or rewrites the tag instead of reporting it, stop and report: that is a finding.
- Pass run: remove the probe tag and rerun the same `ticket_id`. Expected: every reached gate PASS (or a real failure handled by the pipeline's own loop), ending DONE. Estimate 1.4-1.8M tokens and 35-60 min: the 10-09 pass run used 925,732 tokens and 27.8 min before dying at the Test site's transport, and Test, Parity, Verify and Finalize remain. If it dies on a harness fault (WORKFLOW_ERROR, attestation mismatch twice, agent not found), stop, record it, and don't retry without a new owner ask. The vehicle is then hand-finished, as on 10-09.
- New since 10-09, and never run natively: the TRANSPORT-LOSSY fix (f446a2bc8: `cmd_sha`, short `gate_cli.py` calls, one retry), and the 11-11 docs-as-review changes to implement-ticket.js (#859, #864; +23/-2 lines). A failure in either is a finding about the pipeline, not about the vehicle.
- AC3 per run: compare the orchestrator backstop's verdicts with the attested rows in `gate_verdicts.jsonl`, and record any disagreement.
- Evidence in this ticket's Test Summary, per run: workflow run id, each gate site's outcome, the backstop comparison, tokens, wall-clock. This is also input to OD-5 (retire the pipeline), which agent-working-designer brings to the owner later.
- Landing (replaces "local batch, no push"): one PR on the agent-working track closing the vehicle and this ticket. If AC2 and AC3 hold, it also closes the epic TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT and moves `todos/implement-ticket-native-port/` to `done/`. The PR carries the SDLC rescope commits. Push and merge are owner asks on the exact SHA.

**Run plan (planner, 2026-10-09; owner opt-in for this run given in the planner session 2026-10-09, "go with your recommendations").**
- Precondition (checked 2026-10-09): `tools/workflow_bash_sites.py .claude/workflows/implement-ticket.js` reports 0 sites at main 42ce987b6. Re-check it at the run's base.
- Environment, from the 2026-10-06 failure: the run must start from the `agent-working-implementer` session, which was launched in a repo worktree so `.claude/agents` resolve. Pass `scriptPath` = that worktree's `.claude/workflows/implement-ticket.js`, synced to origin/main. Do not run the named workflow, which resolves the main checkout.
- Vehicle: `TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES`, a real small fix at standard tier so that every gate site is reached.
- Deliberate failing gate (AC2), done in two runs, because a gate that fails also stops the run:
  1. **Fail run.** Add one unregistered tag to the vehicle (e.g. `native-run-probe`; do NOT register it). Run with `ticket_id` = the vehicle. Expected: `Scope:tag_registry.check_tags_registered` FAIL through `shAttested('tag_check')`, return `TAGS_NOT_REGISTERED`, and a monitoring run row; Scope only, so it's cheap. If the scoper drops or rewrites the tag instead of reporting it, stop and report: that is a finding, not something to route around.
  2. **Pass run.** Remove the probe tag and rerun the same `ticket_id`. Expected: every reached gate is PASS, or a real failure handled by the pipeline's own loop, and the run ends DONE.
  Both runs together are the evidence for AC2. The "one native run" wording means one real ticket through the native path, with the failing probe as its first attempt.
- AC3: for each run, compare the orchestrator backstop's re-run verdicts with the run's attested gate verdicts in `gate_verdicts.jsonl`, and record any disagreement.
- Evidence goes into this ticket's Test Summary: run ids, each gate site's outcome, the backstop comparison, and the measured tokens and wall-clock per run.
- Landing: both tickets land on the local batch branch `agent-working-small-fixes-batch`, with no push and no PR (owner, 2026-10-08). Closing this ticket also closes the last child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`; close the epic and move the folder to `done/` per CLAUDE.md.

## Test Summary
**2026-10-09, attempt 1 (planner record from the implementer's reports):**
- Fail run wf_2b717fc9-c97: TAGS_NOT_REGISTERED as planned. Gate rows: `tag_check` attested PASS (exit 0), then
  `Scope:tag_registry.check_tags_registered` FAIL, blocking (unregistered=1), then `Scope:conflicts` PASS. The scoper
  kept the probe tag. 7 agents, 293,821 tokens, 81.9 s. Cost observation: the tag check runs after the scoper and
  five shell or monitoring dispatches; monitoring-write is the largest agent.
- Pass run wf_e2dc6921-bdd: WORKFLOW_ERROR, `GATE_ATTESTATION_FAILED test_scope_coverage: wrong command`. Before that,
  attested `tag_check`, `plan_unresolved_questions` and `doc_staleness` all PASS, and the Test agent reported 4691
  passed in tests/tools/. The agent truncated the base64 command, so the shell saw an unterminated quote (exit 2). The
  verifier failed closed. 20 agents, 925,732 tokens, 27.8 min. AC3 is incomplete: the Test, Parity, Verify and
  Finalize sites were never reached.
- Result: BLOCKED on TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY. The vehicle is hand-finished instead (its
  closure records that path). A rerun needs a new vehicle ticket and the owner's Workflow opt-in.

**2026-11-15, run plan v3 (vehicle TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT; the owner's opt-ins were asked in the agent-working-implementer session just before each run; worktree `scriptPath`, never the named workflow):**

| run | id | verdict | agents | subagent tokens | wall time |
|---|---|---|---|---|---|
| fail (probe tag `native-run-probe`) | wf_b59e5ed2-5d3 | `TAGS_NOT_REGISTERED` at Scope, as designed | 8 | 449,009 | 80.8 s |
| pass attempt 1 | wf_d6a35058-f5d | `NEEDS_HUMAN_INPUT` at the Plan gate (the AC3 CLI-rule question; a correct stop) | 11 | 673,649 | 224.6 s |
| pass attempt 2 | wf_f48f4fae-569 | `TESTS_FAILED` at Test | 21 | 1,282,824 | 2,907 s (48.5 min) |

The fail run cost 449k tokens against 294k on 2026-10-09 (about 1.5x). Lowest MemAvailable was 4.09 GB in attempt 1 and 3.71 GB in attempt 2 (5 s watcher, never below the 1.5 GB stop line). The shared-host window with rpg's scoped pytest was 66 s, 12:20:00Z-12:21:06Z, before attempt 2's Test phase.

**Gate sites reached, per run** (`gate_verdicts.jsonl`, `agent-working-native-port-run` shard):
- Fail run: `start_sha` and `tag_check` attested PASS; `Scope:tag_registry.check_tags_registered` FAIL (blocking); `Scope:conflicts` PASS. Scope only.
- Attempt 1: `start_sha`, `tag_check`, `plan_unresolved_questions` attested PASS; backstop `Scope:tag_registry.check_tags_registered` PASS and `Scope:conflicts` PASS; `Plan:...plan_has_unresolved_questions` FAIL (blocking), which is the question that went to the owner.
- Attempt 2: attested `start_sha`, `tag_check`, `plan_unresolved_questions`, `doc_staleness`, `test_scope_coverage` all PASS; backstop PASS for `Scope:tag_registry...`, `Scope:conflicts`, `Plan:...`, `Implement:...doc_staleness_check`, `Test:files_changed_vs_git`, `Test:...test_scope_coverage_static`; agent verdicts `Review` and `Architecture-Verify` APPROVED; `Test:passed` FAIL (blocking).

**AC3, backstop against attested rows, per run:** the fail run's attested `tag_check` exited 0 (the command ran) while the backstop's `check_tags_registered` returned FAIL with `unregistered=1`; that is the designed split (an attested row reports that the command ran, the backstop reports the verdict). In attempts 1 and 2 every attested PASS has a matching backstop PASS, with no disagreement. The first full native run to reach the `test_scope_coverage` site, which died on the truncated command on 2026-10-09, now passes it: the TRANSPORT-LOSSY fix (f446a2bc8) held for five attested sites in attempt 2.

**Result:** no run reached DONE. Attempt 2 ran the attested gates through Test and ended `TESTS_FAILED`: one real failure (a hardcoded literal in the vehicle's new test) plus 57 failures and 7 errors, all `OSError: Cannot allocate memory` from the Test agent's uncapped single `tests/tools` process; the same tests passed when run capped (6,025 passed across six chunks). Parity, Verify and Finalize were never run natively. The owner chose to hand-finish the vehicle (#715 6894904885).

**What the native run reported against what was checked** (input to OD-5):
- "No deviations from the plan": false, plan test 4 was dropped.
- Live check "40 changed, 57 new": re-run gave 41 and 58 (the main checkout kept changing).
- Doc said "the CLI's `--corpus-root` overrides": wrong, `query` has no such option.
- "61 passed" and "88 passed, 28 deselected": consistent with the capped runs.
- The Test agent ran the whole of `tests/tools/` in one uncapped process although the ticket said to run scoped files (filed: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS).

## Files Changed
- agent-working/tickets/done/implement-ticket-native-port/TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN.md (this ticket; evidence only)
- agent-working/agent-monitoring/data/2026-W46/agent-working-native-port-run.{events,gate_verdicts,runs,tools}.jsonl (the runs' rows)

## Completion Summary
Three Workflow runs on the vehicle TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT: the fail run and the plan-gate stop behaved as designed, and the third ran the attested gates through Test before ending `TESTS_FAILED`. AC1 is met. AC2 is partly met and AC3 is met for the sites reached; no run completed end to end. The vehicle was hand-finished on the owner's answer (#715 6894904885).

Known gap: Parity, Verify and Finalize have never run on the native path, so their attested gate sites are untested. The Test agent's uncapped `tests/tools` run is filed as TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS.

