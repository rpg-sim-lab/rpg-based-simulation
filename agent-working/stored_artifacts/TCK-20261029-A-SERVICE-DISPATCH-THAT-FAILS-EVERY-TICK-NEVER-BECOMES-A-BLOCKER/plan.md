---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER
artifact_type: plan
tags: []
---

# Plan: a service dispatch that keeps being refused for payment files one typed blocker (K2 fix)

STATUS: PLAN ONLY. No src code until the designer and rpg-planner review it. Standard tier. Branch rpg-k2-service-blocker (worktree /mnt/data2/rpg-wt/k2fix, off main d084b9248). The ticket is in inprogress. Law: STRAT-191-194 (a dispatch that keeps failing becomes a blocker), Bible ch04. Owner order: #715 7159601467 "Skip stage 1, fix K2 then K3". Designer's option (b) a3833b7d defines the own-job counts.

## 1. The rule (one rule, one place)
After N consecutive TYPED payment refusals of the same (action, building) by the same subject, the subject files ONE typed blocker for that way: kind "access", subject str(building id), through the existing inferred-blocker lifecycle (`infer_blockers` -> `reinferred_blockers_update`, blocker_lifecycle.py:38-47, :152-157). The existing suppression then closes the way softly (x0.1 on a score whose target_id equals the subject, score_modifiers.py:53-60).
- Counted reasons: a data list, initially [INSUFFICIENT_GOLD]. NOT counted (transient or already handled): NO_BED_FREE (already ends the way WAY_CLOSED), TARGET_LOCKED, GROUP_ROLLBACK, ACTION_EXHAUSTION (in-tick race). PAYEE_MISSING and others can be added later by data.
- "Consecutive" means no delivered service (accepted result or paid transfer, the A1 definition) for that (action, building) in between, and the previous refusal is at most `refusal_window` ticks old (a data value, default to be proposed 20: two strategic cadences).
- N (`service_refusal_limit`), the window and the counted-reason list are fields of data/content/strategy/blocker_settings.yaml (schema BlockerSettingsDefinition, reader src/content/blocker_settings.py), never code constants. PROPOSED N = 4, the same as `access_giveup_limit` (one setting family, one number a reader already knows); reason: the v6 runs had 14, 14 and 49 failed dispatches, so N = 4 fires within about 40 ticks of the first refusal at the observed cadence of one per 10 ticks, far below 100, while a single busy evening cannot reach it. N is the designer's to fix before data.

## 2. Pieces (each small, in the order they are built)
a. TYPE THE REFUSAL AT ITS WRITER. `with_service` (building_services.py:75-95) is where `service_delta` returns None for a serving building the subject cannot be admitted to. There it stamps `NavigationUpdate.failure_reason = refusal_reason(entity, action)` (INSUFFICIENT_GOLD, the same function EAT already uses, service_admission.py:75-79) and carries the building id, for REST, EAT and SELL where the payment cannot be covered. REST is the v6 case. Untyped refusals with no payment cause (diet, keeps_coin: "no food source at all") stay untyped and out of the rule.
b. THE COUNT, ONE TYPED FIELD. A new typed field on NavigationComponent (next to giveup_records): `service_refusals`, a small tuple of records (action, building_id, reason, count, last_tick), bumped by a new NavigationUpdate field written in the same update as (a), reset when the same (action, building) is delivered, expired by the window. Omitted from the canonical dict while empty, so main's hash is unchanged until a refusal is stamped. It needs the apply fast-path copy (apply.py:738-754) and the checkpoint FIELD_RULES row (to confirm at build time).
c. THE FILING. One new branch in `infer_blockers` (blocker_lifecycle.py): for a record with count >= N and a counted reason, return the access blocker (id `blocker_service_<action>_<building>`, subject str(building), severity from data, default as the congestion blocker). Same dedup and merge as the other branches.
d. THE EXPIRY. The blocker must go away or it closes the way for the subject's whole life. BLOCKER_TIMEOUT ends only a resolve_blocker PROJECT; the only blocker removal today is `quiet_blockers` (congestion only). The plan extends `quiet_blockers` to the service blockers with the SAME existing quiet spell (BLOCKER_QUIET_SPELL_TICKS = 200 of no re-inference). No new lifecycle, no new constant; the spell is refreshed while refusals recur (re-inference refreshes last_seen_tick).
e. THE ROOT WRITER (an option, not in this rule; see Open question 2). `building_arrival_update`'s fatigue branch (building_arrival.py:106-112) issues REST with no purse test.

