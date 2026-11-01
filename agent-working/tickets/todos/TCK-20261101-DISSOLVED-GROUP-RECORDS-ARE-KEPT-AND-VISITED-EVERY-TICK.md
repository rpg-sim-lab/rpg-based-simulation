---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK

## Title
Dissolved group records stay in the group store for the whole run, and the groups and cooperation phases visit every one of them every tick

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
The ubuntu churn fix (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS, shape A, with the typed next_group_id from TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP) stops reusing and overwriting group ids. Every dissolved group record now stays in the store. rpg-planner-ubuntu recounted its work count from raw (s42, 2000t, non-audit pinned FULL):

| world | store at t2000 (fix; base) | live (fix; base) | records visited, summed (base -> fix) | groups phase median ms/tick |
|---|---|---|---|---|
| crowded | 45; 19 | 2; 0 | 36,411 -> 55,375 (x1.52) | 0.328 -> 0.426 |
| frontier | 110; 28 | 6; 0 | 53,445 -> 102,574 (x1.92) | 0.270 -> 0.990 |
| urban | 79; 19 | 6; 1 | 34,972 -> 74,591 (x2.13) | 0.394 -> 0.631 |

The groups-phase count equals the cooperation-phase count exactly, because both sum the store size per tick. The store grows through the run, so this per-tick work grows with run length. Durable state needs a defined lifecycle (CLAUDE.md Durable State Rule), and this store has no retention bound. It is the same defect class as TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND, which covers projects.

## Scope
Counts first. No rule shape before the counts and the designer's ruling.
1. Store size and live count by tick (t500/1000/2000/5000) per world and seed, on 3 worlds x s42-46, base and the churn-fix head.
2. Per tick: records visited by the groups phase and by cooperation, and how many of those visits are to dissolved records.
3. Every reader of dissolved records (history, observability, read models, id allocation), by file:line. This decides whether dissolved records can be dropped, archived or skipped.
4. Groups and cooperation phase time at 5000t.

## Out of Scope
- The churn fix itself, and its group-id allocation rule.
- Projects retention (TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND).

