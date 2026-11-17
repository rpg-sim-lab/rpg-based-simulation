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

Seventh status pass: 2026-11-17 at `main` efba7d95c (sixth 2026-11-16 at e72270894). Host ubuntu rows come from the ubuntu planners and
repo state. Host u24desktop rows come from `lead-planner-u24`'s #715 records of 2026-11-17; its host page `hosts/u24desktop.md` was last
written 2026-10-29. Status pages for the owner (not in git): the epic status page and the RPG status page linked from the lead's handover.

**Standing directions and pauses (read these before acting on any row):**
- **RPG first** (#715 6911759453): the RPG simulation is the product. It goes first for the heavy slot, host memory, seat time and the
  owner's time. It lifts in M1 Phase 2 (below). On ubuntu the non-RPG seats are low priority (6941107071) and were closed (6941470432);
  on u24 the owner closed 7 idle non-RPG seats.
- **Milestone 1 runs in three phases** (6936893143, superseding the batch and domain-run timing of 6936783692 and 6936842047):
  - Phase 1: implement every item. Each PR passes CI plus the HARD checks (determinism, conservation, hard laws, liveness, the fix's own
    job). There are no full measurement runs per PR. A main commit is recorded as a boundary each time a domain group lands, and merges
    go domain by domain (6937264378). Extinction and liveness are read on the host at each boundary (fallback (a), 6937306315).
  - Phase 2: M1 is code-complete, and RPG-first lifts.
  - Phase 3: back to RPG, which reclaims the host. Boundaries are measured in order (3 worlds x 5 seeds x 5000 ticks), then the strict
    M1 record with the content-alone probe. Deeper issues found in Phase 1 are filed now and fixed here unless they are hard errors.
  - The domain labels are 1 food and liveness, 2 how subjects see and find things, 3 who fights whom, 4 identity, 5 wild births alone
    (6936842047). The target is about two weeks.
- **Phase 1 grade pins** (6941107808): the slow corpus grade anchors are BALANCE pins. A behaviour PR re-pins only what its own change
  moves, with the attribution in its PR body; the host's lead records it on #715 before the push. A move caused by a never-exit loop is
  never re-pinned. A move past twice the pace bar, or in an unpredicted direction, is flagged to the owner.
- **Standing approvals new on 2026-11-17:** S8, CI-fix commits inside an approved PR's scope (6936328520); S9, M1 diagnostic, own-job
  and boundary runs on frozen trees with verified script hashes, recorded by `lead-planner-u24` before each run (6937264378,
  6937352120). Ubuntu heavy runs still need the ubuntu lead's go per run.
- **Re-design discussion** (languages, architecture): still PAUSED (6911604017).
- **Perf** (6556861718): still paused (6911604017). Lifting it needs the seats fence on CPUs 0-3 and steal-time recording first
  (6917238009, `TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS`).
- **`src/engine` work under the next-generation engine and distributed-workers epics:** not before Milestone 1, as both ADRs say.

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| Milestone 1, kinds by properties (`TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC`) | rpg-planner (u24desktop); ubuntu's rpg lane for births and why-it-fights | Phase 1. kind=species step 2 (#946) and step 3 (#949) merged; boundaries B0 = bb26e4e5f, B1 = efba7d95c. Step 4 on u24 lane B. The gate reference is re-baselined to a main run after M1-base (#948). Items 2-6 rule questions all answered (6937049127); rpg-implementer-4 (lane D, u24) takes run 2's segment. M1-base passed on both hosts with equal hashes (6921346060) | none | none | u24: steps 4-5, N10 on lane C (moved from ubuntu, 6936812819), the STALEMATE nav fix, lane D's perception segment. Ubuntu: births (run 5 domain, may start now; owner dispatch) and why-it-fights (run 3) | y: ubuntu births dispatch |
| D73, the free meal is removed (#781) | rpg-planner (u24desktop) | held, conflicts with main; now in run 1, food and liveness (6936842047) | none | its slot in run 1 | rpg schedules it in run 1 | n |
| Rpg gate reads the pooled extinction line | rpg-planner files a testing-track ticket (6937306315) | to file; built in Phase 2 | M1 Phase 2 | RPG first | file now, build in Phase 2 | n |
| AI-first SDLC evolution (`ai-first-sdlc-evolution`) | agent-working (ubuntu) | every open decision made on 2026-11-16 (6910853925, 6911091662, 6911224913, 6911534263, 6913007039). Phases 2-4 filed (#943); tag ruleset applied. Seats closed under RPG first | none | RPG first | dispatch after M1 Phase 1 | y, later: dispatch |
| Next-generation engine (`next-generation-engine`) | architecture-planner-u24 | stage 0 write-up on `perf-planner-next` (backed up at d776f0eee, not merged) | stage 0 write-up | Milestone 1 | the contract spec after stage 0 lands | n |
| Distributed-workers experiment (`distributed-workers-experiment`) | architecture-planner-u24 | design merged (#944); ADR reads per purpose (#945). Children 3-4 shelved; child 3 re-cut after M1 (6917359910) | Milestone 1; contract spec | owner shelving | none until after M1 | n |
| Architecture re-design discussion | architecture-planner | PAUSED (6911604017) | in-flight epics finishing | owner pause | resume when the owner says so | y, later |
| Perf roadmap M0 to M6 | perf-planner (ubuntu, closed) | paused; lift conditions in `TCK-20261116-TIMING-RUNS-SHARE-THEIR-CPUS-WITH-IDLE-SEATS` | none | owner pause | the `nearest_town_tile` hotspot goes to rpg after M1 | y, later |
| Code-health ceiling raises | codebase-planner (not running) | 11 raises approved for kind=species (6933841383, 6934602208), each with a paydown ticket; `lead-planner-u24` holds the fyi | none | seat not running | relay when the seat runs | n |
| ENV-06 calamity escalation producer (`TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT`) | rpg (u24desktop) | todo, P2 | none | owner dispatch | after M1 | y: dispatch |
| Dependabot #811, #813, #881 | rpg-planner | open; clean against main | none | none | land them on rpg's track | y: merges |
| Machine resources, host u24desktop | lead-planner-u24 | M1 runs under S9 on `/mnt/data2`; 7 idle non-RPG seats closed for memory | none | none | none | n |
| Machine resources, host ubuntu | lead-planner | rebooted 2026-11-17 13:33. `/data` 66 % (33 GB free); about 7 GB memory available with 3 seats up (rpg-planner-ubuntu, rpg-implementer-ubuntu, lead); swap empty. Heavy runs one at a time under MemoryMax=3G on CPUs 4-5, the lead's go per run | none | none | none | n |

**Merged since the sixth pass:** #945 (board sixth pass, ADR per purpose), #947 (M1 gate evidence), #946 (kind=species step 2), #948 (gate
re-baseline; closes the nobody-eats epic), #949 (kind=species step 3).

## Residue awaiting the owner

**Never push any of these again.**

- Main checkout: `stored_artifacts/` at the repo root (ignored, old pre-`agent-working/` layout). Archive or keep.
- `/data/vboxuser/aw-held-w46i`, `aw-held-w47a`, `aw-held-w47b`: agent-working-implementer's shard backups, kept until their rows are on main.
- The agent-working-designer worktree holds four untracked SDLC plan copies (two match main). Remove after the designer confirms.
- Remote branch `platform-world-farm-step-one`: recreated by the 2026-11-17 host-stop backup push (6934643401); its PR #926 is merged.
- Local branch `codebase-implementer-ready`: 2 commits on no remote, no seat running.
- Idle worktrees flagged by the seat status tool (over 14 days): `/data/vboxuser/Work/rpg-asset-planner`, `/home/vboxuser/Work/rpg-aseprite-mcp`.
- Host u24desktop: agent-working-planner-u24's scratch worktree, and the stale `rpg-sleeper-lodges` branch (squash-merged as #823).
- Remote branches of merged PRs whose head moved after the merge: not re-counted since 2026-10-14. The lead lists them on request.