## 3. What a reviewer should know it does NOT do
It does not hard-close the way: the hunger and fatigue scores keep a 0.2 x floor (score_modifiers.py:63-64), so a subject with nothing else to do can still pick the way. It does not change a subject that is refused fewer than N times, delivered, or whose refusal is not a counted typed reason. It changes the v6 REST case in one more way (a): a broke REST at an inn gets a typed refusal instead of a silent rough rest (see Open question 1).

## 4. Own-job counts (HARD; the designer fixes them before data; proposals)
Per cell, read from typed state only:
(i) blockers filed by the rule (count, by action, by subject), and the first filing tick.
(ii) FALSE FIRES = 0: a blocker filed for a (subject, action, building) that was delivered (accepted result or paid transfer, A1 definition) within the N refusals that filed it.
(iii) STILL LOOPING = 0: the same (subject, action, building) executed undelivered for more than 100 ticks after its blocker was filed while the blocker stood.
(iv) NEUTRALITY: in a cell where (i) = 0, the final state hash EQUALS main's, cell for cell; a different hash with (i) = 0 is a STOP (the fix leaks).
(v) report-only: blockers removed by the quiet spell, refusals typed per reason, refusal records expired by the window.
How (i)-(iii) are read with no new counting kit: the blocker record is typed state (`entity.strategic.blockers`, id `blocker_service_<action>_<b>`, `first_seen`/`last_seen` per the BlockerState fields already there) and the refusal field `service_refusals` is typed state. To get a per-tick history without a kit, the plan adds ONE run-ledger counter family (the typed counters of the paired tool, TCK-20261015) `service_blockers_filed` and `service_refusals_typed` by action, which is how every other behaviour step is measured. If the run-ledger path is not available at the fix commit, the fallback is a plain pass-through reading `entity.strategic.blockers` after each apply (the same hash-neutral pattern as the K kit); that is flagged now so the planner can rule.

## 5. Measurement (for the S9; proposed)
Cells: the 3 gate worlds (crowded_frontier, frontier_living_world, urban_political) x s42 x 5,000 t, main vs fix, plus the urban_political s42 2,400 t cell that holds the v6 rows (the before-fix evidence: K2 = 3 runs). Trees: a NEW fresh archive of main d084b9248 (the neg trees tree and tree2 have data/runs and are not fresh) and a fresh archive of the fix head, both on /mnt/data2, each checked against `git ls-tree -r` (file list, 0 __pycache__, no data/runs) before use. Tool: the existing paired command (tools/rpg_measure/paired.py) with the run-ledger counters, one process at a time behind rpg_host_gate, no pytest during a run. The v6 kit (k2k3_kit_v6) is NOT re-run as a count; its rows are the before evidence only.

