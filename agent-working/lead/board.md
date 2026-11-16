---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Lead board

Cross-domain view kept by `lead-planner`. **Advice only**: the owner sets planner queues, and the lead never dispatches, reorders a queue
or approves anything. Rows are added by the lead. Owner approvals are logged on issue #715, and each row cites the comment it rests on.

Sixth status pass: 2026-11-16 at `main` e72270894 (fifth 2026-11-15 at 0a8f65c3f). Host ubuntu rows come from the ubuntu planners and
repo state. Host u24desktop rows come from `lead-planner-u24`'s reports of 2026-11-16; its host page `hosts/u24desktop.md` was last
written 2026-10-29. Status pages for the owner (not in git): the epic status page and the RPG status page linked from the lead's handover.

**Standing directions and pauses (read these before acting on any row):**
- **RPG first** (#715 6911759453): the RPG simulation is the product. When RPG work competes with agent-working, perf or process work for
  the heavy slot, host memory, seat time or the owner's time, RPG goes first.
- **Milestone 1 pace** (direction 6911746837, decision 6912138476): HARD checks block (determinism, instruments never change a run, hard
  world laws including conservation and one entity per tile, the fix's own job by its pre-written counts, liveness, one pooled extinction
  line over kinds alive in at least 3 parent seeds, kept by 6919222181). BALANCE checks are report-only, with a flagged line in the PR at
  twice a bar or the third trip in a row. Balance is judged after the foundation and core features, against the owner's "varied but
  reasonable" bands (6892558147).
- **Re-design discussion** (languages, architecture): still PAUSED (6911604017).
- **Perf** (6556861718): still paused (6911604017). Released from it: the world-generator hash-seed fix (done, #940) and the checkpoint
  format version (done, #942). Lifting the pause needs the seats fence on CPUs 0-3 and steal-time recording first (6917238009,
  `TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS`).
- **`src/engine` work under the next-generation engine and distributed-workers epics:** not before Milestone 1, as both ADRs say.

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| Milestone 1, kinds by properties (`TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC`, 12 items) | rpg-planner (u24desktop); ubuntu's rpg lane for its share (6916658273) | 1 of 12 items closed (the name-check probe). Repair chain 5 of 10 done; under the new pace nav and the N10 slot leak are HARD repairs beside the items, D80C is tooling before the record, A' folds into the activity-period item, the rest is backlog. M1-base recorded on u24 at 9c398a068 (18/18, self-check spread 0); its post-base merge check is identical at s42 on all 3 gate worlds. Ubuntu's own copy is recording (frontier s42 final hash matches u24's). The gate report at 9c398a068 is green (15 V1 fails, all known, the free-meal ticket). | M1-base | none | u24: kind-always-means-species first, then the items in epic order. Ubuntu: N10 (dispatched 6916732562; designer's lifecycle rule v1.1, the harm join withdrawn), the wild-births rule work (6916777455), why-it-fights after kind=species | n |
| D73, the free meal is removed (#781) | rpg-planner (u24desktop) | held; the owner ruled its "until earning works" condition met (6916777455). Now a separate step before 2026-12-31, off the items' path | none | its slot | rpg schedules it | n |
| Nobody eats or sleeps (`TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`, epic tier) | rpg-planner (u24desktop) | closing run passed (no starvation; survival at tick 1,100 from 0 to 38 of 55 and 11 of 38). Still in `todos/` | none | none | close in u24's next RPG PR | n |
| AI-first SDLC evolution (`ai-first-sdlc-evolution`) | agent-working (ubuntu) | every open decision made on 2026-11-16: OD-4 a three-layer close check; OD-6 Codex kept as legacy; OD-11/12/13 as recommended (6910853925); OD-5 retire the pipeline in Phase 4 after the close check runs 2 weeks with a mechanical test-scope floor and an architecture verdict on src PRs (6911091662). Docs truth (6911224913, 6911534263) and agent practice (6913007039) decided. Phases 2-4 filed (#943). Tag ruleset applied (6917273988) | none | RPG first | dispatch only on the owner's go | y, later: dispatch |
| GitHub Project ticket view (`github-project-ticket-view`) | agent-working-planner-u24 | every part merged; both hosts' timers run; close approved (6892295458). Still in `todos/` | none | none | close in agent-working-planner-u24's next PR | n |
| Next-generation engine (`next-generation-engine`) | architecture-planner-u24 | world farm done (#926); stage 0 re-measured on 2026-11-16 (urban 6.5 %, crowded 7.8 % spread; frontier inconclusive at 56 %, swap ruled out). Write-up on `perf-planner-next` c0c1a9332, not merged | stage 0 write-up | Milestone 1 | the contract spec after stage 0 lands | n |
| Distributed-workers experiment (`distributed-workers-experiment`) | architecture-planner-u24 | reviewed: option B and a multi-mode core (6910997558). Child 2 conclusive: the pickle codec costs 44-146 times a chunk's compute. Children 3 and 4 shelved, no-go as designed; child 3 re-cut after M1 and the contract spec as a worker-resident replica with typed deltas ("R5 now, R3 later", 6917359910). Design merged (#944). The ADR's per-purpose amendment rides this pass | Milestone 1; contract spec | owner shelving | none until after M1 | n |
| Architecture re-design discussion (languages, architecture) | architecture-planner | PAUSED (6911604017) | in-flight epics finishing | owner pause | resume when the owner says so | y, later |
| Perf roadmap M0 to M6 | perf-planner (ubuntu) | paused (6556861718, 6911604017); lift conditions in `TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS` | none | owner pause | carried: the SimQ anchor-reds bisect stays parked; the `nearest_town_tile` hotspot goes to rpg after M1-base | y, later |
| ENV-06 calamity escalation producer (`TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT`) | rpg (u24desktop) | todo, P2, after LAIR-REGION-TRAUMA | none | owner dispatch | after M1's early items | y: dispatch |
| Dependabot #811, #813, #881 | rpg-planner | open; no conflict with main | none | none | rpg lands them on its track | y: merges |
| Machine resources, host ubuntu | lead-planner | `/data` 60 % before ubuntu's M1-base (~5-10 GB of kept events); swap about 3.9 of 8 GB; Claude seats are not fenced off CPUs 4-5. Heavy runs one at a time under MemoryMax=3G on CPUs 4-5, the lead's go per run | none | none | list M1-base's event dirs for the owner after it reports done | n |

**Merged on 2026-11-16:** #929, #930, #932, #933 (group combat), #934, #935, #937, #931 (HOLD), #936 (restore run id), #939 (gateway docs
archived), #940 (generator hash seed), #942 (checkpoint format), #941 (D1), #938, #943 (agent-working batch), #944 (distributed design).

## Residue awaiting the owner

**Never push any of these again.**

- Main checkout: `stored_artifacts/` at the repo root (ignored, old pre-`agent-working/` layout). Archive or keep.
- `/data/vboxuser/aw-held-w46i`: agent-working-implementer's backup, kept until `ba1f5d013`'s rows are on main.
- The agent-working-designer worktree on `agent-working-designer-sdlc-evolution` (last commit 2026-10-30) holds four untracked SDLC plan copies. Two match main; two look like the pre-review drafts (not compared line by line). Remove after the designer confirms.
- Ubuntu worktrees made on 2026-11-16, each removed by the owner once its work lands: `.claude/worktrees/m1base-tool` (after ubuntu's M1-base and its post-base check), `.claude/worktrees/lead-adr-per-purpose` (after this pass merges).
- Host u24desktop: agent-working-planner-u24's scratch worktree, and the stale `rpg-sleeper-lodges` branch (squash-merged as #823).
- Remote branches of merged PRs whose head moved after the merge: not re-counted since 2026-10-14. The lead lists them on request.
