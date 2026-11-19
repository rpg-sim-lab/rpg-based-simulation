---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Title
Milestone 1, kinds by properties: the §12.3 items, the two gate probes and the record

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.3 milestone 1 and its §12.5 done criteria and freeze rule (owner, 2026-10-23, #715 6356123802).

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
Child tickets, one per §12.5 in-scope item, plus the gate probes and the record:
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD
- TCK-20261109-M1-COARSE-PROPERTY-BANDS-AND-THE-APPRAISAL
- TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS
- TCK-20261109-M1-PLACES-ARE-FOUND-FROM-PERCEPTION-AND-MEMORY
- TCK-20261109-M1-ACTIVITY-PERIOD-AND-HAZARD-TOLERANCE
- TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES
- TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
- TCK-20261109-M1-THE-HERO-IS-WORK-AND-THE-GUILD-IS-MEMBERSHIP
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261109-M1-WHO-A-PLACE-REFUSES
- TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE (name-check probe only since 2026-11-15)
- TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS (content-alone probe, split from the line above 2026-11-15; HELD until rpg-planner says the retirements allow green)
- TCK-20261109-M1-RECORD-AND-M1-DISCLOSURE

Also in milestone 1's scope, and tracked by their own tickets: the repairs that close a v1 disclosure row (§12.5). Under the owner's ruling #715 6731822583, the TOWN-RETURN and ESC-SWITCH precedence sites get unit precedence-grid rows only, with a behaviour step only if a count shows a defect. FLEE-LINE stays a full fix.
- Rule work before code (§12.3, "How the path runs"): the catalog text and kernel spec come first. Owner-level choices go to the owner as questions with options and a recommendation when the milestone starts. The forward design's proposed recommendations are not rulings.
- Measured as its own step, once at fold against its parent (decision 76), on the cumulative watch that restarts at v1.1, with the §12.5 per-step stop rules. Those rules and the watch are not trimmed without an owner ruling (#715 6731822583). The measurement tier is stated at dispatch under the standing depth rule (#715 6731764470). It is never below the floor (#715 6731822583): the paired default tier plus every world where an affected known entry lives. A hash-equal check alone proves only an observability change. Decision 76 (§12.3) sets a behaviour step at 3 worlds x 5 seeds x 5000 ticks per arm, and going below it needs an owner ruling.
- Moved in from the closed decision-core epic (TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS), owner #715 6875278006, re-scoped at dispatch:
  - TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE: reads species and occupation, not role. Its role-based drive defaults are dropped (owner). Sequenced with M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD and M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS.
  - TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER and TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH: measured in M1-COARSE-PROPERTY-BANDS-AND-THE-APPRAISAL.
- The de-hero inventory (closed epic TCK-20261001-EPIC-DEHERO-ROLE-GATED-PRIVILEGE-INVENTORY, DUPLICATE, owner #715 6875278006) is carried by M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES's inventory step.

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).
- The free-meal removal (decision 73): its own step before the items (§12.5).

## Acceptance Criteria
- Every child is closed, or moved out by owner ruling, and the record ticket's done items hold (§12.5).
- PERFORMANCE is a first-class non-functional requirement (owner #715 6968328816, 2026-11-18):
  - REGRESSION RULE, for every M1 PR: a significant performance regression the PR introduces is investigated, then either explicitly accepted by the owner or fixed before merge. It is never auto-deferred to a backlog ticket. The PR review checks a before/after cost read of the changed phases whenever the PR changes a per-tick or per-entity path. A regression is significant against perf-planner's quiet-host baseline, once that exists.
  - PERF BUDGETS: the two M1 items that replace measured hot reads each carry a perf budget plus a before/after profile in their own acceptance. TCK-20261109-M1-PLACES-ARE-FOUND-FROM-PERCEPTION-AND-MEMORY replaces nearest_town_tile. PERC-02b, the perceived_neighbours migration under TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS, replaces the nearby_entities reads. The budget numbers wait for perf-planner's quiet-host baseline; no quantitative target is set before it.
  - Temporal scaling (TCK-20261118-TEMPORAL-SCALE-AUDIT-CAN-THE-CURRENT-CALENDAR-CARRY-MULTI-GENERATION-RUNS) is a separate question from execution cost per tick.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD
- TCK-20261109-M1-COARSE-PROPERTY-BANDS-AND-THE-APPRAISAL
- TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS
- TCK-20261109-M1-PLACES-ARE-FOUND-FROM-PERCEPTION-AND-MEMORY
- TCK-20261109-M1-ACTIVITY-PERIOD-AND-HAZARD-TOLERANCE
- TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES
- TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
- TCK-20261109-M1-THE-HERO-IS-WORK-AND-THE-GUILD-IS-MEMBERSHIP
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261109-M1-WHO-A-PLACE-REFUSES
- TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE (name-check probe only since 2026-11-15)
- TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS (content-alone probe, split from the line above 2026-11-15; HELD until rpg-planner says the retirements allow green)
- TCK-20261109-M1-RECORD-AND-M1-DISCLOSURE
- TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE (moved in, #715 6875278006)
- TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER (moved in, #715 6875278006)
- TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH (moved in, #715 6875278006)
- TCK-20261001-EPIC-DEHERO-ROLE-GATED-PRIVILEGE-INVENTORY (closed DUPLICATE into this epic, #715 6875278006)

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
See the child tickets.

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
- 2026-11-16 (rpg-planner): M1-base RECORDED at 9c398a068 (#715 6912633288); gate reference re-baselined to v2 from main run 43895014837 (memo row 97; owner 6920465555, 6920528237). Item order on u24 (rpg-designer, under the M1 pace rules, owner 6912138476): kind=species (dispatched, owner 6920334481; step 2 proven neutral, owner GO 6921470279) → coarse bands and the appraisal → honest perception defaults → places from perception and memory → activity period (A' folded in) → hero-as-work. Name-branch retirement in stages: camp tether after places, faction hostility after ubuntu's why-it-fights, hero role after hero-as-work. Ubuntu lane (owner 6916732562): N10, births (code after kind=species step 2 is on main, species read only through species_of()), why-it-fights after kind=species.
None yet.

- 2026-11-17, MEASUREMENT PLAN (owner rulings on #715): 6936783692 (3 batches) and 6936842047 (5 domain runs) are superseded by 6936893143 (3 PHASES).
  - Phase 1: implement every item; each PR merges on CI + the hard checks + its own job. The extinction line + liveness are read on the host at each domain boundary (6937306315; S9 scope 6937352120).
  - Phase 2: RPG-first lifts.
  - Phase 3: each boundary is measured against the previous one (3x5x5000), then the strict M1 record + the content-alone probe.
  - Slow corpus grade pins: rule (a), 6941107808.
- PHASE 1 BOUNDARY LIST. Rules: a boundary is recorded before every domain switch; no ping-pong; neutral steps are their own segments; docs-, ticket- and registry-only PRs ride the open segment.
  - B0 = bb26e4e5f: main at the start of Phase 1, after #948.
  - B1 = efba7d95c: #949, kind=species step 3, a NEUTRAL segment B0→B1 (K4 IDENTICAL).
  - Open segment after B1: none yet. #950 (doc-only) rides it.

- 2026-11-18, OWNER #715 6971915608:
  - CLOCK REVIEW LINE for every M1 PR, starting now (wording by rpg-designer):
    > **Clock rule (M1 review line, until docs/engine/time_semantics.md lands).** Every read of time names its clock. Domain-time meaning (calendar dates and conversions, day vs night, time of day, ages, and biological or social durations such as gestation, maturity, hunger or sleep) is read ONLY through the authoritative calendar helpers (`src/core/calendar`: is_night, the day bands, the tick-per-day constants). No raw `world_time` arithmetic or copied constants outside them. Explicitly tick-based operations stay valid when their unit and intent are stated where they're used: cadences (`tick % cadence`), keyed draws, cooldowns, windows and timeouts counted in kernel ticks, all on the absolute kernel tick (`state.tick`), never on `world_time` or a wrapped or derived time. A reviewer flags: a domain-time meaning computed from raw ticks or `world_time`; a tick-based rule whose unit isn't named; and two readers of the same meaning using different clocks. This isn't a ban on tick arithmetic, only on competing readings of time.
  - BOUNDARY PERF: the run-1 / Phase 1 boundary read (15 plain runs) also reports wall time and peak RSS per cell against the previous boundary: same config, sequential, pinned, report-only. Flag a median move larger than that boundary's own run-to-run spread. No new runs.
  - 2026-11-19, OWNER #715 6997605774, a BAR-DESIGN RULE (standing, every M1 measurement):
    - Every pre-set check (rule (a) predictions, HARD bars, non-vacuous floors) states its event's EXPECTED PERIOD, in ticks and in calendar time at 2400 ticks/day.
    - It confirms that the run window covers several periods.
    - If the window doesn't cover them, the check is declared UNTESTABLE IN THAT WINDOW. It is never read as a pass.
    - This is rpg-designer's lesson from the births 2000t S9.
    - Companion: the tick-constant inventory (TCK-20261118-TEMPORAL-SCALE-AUDIT-CAN-THE-CURRENT-CALENDAR-CARRY-MULTI-GENERATION-RUNS scope 7).
    - A long-run checkpoint read was NOT approved.
  - EVIDENCE LABELS in every S9 packet: inspected / executable / executed / validated. Kit preflight: TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN.

## Test Summary

## Files Changed

## Completion Summary
