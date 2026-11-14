---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Lead board

Cross-domain view kept by `lead-planner`. **Advice only**: the owner sets planner queues, and the lead never
dispatches, reorders a queue or approves anything. Rows are added by the lead. Fourth status pass: 2026-11-14 at `main` d902fc674 (third 2026-10-14 at 6adb134ea). Host ubuntu rows come from the ubuntu planners and repo state. Host u24desktop rows come from `lead-planner-u24`'s live report of 2026-11-14 (its host page `hosts/u24desktop.md` was last written 2026-10-29). The repository moved to `rpg-sim-lab/rpg-based-simulation` on 2026-11-12. Owner approvals are logged on issue #715.

On 2026-11-14 the owner paused the architecture re-design discussion until the epics in flight finish (#715). The rows below follow that order.

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| Milestone 1, kinds by properties (`TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC`, 12 children) | rpg-planner (u24desktop) | in delivery; 0 of 12 children closed on main; the HOLD-mode repair (`TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP`) in progress | roadmap §12.5 done criteria | the HOLD repair's stage 1 waits on a spy fix, plan v4 and a free host | rpg-planner reports child progress; the four old RPG foundation epics fold in per the owner's ruling (#715 6875278006) | n |
| GitHub Project ticket view (`github-project-ticket-view`) | agent-working-planner-u24; P2 by agent-working on ubuntu | P0 #889, P1a #893, P1b #909, P1c #910, P2 #913 merged; Project `rpg-sim-lab/1` | u24's first P2 `--apply` (owner OK #715 6878981927) lifts the u24 write hold | none | agent-working-planner-u24 drafts the P3 timer options with a recommendation (#715 6879676454) | y: P3 timer choice; optional: hide the Host facts field in the Project views |
| Role cards follow design decisions | agent-working (ubuntu) | DONE: #908 (cards cite the amended decisions), #912 (citation index and report-only check) | none | none | none | n |
| Docs as the review source (`docs-as-review-source`) | agent-working (ubuntu) | DONE: #859, #864, #914 (generated `docs/architecture/project_facts.md`); epic in done/ | none | none | none | n |
| Epic dispositions (owner #715 6875225978) | each owning planner | session-layer and session-lead closed (#911); parity-ledger-paydown closed on rpg-planner-ubuntu's branch (4cb3b3e5b, rides its next PR); rpg-regression-gate-report closed on u24 testing-planner's branch (b4dc4acef, rides testing's next PR) | the owning planners' next PRs | none | push with the next PR on each track | n |
| Next-generation engine (`next-generation-engine`) | architecture-planner-u24; stages by rpg, perf and platform | ADR accepted (#853); stage 1 audit landed (#863); contract spec open | world farm (platform, not cut); stage 0 re-measure (perf) | the perf pause (#715 6556861718); stages 3 to 5 wait for M1 | none while the re-design is paused | y, later: the perf pause |
| Distributed-workers experiment (`distributed-workers-experiment`) | architecture-planner-u24 | ADR accepted (#861); design draft written | the owner's review of the whole plan (#715 6731938042) | the owner review gate | none while the re-design is paused | y, later: the plan review |
| Architecture re-design discussion (languages, architecture) | architecture-planner (ubuntu) | PAUSED by the owner on 2026-11-14 | the epics above finishing | owner pause | resume when the owner says so | y, later |
| Perf roadmap M0 to M6 | perf-planner (ubuntu) | paused (#715 6556861718) | none | owner pause | carried follow-ups: SIMQ-ANCHOR-REDS bisect, generator PYTHONHASHSEED, CHECKPOINT-HAS-NO-FORMAT-VERSION | y, later: keep or lift the pause |
| D73, the free meal is removed (#781) | rpg-planner (u24desktop) | HELD under the owner's parking rule; PR conflicts with main | owner ruling | owner hold | re-sync only when it is picked up again | n |
| Idle epics: ai-first-sdlc-evolution (since 2026-10-31), implement-ticket-native-port (since 2026-10-18) | agent-working | idle; SDLC has 2 children blocked on credential and ruleset asks; native port's last child needs a Workflow opt-in | owner asks | owner asks | the owner chooses to resume or close each | y |
| ENV-06 calamity escalation producer (`TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT`) | rpg (u24desktop) | todo, P2, after LAIR-REGION-TRAUMA | none | owner dispatch | none | y: dispatch |
| Dependabot #811, #813, #881 | rpg-planner | open; no conflict with main | none | none | rpg lands them on its track | y: merges |
| Machine resources, host ubuntu | lead-planner | managed: `/` 59 %, `/data` 84 % (85 % gate); Docker store on `/data/containerd`; heavy runs one at a time under MemoryMax=3G on CPUs 4-5 | none | none | free space on `/data` before heavy builds (owner's `Work/groups_base` 9.4 GB, `Work/simq_sweep` 4.3 GB); cap the Docker build cache (runbook step 7) | y: the `/data` cleanup and the build-cache cap |

## Residue awaiting the owner

**Never push any of these again.**

- Main checkout: `stored_artifacts/` at the repo root (ignored, old pre-`agent-working/` layout). Archive or keep. The repo-root `agent-monitoring/` listed on 2026-10-14 is gone.
- Remote branches of merged PRs whose head moved after the merge, and branches with no merged PR: not re-counted since 2026-10-14. The lead lists them on request.
- Host u24desktop: agent-working-planner-u24's scratch worktree on the P2 branch (its removal is the owner's); the u24 disk is critical (4.1 GB free on 2026-11-14, delete list with `lead-planner-u24`).
</content>
</invoke>
