---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-A-BROKE-BODY-CAN-EARN-BY-TAKING-A-QUEST

## Title
A broke body that can take quests earns money by taking one at a guild or similar building, not only by a work shift

## Status
OPEN (designer rulings recorded 2026-11-23; dispatch after #995 closes)

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner direction, 2026-11-23 (#715 comment 7083407878, relayed by the lead): earning money must not
be only `WORK_SHIFT`. A quest at a guild or similar building is a main earning way, and work at
other buildings stays valid. Quest kinds are many and extensible: collect resources, kill N (with a
quest item as evidence), clear a camp, explore, and so on. Quests may in future be given by
intelligent entities that form a society, and may also spawn from simpler logic. Quest takers are
intelligent bodies. The owner said "maybe only humanoid", but the taker rule stays kind-neutral as a
declared capability. The designer rules which property it is.

Facts at main ff27ac4b5 (the ubuntu lead's read, inspected):
- `src/ai/goals/ways.py::WayKind` earns money only through `BUY` (sell, then buy) and `WORK_SHIFT`.
  There is no quest way.
- A quest system exists already: `src/quests/` (generator at guilds; HUNT/GATHER/EXPLORE templates;
  service), `src/engine/quests.py`, gold+XP rewards, and authored `QuestDefinition` kinds.
- EXCH-02 (`docs/world_rules/material-economy/economy-exchange.md`) already names "a task's reward"
  as an ordinary earning way. Its amendment (owner, 2026-10-09, memo row 38) requires a reward to
  come from a payer's purse. That is today's law: EXCH-02-B is done (#536, divergence 2.110, which
  supersedes 2.98). A quest reward is paid by its one real giver, the treasury of the faction
  holding the posting building's ground or the offering faction. It is OWED (OwedRecord) when the
  giver can't pay. A quest with no giver pays XP only.

## Scope
- A "take a quest" earning way in the earn_then_buy chain (`opening_steps.py` / `ways.py`), offered
  next to `WORK_SHIFT` and `BUY` when a quest-giving building is within reach and the subject can
  take quests. It is built on the existing quest system; no second quest model.
- Taker (designer ruling Q1): ONE predicate `can_take_quest(entity)` in one place. Today it returns
  `keeps_coin(entity)` (D43's keeps_coin_and_trades). Every caller reads only that predicate: the
  way, the generator's taker filter if any, and the tests. The quest way earns coin, and coin means
  something only to a body that keeps and trades it.
- Payer (designer ruling Q3): the quest way is an EARN way only when its giver can pay the reward
  NOW (giver treasury >= the reward's gold), the way `shift_startable` requires the employer's
  purse. A quest that would end in an OwedRecord or XP only never opens as a food or earn way; a
  broke body taking it would starve holding an IOU.
- Ranking (designer ruling Q2): the earn ways are ranked by EXPECTED TICKS UNTIL COIN IN HAND, not
  by a fixed kind order:
  - BUY (sell held goods): travel to a shop with coin;
  - WORK_SHIFT: travel plus the shift length;
  - QUEST: travel to the posting building plus the template's expected duration.
  A quest kind's expected duration, and any travel-estimate factor, is a DATA value in `data/`,
  never a code constant. Ties break SELL > WORK_SHIFT > QUEST, so the result stays deterministic.
- Danger (Q2): a kill or clear-camp quest opens only if the same power belief the HUNT step uses
  (CONFLICT-03, "believes it can overcome") says the taker can overcome the quest's target kind.
  There is no second power judgement. This way is a caller of the Step B `judge_power` seam. Collect
  and explore quests have no power gate in this ticket.
- Hunger budget (Q2): a way whose expected ticks to coin exceed the body's ticks until the
  starving line is not opened for a food project. This is said ONCE, in the shared ranker, and
  applies to all three ways alike, not as a quest special case.
- A quest's lifecycle (taken, in progress, evidence, turned in, paid) uses the existing typed quest
  state. Payment goes through the authoritative pipeline.
- Docs: the SURV-06 / EXCH-02 world rules, the Bible chapter 03 earning paragraph, a parity entry,
  and a divergence entry if the behaviour departs from the Bible.

## Out of Scope
- Society-given quests (future, per the owner).
- Quest GIVING by entities (future).
- New quest kinds beyond the existing templates. A camp-clear template, if one doesn't exist, is
  added as an extension point only.
- Any change to #995 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1). Its W run is
  live on its src, and an amendment would void that run.

## Acceptance Criteria
- AC1: a broke, hungry body with the taker capability, beside a quest-giving building and with no
  shift open, takes a quest, completes it, is paid, and then eats (an integration scenario).
- AC2: a coin-keeping body with no work and an open quest gets the quest way; a non-coin body in
  the same scene does not. The predicate is pinned by property: the test swaps the trait, never
  the kind (owner rule: no person class in checks).
- AC3: the ranking is by expected ticks to coin in hand, with the tie order SELL > WORK_SHIFT >
  QUEST, pinned by a unit test per ordering edge and one per tie. The hunger budget closes a way
  whose ticks to coin exceed the ticks to the starving line, for all three ways. If this changes
  WORK_SHIFT behaviour in an existing test, that test is a changed expectation and an owner ask,
  checked before landing.
- AC4 (payer): in the same scene, with the giver's treasury below the reward the way is closed, and
  at the reward it is open. After completion the treasury is down R and the taker up R
  (conservation). A quest that would be owed or XP-only never opens as a way.
- AC4b (danger): a kill or clear quest whose target the taker believes it cannot overcome is closed,
  through the same belief the HUNT step reads.
- AC5: the A7 invariant holds; the quest path yields to a present threat.
- AC6: a W-style measurement shows the change against the base (the kit set at dispatch).
- AC7: the TCK-20261122 three-starving-bodies scenes are re-read after this lands, to see whether
  any of them had an open quest within reach.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#995: D73 ATOMIC payment, SEEK_WORK,
  2.224 admission)
- TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM
  (human 5 died with WORK_SHIFT and BUY untried)
- TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (#536; divergence 2.110,
  which supersedes 2.98)
- TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN (Step B,
  the `judge_power` seam; this way is a consumer)
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING, TCK-20260619-E23C-QUEST-REWARDS (the existing quest
  system's history)
- TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT (Step A, A7)

## Related Docs
- docs/world_rules/material-economy/economy-exchange.md (EXCH-02 and its payer amendment)
- docs/mechanics/03_economic_laws.md
- docs/guidelines/intentional_divergences.md 2.110 (supersedes 2.98), 2.218, 2.223, 2.224

## Related Stored Artifacts
None yet.

## Related Code Areas
src/ai/goals/ways.py, src/ai/goals/opening_steps.py, src/ai/goals/scorers.py, src/quests/,
src/engine/quests.py, src/engine/service_admission.py (keeps_coin)

## Assumptions / Open Questions
Designer rulings, 2026-11-23 (rpg-designer, relayed to rpg-planner):
- Q1 taker: (a) keeps_coin behind `can_take_quest`. Not a separate intelligence property now: it
  would be a new declared trait with no other consumer, content edits on every species, and its own
  rule for what else intelligence gates.
- Q2 ranking: expected ticks to coin, with the tie order and hunger budget above; danger through the
  HUNT belief, later `judge_power`.
- Q3 payer: today's law (2.110): the giver's treasury, open only when it can pay now.
Q4/Q5, owner IDEAS (#715 7083481188) as SHAPED by rpg-designer, 2026-11-23. APPROVED by the owner
("Approve (Recommended)", ask 7083514723, answer 7083528531):
- Three judges, never merged, each its own function with a typed reason, none reading another's
  inputs:
  - CAPABILITY: can the body take quests at all. `can_take_quest(taker)` = keeps_coin (Q1).
  - PERMISSION: does THIS source allow THIS taker. `source_admits` (Q4) and `quest_rank_qualifies`
    (Q5); the source judges.
  - PRUDENCE: should the taker attempt it. The danger gate (the taker's own power belief), and the
    hunger budget.
- Q4 `source_admits(source, taker, state) -> Admission{admitted, layer GROUP|INDIVIDUAL, reason}`:
  - The source is the same giver as the 2.110 payer, the faction holding the posting building's
    ground or the offering faction. One identity for pay and permission.
  - GROUP: that faction's existing STANCE toward the taker's faction, bucketed ALLY / NEUTRAL /
    WARY / HOSTILE. A factionless body reads NEUTRAL. No per-kind regard table.
  - INDIVIDUAL: `known_standing(source, taker, state)`, one function. It reads public reputation
    (§4) KNOWLEDGE-GATED (the TCK-20261003 defect class), plus the directed trust and sentiment of
    the posting building's attendant, if any (ch07 §1-2). Nothing known gives UNKNOWN, which is
    neutral.
  - The combination is one table, with its thresholds in DATA:
    - ALLY/NEUTRAL: admitted unless the standing <= BANNED;
    - WARY: admitted only if the standing >= VOUCHED;
    - HOSTILE: refused unless the standing >= CHAMPION.
    `layer` names the deciding layer.
  - Tests:
    - hostile faction with UNKNOWN standing is refused (GROUP);
    - the same with CHAMPION standing known to the source is admitted (INDIVIDUAL);
    - the same standing unknown to the source is refused;
    - neutral with a known grudge is refused;
    - kind-swap with the same faction gives the same result; faction-swap with the same kind gives
      a different result.
- Q5 `quest_rank_qualifies(source, taker, quest, state) -> {qualifies, standing_rank, needed_rank,
  basis}`:
  - A quest carries a typed, durable int `rank` (template or quest data), with model, tests and
    inspection.
  - standing_rank = max(REPUTATION tier from known_standing and the completed-quest record,
    OBSERVED-POWER tier from level or declared power as the source can observe it). Tiers are in
    data. It qualifies iff standing_rank >= rank.
  - judge_power is NOT used for rank. It is a pairwise belief (observer entity vs another body),
    while rank is a threshold on the taker alone judged by a faction. judge_power stays the
    prudence gate (the taker vs a kill or clear quest's target). The owner packet says so plainly,
    since the leads' relay suggested power via judge_power.
- CHECK ORDER (way-finding, deterministic; the first failure gives the one typed reason; every
  gate's flag is kept for inspection):
  1. can_take_quest;
  2. the payer can pay now;
  3. source_admits;
  4. quest_rank_qualifies;
  5. danger (kill/clear only);
  6. the shared ranker (hunger budget and ticks to coin).
  Gates 1-5 open or close the way; step 6 ranks the open ways.
- REFUSAL MEMORY: none for way-finding gates (pure, recomputed each tick, like inn admission). A
  refusal AT ARRIVAL (the state changed on the way) files a give-up on that source through the
  EXISTING F2 give-up memory (anchored target, the same expiry), with the refusal's typed reason.
  No new store. Test: refused at arrival → no re-target inside the window, and a re-target after it.
- AC additions: AC8 (Q4 tests above), AC9 (Q5 rank tests: a novice fails a high rank, either tier
  qualifies), AC10 (check order and first-failure reason), AC11 (the arrival refusal uses the F2
  give-up window).

Future owner questions, not in this scope:
- whether a later intelligence property should widen or narrow takers (only the predicate changes);
- a power gate for a dangerous explore target.
- a kind-level regard layer beyond faction (Q4 uses faction stance only);
- the guild judging power pairwise against the quest's target (the Q5 seam allows a new basis);
- quest GIVERS who are entities (their own regard as the individual layer).
Assumptions:
- the existing guild generator is enough for "simpler logic" quest spawning;
- dispatched only after #995 closes, so the earn_then_buy chain is stable.

## Durable state, lifecycle and clocks
A taken quest is durable: the existing typed quest state carries taker, kind, progress, evidence
and status. Payment is a typed update through the authoritative pipeline. The quest timer, if any,
stays in data files.

## Implementation Notes
Filed by rpg-planner from the owner direction. Read-only investigation comes first at dispatch.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