## 6. Tests (written with the code; run in a host gap)
- real-kernel test: a broke subject refused N times at an inn files the blocker and the goal stops re-targeting that way (the 0.1 factor on that target; the hunger/fatigue floor stated in the assertion);
- a single transient refusal files nothing; N-1 refusals file nothing; NO_BED_FREE files nothing (not a counted reason);
- a delivered service within N resets the count and files nothing (false-fire guard);
- the window: refusals further apart than `refusal_window` do not accumulate;
- typed round trip of the new refusal field and reason (checkpoint/serialize, canonical dict omitted while empty, hash equal to main with no refusal);
- the filed blocker expires after the quiet spell and not before;
- the data path: N, the window, the reason list and the severity read from blocker_settings.yaml; a missing field is a schema error, not a code default;
- unit tests for `with_service` typing (REST, EAT, SELL payment refusal) and for the untyped refusals staying untyped.
Docs in the same change: Bible ch04 STRAT-191-194 text, a parity ledger row, a divergence entry (number to be taken at build time: the next free after lane C's 2.225 and the death-ends-projects 2.226), mechanisms.yaml goal_hierarchy or the blocker mechanism line for the planner.

## 7. Open questions (rulings needed before code; I do not pick)
1. TYPING A BROKE REST changes behaviour beyond the blocker: today it is a silent rough rest that costs nothing and ends the task as SUCCESS; a typed INSUFFICIENT_GOLD would make the actions phase treat it as a rejection and, unless INSUFFICIENT_GOLD is added to the REST ends-held reasons (`_ENDS_HELD_REASONS_BY_ACTION`, actions.py:44-58), change how the task ends. Which is wanted: keep the rough rest and only count the refusal, or end the REST on a typed refusal?
2. THE ROOT WRITER. Fixing `building_arrival_update` so a fatigue arrival with an unpayable bed ends the project WAY_CLOSED (like `finds_no_bed`, typed and existing) would stop the observed v6 loop with one test and no new field, but it covers REST at inns only and not the general "N refusals of one way" class the law states. Is that wanted in addition, instead, or not at all?
3. SOFT SUPPRESSION. The existing blocker effect is x0.1 with a 0.2 floor for hunger and fatigue, so the way is not closed. Is that enough for "the goal stops re-targeting that way", or should the way filter (`ways_in_reach`) read the blocker?
4. THE #996 NAVIGATION EXPERIENCE ALTERNATIVE. The nearest existing machinery for "N failures of one way, then refuse it until due" is the navigation experience memory with `destination_suppressed` (a typed give-up record per anchor and purpose, with its own due/expiry). Filing a service refusal there would need no new blocker kind, no `quiet_blockers` change and would suppress the target hard, but it is not "a typed blocker" as STRAT-191-194 and the ruling say. The plan follows the ruling; is the alternative worth a design look?
5. N = 4, window 20, severity as congestion: confirm or set.
6. Dead branches in infer_blockers (path_not_found and liquidity_exhausted case mismatch): leave for a separate ticket?

## 8. Order of work after approval
(1) data setting + schema + reader + tests, (2) typed refusal at the writer + unit tests, (3) the count field with the fast-path/checkpoint rows + round-trip tests, (4) the filing branch + expiry + real-kernel tests, (5) docs/parity/divergence, (6) targeted pytest and mypy in the lock env, (7) fresh trees and the S9 measurement. No push; the head sha is reported.

## 9. RULINGS FOLDED IN (rpg-planner and rpg-designer, rpg-designer-k2-fix-plan-rulings.md a73bc655d487395b..., 2026-11-25) AND WHAT WAS BUILT
Approved plan with these rulings; the section 7 questions are answered:
- Q2 BOTH, the root first, as separate commits. (A) = commit 885634b6: ONE shared predicate `service_admission.no_bed_for(state, entity, building)` = `finds_no_bed` OR (the same scope AND not `payment_covers(entity, "REST")`); the scope is finds_no_bed's own by trait (keeps_coin, functional building that declares beds), no kind name and no "person" class; used by the fatigue arrival (`building_arrival`) and the first REST execution (`building_services.no_bed_in_reach`); the arrival ends the project with the existing typed WAY_CLOSED. (B) = the N-refusal blocker, minimal (pieces a-d), built as the next commit.
- Q1 count only: the REST end is unchanged and INSUFFICIENT_GOLD is NOT added to the ends-held reasons; B stamps a typed record only (no failure reason set).
- Q3 the existing soft effect; no `ways_in_reach` change; B(iii) measures it. Q4 no: a blocker. Q5 N = 4, window 20, severity 0.5 (as congestion), all from data. Q6 the dead infer_blockers branches are untouched (a separate ticket by rpg-planner).
- Divergence number: 2.227 (after lane C's 2.225 and the death-ends-projects 2.226); parity row STRAT-358 (STRAT-357 is the death-ends-projects row); ONE divergence entry with separate A and B lines.
Built (B), mirroring the existing give-up records: `src/core/service_refusals.py` (the typed record, the streak count, the id prefix), `NavigationComponent.service_refusals` (canonical-omitted while empty), `NavigationUpdate.service_refusal_add` and `service_refusal_clear` (merge and is_noop), the navigation patch (clear first, then add, cap 8), apply fast path, the checkpoint FieldRule, the fingerprint tail, the data fields (limit, window, reasons, severity: schema + reader, no code default), the writers (`with_service` stamps REST and clears on delivery; `_survival_action` stamps EAT next to its typed refusal), the `infer_blockers` Phase 5 branch (gated by the window so a lapsed streak is not re-inferred), `quiet_blockers` extended to the id prefix.
Own-job counts (fixed by the designer): A(i) WAY_CLOSED ends from the purse half; A(ii) report-only; B(i) blockers filed; B(ii) false fires = 0; B(iii) still looping > 100 ticks = 0; (iv) with A(i) = 0 and B(i) = 0 the final hash equals main's else STOP; (v) DECISIVE: approved kit v6 (SHA256SUMS 018169d6, unchanged) on the FIX tree: K2 runs > 100 ticks = 0 in urban s42 2,400 ticks (before: 3), plus the 3 x 5,000 tick fix cells reported; (vi) report-only counts. How the counts are read is NOT decided here (see the report to rpg-planner): no run-ledger counter was added in this change.
Deviation from plan section 2b (reported): the typed refusal is a record (action, building, tick, reason), not a counter; the streak is computed from the records (the same shape as the give-up records), so no counter reset logic exists besides the clear on delivery.