## Acceptance Criteria
Updated to the designer ruling below (2026-11-01).
- **(a) live-only iteration** (rider on the ubuntu churn lane, ubuntu owner #715 6555733640):
  - The groups and cooperation phases do per-group work for LIVE groups only, through a derived view. No new durable field without a typed FIELD_RULES row.
  - Final state hash equal to the churn tree (without (a)) on 3 worlds, s42, 2000t. Any difference is a finding to rpg-designer naming the reader, not patched past.
  - Count bar, deterministic and from the same run: per-group work visits (groups and cooperation, each) EQUAL the summed live-group count per tick. Any excess is a finding naming what it visits. The derived view's own scan (filtering the store) is reported separately as "store records scanned per tick, summed", disclosed, with no bar.
  - Timing: frontier groups-phase median ms/tick at most 1.5 x base's median (base 0.270, so at most 0.405), or within base's spread. If not met, it is disclosed with the rows. It is not a STOP: deaths and behaviour don't depend on it.
  - Frontier bar A unchanged: R x 11.2 s > 52.2 s fires (iii).
- **(b) retention:** counts per Scope 1-4 (every reader of a dissolved record, and store growth per 1000t at 5000t). The policy is shared with TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND, one rule for both. Not on the critical path.
- **(c) id reuse test:** drop dissolved records, round-trip a checkpoint, and the next id issued is above every id ever issued.

## Related Tickets
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (source; its PR discloses the rate)
- TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP
- TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND

## Related Docs
- docs/simulation/domains/party_contract.md (GroupRecord lifecycle fields)
- docs/simulation/domains/cooperation_contract.md (GroupEvaluator evaluates all groups)

## Related Stored Artifacts
- none yet (ubuntu churn ticket staging artifacts carry the run rows)

## Related Code Areas
- src/systems/world_systems/groups.py (group store, id allocation; groups.py:308 per the id-overwrite ticket)
- src/engine/pipeline_phases/groups.py (groups phase)
- src/systems/social_systems/group_service.py
- cooperation phase / GroupEvaluator

## Assumptions / Open Questions
- Does anything read dissolved records after dissolution? Count 3 answers this.
- Must this land before N14-on-F3 and A' read groups cost at 5000t? Designer.

## Designer ruling (rpg-designer, 2026-11-01)
Two concerns, ruled separately. Priority P2.
- **(a) ITERATION, now:** the groups and cooperation phases iterate LIVE groups only. A dissolved record has no behaviour.
  - Use a derived live view (a status filter, or an index rebuilt from state). Add no new durable field unless cost needs one; if one is needed, it is typed and goes through FIELD_RULES on restore.
  - Acceptance: hash-equal to the churn tree on 3 worlds at 2000t, and the frontier groups phase back near base per tick.
  - Any hash move means a phase reads dissolved records for behaviour. That is a finding to the designer, named with its reader, not something to patch past.
  - (a) should land before any 5000t set that reports tick time (N14-on-F3, A'). It rides right after the churn landing, or with it if hash-equal.
  - If (a) isn't ready when such a set runs, the set reports the groups and cooperation phase ms separately, with the store size at its end, and discloses it. Deaths and behaviour verdicts are not blocked.
- **(b) RETENTION, separately:** dropping or archiving follows ONE policy with TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND. There are not two retention rules.
  - Counts first: every reader of a dissolved group record (contracts holding a group id, memory or beliefs, reputation, SimQ, read models, replay), and store growth per 1000t at 5000t.
  - Not on the critical path.
- **(c) ID REUSE:** a drop cannot cause reuse while next_group_id is persisted typed state. The load seed max(10000, the highest non-squad id + 1) applies only to an old checkpoint without the counter, through FIELD_RULES.
  - Test: drop dissolved records, round-trip a checkpoint, and the next id issued is above every id ever issued.
- The Scope counts above now serve (b). (a) needs no counts beyond its acceptance check.

## Implementation Notes
Filed by rpg-planner 2026-11-01 on the churn work-count finding (relayed by lead-planner-u24). Step (a) taken by the ubuntu owner as a rider on the groups/churn batch (#715 6555733640). (b) and (c) are not dispatched.

## Test Summary

## Files Changed

## Completion Summary

## (a) counter definition and expected sources (rpg-planner, 2026-11-01, set before any reading)
- The counter definition is rpg-planner-ubuntu's, accepted.
  - A VISIT is a loop-body entry before any dissolved-skip guard, counted per pass (election, defection, update_groups, cohesion).
  - The LIVE count is taken from state at phase start.
  - Visits and live count are compared per pass.
- Per pass, excess = visits - live_at_start must decompose exactly into two named sources:
  - **(A) dirty-set dissolved ids skipped at the guard:** each id at most once per pass, and only on its dissolve tick or the next.
  - **(B) same-tick creations and dissolutions:** at most that tick's creations + dissolutions.
- Residual = excess - (A) - (B) must be 0 in every pass of every run.
- A residual, or a dissolved id visited after its dissolve tick + 1, is a finding to rpg-designer. (A) and (B) within their bounds are disclosed, not escalated.

## Step (a) result and rationale correction (rpg-planner, 2026-11-01; rpg-planner-ubuntu's figures, a6902557b)
- **Hash:** equal to the churn tree on 3 worlds at 2000t. FULL on every tick.
- **Count:** met, residual 0. Per pass, visits = live at phase start + same-tick adds (45 / 110 / 79, in election and defection only). update_groups and cohesion equal the live count exactly.
- **Filter scan:** 83.1 / 153.9 / 111.9 store records per tick, 3 scans per tick. Disclosed. It grows with run length.
- **Timing:** frontier groups phase 1.017 ms/tick (0.990 before (a)) against the 0.405 bar, so the timing bar is missed. Single run, with the counter wrapper inside the timer. Disclosed, not a STOP.
- **Rationale correction:** visits fell from about 51 to about 3.7 per tick with no visible fall in time. Walking dissolved records was NOT shown to be where the phase spends its time. The Request Summary's link between visits and the ~1 ms/tick is WITHDRAWN as a cost attribution: the visit count is cut, and the cost cause is open. Attribution runs are pending (one frontier s42 run without the wrapper, one profiling GroupPhase.resolve).
- **Test expectation change OK'd by rpg-planner:** a full-scan tick yields live ids. The test is renamed to say so, plus a pin test that dissolved records stay in the store, the allocator issues above them, and hash and checkpoint include them.

## (b) retention AC addition: id reissue (rpg-planner, 2026-11-01)
- next_group_id is now `int = 10000`, non-optional. It is seeded only on restore of a pre-counter checkpoint, through FIELD_RULES. Every src builder that makes a state with groups passes it explicitly, and GroupCounterBehindStoreError is raised at load and in those builders (ubuntu churn lane, ruled 2026-11-01).
- Any retention drop must never lower next_group_id.
- A state that has had records dropped must never be re-seeded from stored ids. The FIELD_RULES seed max(10000, the highest non-squad id + 1) is valid only for pre-counter checkpoints, which predate any drop.
- The (c) test covers it: drop, round-trip a checkpoint, and the next id issued is above every id ever issued.
- **Amended 2026-11-01:** an AST scan found that no src builder hands in groups. So GroupCounterBehindStoreError runs at RESTORE only, after fill_missing_fields, plus a static guard against any future builder that supplies groups without the counter.
  - Added to (b): a drop must never lower next_group_id, and a state with stored ids at or above the counter is refused at restore.
  - Named gap: a hand-built runtime state with groups at or above 10000 and no counter keeps 10000. That's safe only while records are kept, because the allocator skips taken ids. Retention must account for it.
