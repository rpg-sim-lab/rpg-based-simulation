---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER

## Title
Seven people under combat-engage projects die to HAZARD in one cluster within 8 ticks: do BRACKETING moves path into hazard tiles?

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A traced frontier_living_world seed 42 (5000t) on 2026-10-20 for V3 step (ii) (rpg-v3-starvation-threat 29d4d3d07 vs the old gate). It found 10 extra people deaths. None was on the (ii) path: they are trajectory drift from a first divergence at t991, where leader 30 (hunger 99.1) dropped proj_combat_engage_530 under (ii).
Of the 10, seven (ids 8, 10, 1, 2, 4, 11, 9) die by HAZARD in ticks 1281-1288 inside one cluster around (42-45, 43-45). All were on BRACKETING moves under proj_combat_engage_*, with hp 20-120 and hunger 44-64: healthy, not starving. A group walking into a hazard together while bracketing looks like a pre-existing movement defect that the drift exposed. (ii) did not cause it.
Files:
- /mnt/data/scratch-rpg-implementer/v3proof2/trace_b.json, trace_ii.json
- script /mnt/data/scratch-rpg-implementer/v3_trace_an.py

## Scope
- Name the hazard at (42-45, 43-45) on frontier and its declared damage.
- Find out whether BRACKETING / engage movement scores or avoids hazard tiles, compared with ordinary travel (route or terrain cost, D72).
- Find out why several members enter the cluster in the same window: the group following the leader, a shared bracket target, or something else.
- Fix it so that combat movement respects hazards the way travel does, if it doesn't. Measure it as its own step: paired 3 × 42-46, crowded first.

- Second finding (designer 2026-10-20): the group keeps its engagement after its leader leaves. Leader 30 dropped proj_combat_engage_530 at t991 to eat, which is the rule working as written, but the members stayed on proj_combat_engage_* and bracketed on without it. Find out whether a group engagement should end or re-plan when the leader leaves.
- Measure it together with H1 (COMBAT-ENGAGEMENT-HOSTILITY) and the owner's after-v1 hazard-avoidance item (the D75 gap), one measured step, so the three combat-movement changes are not stacked unmeasured.

## Out of Scope
- V3 step (ii) and the hunger/threat gate.

## Acceptance Criteria
- A real-kernel test: a subject on a bracketing move next to a hazard tile does not step into it when a safe alternative exists, or a stated reason why it should.
- The seed-42 (ii) arm no longer loses the 7 people to that cluster, or the remaining deaths are explained.

## Related Tickets
- V3 step (ii) ticket on rpg-v3-starvation-threat
- D72 terrain cost
- H1 TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (measure together)
- the owner's after-v1 hazard-avoidance item (D75 gap)
- disclosure N3 (designer 8e4071cc2) carries this attribution

## Related Docs
- docs/mechanics/02_combat_laws.md (tactical modifiers)
- docs/mechanics/05_world_evolution.md (hazards)

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine tactical movement (BRACKETING)
- hazard damage application

## Assumptions / Open Questions
- Is the hazard visible to perception in the bracketing scorer?

## Implementation Notes
After v1.

## Test Summary

## Files Changed

## Completion Summary

