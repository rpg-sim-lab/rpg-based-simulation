---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH
phase: done
date: 2026-10-29
tags: []
---

# TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH

## Title
An escalated hunger or fatigue goal that has already won scoring still loses evaluate_project_switch to the lock or retention margin of an ordinary current project

## Status
DONE (hand-orchestrated close; PR prepared, local, not pushed)

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-implementer's need probe for :1610 (TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED) on c32db1a41, frontier_living_world s42-46, 5000t. Data: /mnt/data/scratch-rpg-implementer/c1610/need/ (analyze_need.py).
- Orphan path: escalated need orphans lost the switch, hunger 103 times (14 episodes) and fatigue 307 times (19 episodes). escalated_need_wins was true on every loss. Hunger was 88-100 and sleep_debt about 73-80 in the examples.
- Fresh-candidate path ("no_create_other": no record, no create, gate passes): escalated hunger 97, fatigue 102. evaluate_project_switch returned None.

rpg-designer ruling (2026-10-29): this gap already exists in base d914bace7 (intelligence.py about l.1606-1780) and was not caused by :1610.
- In base, an ACTIVE orphan is not SUSPENDED, so a fresh candidate goes through the same switch with the same score and loses the same way.
- :1610 changes only what follows a win: the orphan becomes current instead of a duplicate being left behind.
- :1610 lands with ruling (b) unchanged, once a base count confirms base lost those switches too.

Defect: Bible 04 "Standing Needs Escalate" (SURV-07) says a pressing need outranks ordinary goals. Here the escalated goal has already won scoring against the current project's live score (with_live_current_score). It is then held by retention_margin and/or the lock in evaluate_project_switch, which is the ordinary-goal hold that SURV-07 says the need overcomes.
- Present threats are handled upstream: below the starvation line a present threat removes the escalation (escalation.py l.40), and the tactical pass pre-empts.
- So the switch is the only place an escalated need loses to a non-threat.

## Scope
Counts first, then numbers to rpg-designer through rpg-planner before any fix shape. Use pure probes, with the state hash equal with and without the probe. Run on frontier_living_world s42-46, on main after :1610 lands. Report the orphan path and the fresh path separately, and hunger and fatigue separately:
- (a) Held by the lock (dual condition: normalized score + margin, plus the 0.8 floor) vs held by the base retention comparison (candidate.score > current.score + retention_margin). Give the score, current score and margin bands.
- (b) The current project's kind when the need loses.
- (c) Parked time: ticks from the first loss until the earliest of need met, switch won, or the consequence line reached.
- (d) Any death or collapse (STARVATION, exhaustion) inside a parked window.

