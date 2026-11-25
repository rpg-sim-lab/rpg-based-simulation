---
status: historical
layer: performance
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK
date: 2026-11-24
tags: []
---

# Owner decision "Faster hash, same output" (#715 7123298032, item 2), word for word

Provenance: owner -> lead-planner (ubuntu), logged on #715 as comment 7123298032. perf-planner drafted the brief, and lead-planner relayed it to rpg-planner-ubuntu on 2026-11-24. rpg-planner-ubuntu read the comment through the GitHub API. The whole comment is kept; item 2 is this ticket's.

----- #715 7123298032 -----
**Owner decisions (lead-planner, ubuntu), logged before relay.**

1. **Frontend majors push.** Branch rpg-ubuntu-frontend-majors, head 066c70f7c, on cef537d29. It moves globals 17.14, @types/node 26.6.6, jest-dom 8.0.0 and jsdom 31.0.1 one commit each, plus a test-only GameCanvas.zoom.test.tsx fix that compares exactly at the CSSOM 6-digit form; no component, CI or Node change. Lead reviewed the test diff. Gap: AC2 'lint passes' is not met (pre-existing 21 problems, and CI does not run lint); the follow-up TCK-20261124-FRONTEND-LINT-IS-RED-ON-MAIN-AND-CI-DOES-NOT-RUN-IT is filed in the PR. Owner's answer: "Yes, push 066c70f7c". Scope: push this exact sha, open the PR (pr_render, --check), and poll CI.

2. **Replay hash fix.** Step 0 (GO 7122627318, result /data/vboxuser/perf_runs/obs_attr_result.md sha256 5b06fd29…14cb): the per-tick replay digest is 74.3 ms/tick, 81% of replay cost; the fingerprint is 4.9 ms (noise); final hashes are equal. Owner's answer: "Faster hash, same output". Scope: perf-planner drafts a brief for rpg-planner-ubuntu for a cheaper canonical walk with byte-identical digest output, with replay bytes unchanged as acceptance. The section 7 questions (digest only in audit_mode; snapshot-then-hash exception) wait for that result.

3. **Data deletes.** Owner's answer: "Yes, delete the list". Lead deletes /data/vboxuser/perf_runs (keeping obs_kit and obs_attr_result.md), o3-trace-runs, o3-trace-trees, o3-trace-verify, births-*, gate-reports, saved-monitoring-rows, fe-verify and fe-tmp, checking each path first.
----- END -----
