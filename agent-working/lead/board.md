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

Fifth status pass: 2026-11-15 at `main` 0a8f65c3f (fourth 2026-11-14 at d902fc674). Host ubuntu rows come from the ubuntu planners and
repo state. Host u24desktop rows come from `lead-planner-u24`'s reports of 2026-11-15; its host page `hosts/u24desktop.md` was last
written 2026-10-29. Epic-only status pages for the owner (not in git): the epic status page and the per-epic review pages linked from
the lead's handover.

**Pauses in force (read these before acting on any row):**
- **Re-design discussion** (languages, architecture): PAUSED by the owner on 2026-11-14 until the epics in flight finish. The 2026-11-15
  architecture-epic items below are a narrow exception (#715 6889952914). They do not lift this pause.
- **Perf** (#715 6556861718): paused, except the two measurement-only items in the next-generation engine and distributed-workers rows
  (#715 6889952914).
- **`src/engine` work under the next-generation engine and distributed-workers epics:** not before Milestone 1, as both ADRs say.

| epic or batch | owner role | state | depends-on | blocked-by | lead's recommended next step | owner decision needed (y/n) |
|---|---|---|---|---|---|---|
| Milestone 1, kinds by properties (`TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC`, 12 children) | rpg-planner (u24desktop) | in delivery; 0 of 12 children closed on main. The name-switch ratchet now gates `src/world` and `src/core` too (#918, #920) | roadmap §12.5 done criteria | none recorded | rpg-planner reports child progress | n |
| Four October RPG foundation epics (BODY-RECOVERY, DEHERO, SEMANTIC-FOUNDATION, DECISION-CORE) | rpg-planner (u24desktop) | decided by the owner (#715 6875278006): closed, merged into M1, or children moved into M1. The closes and M1 links are filed at u24 `540c8cba0` (backed up at `92029fa73`, #715 6889629052); still `EPIC_SCOPED` on main | the u24 hotfix PR `TCK-20261115-MULTI-RUN-INDEX-FLOW` that carries them | none | land with that PR | n |
| Nobody eats or sleeps (`TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`, epic tier) | rpg-planner (u24desktop) | all children done; AC1 and AC3 unproven (10-31 note). The closing run is owner-approved, read-only, on u24 after the hotfix | that run | none | close if AC1-AC3 pass, else a follow-up ticket | n |
| GitHub Project ticket view (`github-project-ticket-view`) | agent-working-planner-u24; ubuntu's agent-working for its own host | P0-P3a merged (#889, #893, #909, #910, #913, #916); P3b all lanes #917 (0f1c35206); filed date and backlog view #919 (c5d09998c). P3c host timer is PR #921 | #921 | none | after #921: the owner installs the timers (u24 :00, ubuntu :30; #715 6881411615). Ubuntu's first `--apply` runs only on merged main (P3b amendment B) | y: install the timers after #921 |
| AI-first SDLC evolution (`ai-first-sdlc-evolution`) | agent-working (ubuntu) | rescoped by the owner (#715 6889309909 words, 6889318166 answers): the machine account, credential removal, E6b and the M1 merge rule are deferred "for now"; the tag ruleset is kept as `TCK-20261115-SDLC-BASELINE-TAG-RULESET` (the owner applies it). The record is on the pushed branch `agent-working-planner-next` (dbb360234, no PR) | the ticket view epic finishing | none | Phase 5 next, then agent-working-designer brings OD-4/5/6/11/12/13 to the owner; Phases 2-4 are filed after those decisions; R1-R5 deferred | y, later: those ODs; apply the tag ruleset |
| implement-ticket native port (`implement-ticket-native-port`) | agent-working (ubuntu) | resumed by the owner (#715 6889470987). Last child `TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN`; new vehicle `TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT` (owner 6889489078; about 1.7-2.1M tokens). Claim #634 6889505389 | ubuntu's heavy slot (after the ghpair run) | the slot | lead gives the slot go; the owner's Workflow opt-in is asked in the implementer session just before the run. Its PR also carries `agent-working-planner-next` | y: the Workflow opt-in at run time |
| Next-generation engine (`next-generation-engine`) | architecture-planner-u24; stages by rpg, perf and platform | ADR accepted (#853); stage 1 access audit landed (#863); contract spec BLOCKED. **Owner 2026-11-15 (#715 6889952914):** the world farm (child 3) is filed and built by platform-planner; the stage 0 re-measure (child 1) is exempt from the perf pause | the stage 0 and audit results for the contract spec | the re-design pause for everything else; stages 3-5 wait for M1 and, for the executor, Gate B | world farm and stage 0 proceed; the rest waits | n |
| Distributed-workers experiment (`distributed-workers-experiment`) | architecture-planner-u24; children by testing, perf, rpg, platform | ADR accepted (#861, #715 6777076537); design draft written. **Owner 2026-11-15 (#715 6889952914):** child 6, the evidence guard, is filed and built (testing, with rpg); child 2's data-cost measurement is exempt from the perf pause; children 3, 4 and 5 are filed as tickets only | children 3-5 filed | the owner's whole-plan review (6731938042) gates children 3-5's implementation | file children 3-5, then bring the whole plan to the owner | y, later: the plan review |
| Architecture re-design discussion (languages, architecture) | architecture-planner (ubuntu) | PAUSED by the owner on 2026-11-14 | the epics above finishing | owner pause | resume when the owner says so | y, later |
| Perf roadmap M0 to M6 | perf-planner (ubuntu) | paused (#715 6556861718), except the two measurement items above (6889952914) | none | owner pause | carried follow-ups: SIMQ-ANCHOR-REDS bisect, generator PYTHONHASHSEED, CHECKPOINT-HAS-NO-FORMAT-VERSION | y, later: keep or lift the pause |
| Epic dispositions (owner #715 6875225978) | each owning planner | session-layer, session-lead and docs-as-review-source closed (#911, #914); RPG regression gate report closed in #918; parity-ledger paydown closed on rpg-planner-ubuntu's seat branch (`6b9241193`, no PR) | rpg-planner-ubuntu's next PR | none | land with that PR | n |
| ubuntu RPG group-combat batch (`TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER`, `TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET`) | rpg-planner-ubuntu | built (437160ac3, not pushed); owner go #715 6883358041. The paired deaths and hold-line run (designer ruling (a) on #634) holds ubuntu's heavy slot until about 19:00 | that run | none | after it: rebase onto main, run the name-switch test, and the push ask shows the batch's diff vs main is byte-identical to 437160ac3's | y: the push |
| D73, the free meal is removed (#781) | rpg-planner (u24desktop) | HELD under the owner's parking rule; conflicts with main | owner ruling | owner hold | re-sync only when it is picked up again | n |
| ENV-06 calamity escalation producer (`TCK-20261114-ENV-06-CALAMITY-ESCALATION-PRODUCER-IS-NOT-BUILT`) | rpg (u24desktop) | todo, P2, after LAIR-REGION-TRAUMA | none | owner dispatch | none | y: dispatch |
| Dependabot #811, #813, #881 | rpg-planner | open; no conflict with main | none | none | rpg lands them on its track | y: merges |
| Machine resources, host ubuntu | lead-planner | `/` 59 %, `/data` 56 % (85 % gate); Docker store on `/data/containerd`, build cache capped at 3 GB; heavy runs one at a time under MemoryMax=3G on CPUs 4-5 | none | none | the slot queue: ghpair (until about 19:00), then the native-port run, then the perf measurements | n |

## Residue awaiting the owner

**Never push any of these again.**

- Main checkout: `stored_artifacts/` at the repo root (ignored, old pre-`agent-working/` layout). Archive or keep.
- `/data/vboxuser/aw-held-w46i`: agent-working-implementer's backup, kept until `ba1f5d013`'s rows are on main.
- The agent-working-designer worktree on `agent-working-designer-sdlc-evolution` (last commit 2026-10-30) holds four untracked SDLC plan copies. Two match main; two look like the pre-review drafts (not compared line by line). Remove after the designer confirms.
- Host u24desktop: agent-working-planner-u24's scratch worktree (its removal is the owner's).
- Remote branches of merged PRs whose head moved after the merge: not re-counted since 2026-10-14. The lead lists them on request.