Lean fix shape, for the counts to confirm (rpg-designer's call):
- In evaluate_project_switch, a candidate with escalated_need_wins true bypasses both the lock and retention_margin. It still SUSPENDs the current project in the same update.
- "detour" stays the only unconditional structural bypass for other kinds.
- This is a Bug Fix divergence: the code then does what SURV-07 already says. Bible 04 section 2 (Generalized Bypass) needs the escalated-need exemption written in.
- Paired run 3 worlds x s42-46. It goes to the owner only if the paired run STOPs.

## Out of Scope
- Scoring-stage outbids, where the need loses before the switch: TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95.
- Hunger vs retreat on one scale: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE.
- Orphan records: TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS.
- Mapped kinds: TCK-20261028-MAPPED-GOAL-KINDS-NEVER-MATCH-THEIR-OWN-PROJECT-RECORDS.
- Any fix before rpg-designer rules on the counts.

## Acceptance Criteria
- A counts table (a)-(d) per path and per need, sent to rpg-designer through rpg-planner.
- If a fix is ruled: real-kernel tests show that a locked ordinary current project yields to an escalated need, the current project is SUSPENDED in the same update, and a non-escalated candidate is still held. Also: a Bible 04 section 2 edit, a parity ledger entry, a divergence entry (Bug Fix), and a paired run with no unowned STOP.

## Related Tickets
- TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED (:1610, lands first)
- TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION, TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE

## Related Docs
- docs/mechanics/04_strategic_cognition.md: section 2 Interruption Resistance (Generalized Bypass, STRAT-236), Standing Needs Escalate (SURV-07)
- docs/guidelines/intentional_divergences.md 2.40, 2.79, 2.143

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH/ (investigation.md, plan.md, plan_v2.md, test_plan.md, test_plan_v2.md). Investigation, plan and test plan were written before any src change (plan stage, dispatched by rpg-planner 2026-11-25); plan_v2 and test_plan_v2 fold in the designer rulings 972600b6.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (evaluate_project_switch, the project lookup and switch path)
- src/ai/goals/escalation.py (escalated_need_wins)

## Assumptions / Open Questions
Plan, investigation and test plan: agent-working/staging_artifacts/TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH/ (written before code). Open questions Q1-Q5 are in plan.md section 7.
- Sequenced after :1610 lands. Independent of the mapped-kinds and orphan tickets. Not dispatched.

## Durable state, lifecycle and clocks
None new. The rule writes only the existing suspend and current-project updates (`suspend_record`, `current_project_id_set`); the only added module-level object is the immutable `_SWITCH_ENV` (functions and constants), not state. No canonical-dict, checkpoint or hash change except through the behaviour.

## Implementation Notes
- 2026-10-31 DESIGNER RULING (SURV-07 family, from the F3-base family table). THE ONE PRECEDENCE LAW P: at every decision site choosing between a need past its escalation onset and any other goal or act, the need wins unless acting_threat_to(subject) holds (memo row 88: a perceived hostile attacking or pursuing the subject, or one that hit it within the window). No owner row is needed. Whether to flee at all stays on present_threat_to (AGENCY-07); where flight is warranted but the hostile is not acting, a pressing need still wins. ONE shared predicate pair, both reads: need_is_pressing(subject) (need_pull ESCALATION_ONSET line) and need_yields(subject, state) = acting_threat_to. Every site calls them; none re-derives them. ONE PRECEDENCE GRID test: {need pressing y/n} x {no hostile / perceived only / present-not-acting / acting} x site -> winner; each site's ticket adds its rows. Provisional order until harm-per-tag is counted: ENGAGEMENT -> LOW-HP-RETREAT -> TOWN-RETURN -> ESCALATED-SWITCH -> FLEE-LINE.
- THIS SITE: a pressing need bypasses the project lock and the margin (confirms the designer's earlier lean). Uses the predicates landed by ENGAGEMENT-OVERRIDES. F3 base: 1699 ticks / 153 subjects / longest 1.

### Like-for-like probe, 2026-10-29 (lane A, need_probe_base.py; data /mnt/data/scratch-rpg-implementer/c1610/needbase/ and needc/)
- Same wrapper both arms, frontier_living_world s42-46, 5000t, base d914bace7 vs :1610 c32db1a41. Counts per decision tick.
- Strict gate refusal = no live record, no create, count at cap, no escalated need. Base 3081 -> new 6814: combat_engage 533->2433, resolve_blocker 1521->2269, region_stabilization 240->1581, town_return 460->175, harvesting 59->146, fatigue 52->77, recover 113->75, combat_retreat 68->31, hunger 29->25, reach_location 6->2. No hunger/fatigue refusal is escalated in either arm.
- ESCALATED SPLIT (orphan switch, ACTIVE record beside another current project): base hunger lost 57 / won 28 (67% lost), fatigue 28 / 14 (67%); new hunger 103 / 18 (85%), fatigue 307 / 129 (70%). Every loss and win is escalated in both arms. Base totals 85 lost / 42 won; new 410 / 147. Confirms the designer's ruling that this is a base gap; :1610 raises the call count, not the loss rate (fatigue), and hunger rises 67% -> 85%.
- Escalated need no-record/no-create events are all lost switches: hunger 53 -> 97, fatigue 34 -> 102 (non-escalated 3 and 3 in both arms).
- Still owed by this ticket's counts step: (a) lock vs margin, (b) current project kind, (c) parked time, (d) deaths.
- 2026-11-09 OWNER ORDER RULING (#715 6731822583, relayed by lead-planner-u24 and verified by rpg-planner), on the §12.5 order: "Unit rows only (Recommended)". This site gets unit precedence-grid rows only. A behaviour step follows only if a count shows a defect, and that step then needs its own owner yes. FLEE-LINE stays a full fix. Applies with the standing depth rule (#715 6731764470) and the measurement floor (#715 6731822583).

## Test Summary
New: tests/unit/strategic/test_escalated_need_takes_the_project_switch.py (372: 12 behaviour rows plus a 360-combination neutrality oracle, the pre-refactor code copied, with the rule off); tests/tools/test_k3_phase0_kit.py (17) and tests/tools/test_k3_switch_kit.py (10), the controls of the two measurement kits. Mutants (in place, restored): the pressing test off (2 fail), the threat test off (1), the kind exclusion off (3), the rule for every kind (2). Phase 0 kit m3 (stale accepted result counted) fails its control after kit v2.
K3-FORCED SETUP CHANGES (the loser made non-escalated; the claim and assertions unchanged, rpg-planner ruling, lead agreed): tests/unit/strategic/test_project_lookup_live_record_first.py::test_a_different_target_candidate_that_loses_the_switch_changes_nothing_and_creates_nothing and ::test_an_orphan_that_loses_the_margin_leaves_the_current_project_unchanged (sleep_debt 50.0, with a comment citing the ticket, STRAT-359 and 2.228).
COMPLETENESS PINS (from the check's own output): tests/unit/tools/test_mechanism_registry_completeness_check.py total_targets 60 -> 61, bound 56 -> 57 (+systems/strategic_systems/project_switch_rules, bound under goal_hierarchy).
Gates (HEAD 2721f7b38, lock env, host gate each run): full tests/unit -m "not slow and not extra_slow", one directory per process: every directory rc 0 (strategic 1088 passed, tools 1455 passed), motivation collects no test (unchanged), observability per file 0 failures (as one process it segfaults in DuckDB, also on main); code-health `check --summary-for` OK, packages validate 0 problems, import_contracts ci 17 kept 0 broken, `mypy src | mypy_baseline filter` clean.

## Files Changed
src: systems/strategic_systems/project_switch_rules.py (new: `SwitchEnv`, `escalated_need_takes_switch`, `ordinary_switch_allows`; imports nothing from intelligence), systems/strategic_systems/intelligence.py (evaluate_project_switch calls them; `_SWITCH_ENV`), ai/goals/escalation.py (`is_need_kind`).
tests: tests/unit/strategic/test_escalated_need_takes_the_project_switch.py (new), tests/unit/strategic/test_project_lookup_live_record_first.py (two setup rows), tests/unit/tools/test_mechanism_registry_completeness_check.py (pins), tests/tools/test_k3_phase0_kit.py and tests/tools/test_k3_switch_kit.py (new).
tools: tools/rpg_measure/k3_phase0_{spy,summary}.py, k3_phase0_launch.sh, k3_switch_{spy,summary}.py, k3_switch_launch.sh (measurement kits, tools only).
docs and registries: docs/mechanics/04_strategic_cognition.md (Escalated Need Takes The Switch), docs/guidelines/intentional_divergences.md (2.228), docs/parity_ledger/strategic_cognition.yaml (STRAT-359), registries/mechanisms.yaml (goal_hierarchy summary sentence and implemented_by), docs/REGISTRY.yaml.

## Completion Summary
K3 (an escalated hunger or fatigue need that won scoring lost the project switch to an ordinary current project's lock or margin) is fixed: an escalated need with no present threat takes the switch when the current project is not itself a need project (by kind identity); everything else is the unchanged lock-and-margin decision, now in `ordinary_switch_allows`. No new scoring, setting or typed field; `SwitchEnv` passes the scale function, ceilings, urgency floor and threat-resolved test in, so the new module imports nothing from intelligence.
EVIDENCE CHAIN (owner order #715 7159601467 "fix K2 then K3"; the designer's reads): Phase 0 (583d6408): the 10 group-D rows are the winner's own hunger project ended or orphaned in the same update, outside a switch rule (-> TCK-20261123 and TCK-20261028); the K3 baseline is 30 on e39fe7873 (A 12 town_return, B 6 resolve_blocker, C 2 need against need, D 10). DECISIVE (runs 1-3, ec63111f; kit v6 STAGE=neg on the fix head, urban_political s42 2,400 t): K3 13 = A 0, B 0, E 0 (A+B+E 18 -> 0), C 5, D 8. OWN JOB (kit v3, 4 cells): TAKEN/FIRES crowded 11/3, frontier 25/14, urban 5,000 t 23/17, urban 2,400 t 11/7; TAKEN under a present threat 0 in every cell (acting threat 0 too); neutrality not applicable (TAKEN > 0 everywhere; the base plain hashes equal the known e39fe7873 values). GUARD (report-only): 7 rows whose released current was combat_engage, damage within 50 ticks in none.
DISCLOSED: C rose 2 -> 5 (need against need, excluded by ruling Q1, report-only; rows 11-13 are an escalated hunger winner held off by a fatigue project through the ordinary path; a question for the owner's cognition documents, not this ticket). D (8) is the Phase 0 shape, evidence for TCK-20261123 and TCK-20261028. The collapse lines (hunger >= 95, sleep_debt >= 98: 35/38, 41/48, 21/30, 17/26 on the fix arm) are NOT measured against the base: the base arm ran plain only, so no comparison is claimed; they include the never-fed and never-slept cohort. The suspended released projects mostly expire by the 200-tick suspension TTL; the need project stays current a median of 50 ticks. The PR is stacked on rpg-k2-service-blocker (#1015).