## 2026-10-31 second case and designer rule (rpg-planner)
- urban_political s44 5000t, N14 new2 arm (pre-#795; lane B re-run t1585-1640, /mnt/data/scratch-rpg-implementer-2/n14/out/pack_new2_s44.jsonl, trace_pack.py): subject 13 (hunger 80) pursues non-acting scout 16 from t1608; 2, 5, 1, 6, 9 adopt the same target; REPOSITION/BRACKETING from t1618; the pack enters bandit_road (ROAD, hazard_level 2.0, NATURAL_TERRAIN) at t1624 and all six die t1629-1635 in the same road cells; 16 (fleeing along x=44) is unhurt. Same cluster (42-45, 43-45) as this ticket's frontier s42 case.
- Designer rule direction: a pursuit or BRACKETING step into a cell with hazard_level > 0 is weighed like any other move into a hazard; no engagement exemption.
- Counts first (15-run set, base at or after 6fdfdf555): hazard deaths during engage/BRACKETING moves; whether the pursuer's target itself entered the hazard. The need side of this case belongs to TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED.


- **2026-11-01 scope check (rpg-designer):** this ticket's scope names BRACKETING only. The tactical INTERCEPTING chase target writer (tactical.py:612) is NOT inside it. The ubuntu churn trace (crowded s42) found 3 extra HAZARD deaths on an INTERCEPTING chase along y=40 into terrain draining 20 hp/tick, with no retreat. The F3 f3r crowded HAZARD tier-1 (23→27) may share that path; lane B is checking. If it does: WIDEN the scope to "every engagement/chase move (BRACKETING, INTERCEPTING, any combat target writer) respects hazards the way travel does", and this ticket ranks ahead of F3's landing as an exposed old defect (designer ruling).
  - **Evidence (ubuntu, 2026-11-01):** origin branch rpg-ubuntu-group-id-alloc-impl, file agent-working/staging_artifacts/TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS/evidence/trace15/hazard_intercept_victims_3_11_5.txt (crowded s42).
    - tactical.py:612 writes the chase for victims 3 and 11. Victim 5 moves with target_id 34 and no payload reason; its writer is not shown.
    - From reading the code, unrun: find_intercept_position checks only occupancy for its aim; tactical.py has no hazard term. Whether this move uses route_search.py (which mentions hazard) is unchecked; check it in investigation.
  - **More from rpg-planner-ubuntu's read of the same file:**
    - Entity 3: its group 10026 had shared_target_id 34 until t402, and it chases 34 from t408. target_score (tactical.py ~389-399) boosts a group's shared target, so a group-shared target is a chase source.
    - Entity 11: INTERCEPTING, hp 120 at entry, drain 20 per tick.
    - route_search.py's docstring says hazard is NOT in the route weights. This is documentation only; no route was traced.
    - In base, entity 32 died on a PANIC_RETREAT at hp 17 into the hazard: retreat routing has no hazard weight either.
    - Candidate wider scope: every move kind (chase, group-shared target, panic/retreat, travel) reads hazard in its aim or route. Confirm per writer in investigation.
  - **Correction (rpg-designer, 2026-11-01):** v1 has NO hazard avoidance for any move. Disclosure H1 (docs/plans/systemic_world/v1_disclosure.md) says "Subjects do not leave or avoid a draining regional hazard"; routes weigh terrain cost only (2.128). This ticket is tied to H1, the owner's after-v1 item. It does NOT automatically rank ahead of F3. If F3's tier-1 HAZARD rise has F3 as a causal step onto H1 exposure, an owner row decides: (a) bring H1 forward before F3, or (b) land F3 with the rise disclosed against H1.
  - **Re-scope (2026-11-01):** the widening drafted above is NOT a lane fix. The victim evidence (F3 crowded s44/s46, ubuntu 3/11/5, base 32 PANIC_RETREAT) attaches to H1 / disclosure row N3 as exposure evidence. Whether to widen this ticket to every move kind (chase, group-shared target, retreat, travel) is part of the OWNER's H1 decision, raised through lead-planner-u24 when an owner row comes up. No dispatch without that.
  - **Read finding (rpg-designer via lead, 2026-11-01; read, not measured; line checked by rpg-planner):** target_score (tactical.py:390-428) returns `(not_adjacent, group_bias, is_current_target, -capability_confidence, hp, dist * pressure_dist_mod, id)`. group_bias = 1.0 - trust when the hostile is the group's shared_target_id and trust >= 0.2 (halved again for VANGUARD), else 1.0. So a shared target with trust >= 0.2 outranks the subject's own capability confidence, the hostile's hp and distance; only adjacency ranks above it.
  - **Counts-first step amended:** the target_score probe is taken AT THE PICK TICK, when this ticket's counts step is scheduled, not before.
  - **Evidence (ubuntu churn H1 clusters, crowded s42 and frontier s43):** novice workers in recruit pairs follow a shared target into a chase that ends beside the hazard; the last leg is their own pick. Pointer: origin rpg-ubuntu-group-id-alloc-impl, agent-working/staging_artifacts/TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS/evidence/. The churn Tier 2 is closed as divergence. Still H1/N3 exposure evidence; no dispatch without the owner's H1 decision.
  - **Evidence (retention re-measure, lane C, 2026-11-01; fix 5c6001620 vs base 6fdfdf555, crowded s43):** 7 extra HAZARD victims, all FAIL (trajectory; no retreat on any path; first diff at t142).
    - e13 entered on a tactical INTERCEPTING chase (tactical.py:612).
    - e32, e5, e8, e2, e6 and e4 entered on tactical REGROUP moves (tactical.py:382) into drain tiles at (44,41-43) and (40-42,41-51).
    - HAZARD entry-move table: REGROUP 8 on fix vs 0 on base; INTERCEPTING 2 and BRACKETING 3 are equal on both arms.
    - REGROUP joins INTERCEPTING and BRACKETING as a move leg with no hazard weight. Still H1/N3 exposure evidence; no dispatch without the owner's H1 decision.
    - **On F3 (lane C on-F3 re-measure, base 30307228c vs fix c1f20e1e1; rpg-designer 2026-11-01):** REGROUP hazard entries 0->8 were seen pre-F3 only; not reproduced on F3 (fix 1, base 1). Kept as H1/N3 evidence, not a measured effect of the retreat fix.
  - **Evidence (frontier s43 churn-on-F3, ubuntu groups batch C; rpg-designer 2026-11-01):** e30 kills 4 group members (e12, e36, e9, e19) in t1433-1511; untraced; candidate for groups converging on one strong hostile (target_score group_bias :428). Frontier's 5-seed DEFEAT total fell 35->31, so the s43 rise 3->10 is report-only. e12 was traced and ruled NOT FED (single candidate, group_bias 1.0).
  - **Evidence (urban s42 churn-on-F3, ubuntu groups batch C; rpg-designer 2026-11-01):** e23: VANGUARD BRACKETING (tactical.py:542/:552, t1669/1671/1677) repositions a hp-32 vanguard around its target (17) while it is hit 6 times (t1671, 1674, 1676, 1679, 1681, 1686; 17 hp each); killed t1687. The last bracket walk (t1678) ended on the death tile [41,30], and from t1679 e23 returned AVOID_NO_ROUTE while trying to leave (boxing-in not shown: neighbouring occupants are not in the rows). The branch reads role, not own hp. Provisionally NOT FED (participation in an engagement chosen on a NOT FED pick), pending the hit-attacker rows and the t1668 distances to [41,29].
  - **Child (2026-11-01):** TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (P1): self-defence outranks group_bias in target_score. From crowded s43 e10 (churn-on-F3, ruled FED); ready for either option of the churn owner row.
