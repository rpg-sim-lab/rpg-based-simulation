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
OPEN (blocked on the designer's taker-property ruling, see Open Questions)

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
  come from a payer's purse. Divergence 2.98 records quest reward coin as minted today, a bounded
  known exception.

## Scope
- A "take a quest" earning way in the earn_then_buy chain (`opening_steps.py` / `ways.py`), offered
  next to `WORK_SHIFT` and `BUY` when a quest-giving building is within reach and the subject has
  the taker capability. It is built on the existing quest system; no second quest model.
- One kind-neutral taker gate, declared as data, read through one rule (as admission reads
  `keeps_coin`, D43).
- The precedence between `WORK_SHIFT`, `BUY` and the quest way is set by the designer.
- A quest's lifecycle (taken, in progress, evidence, turned in, paid) uses the existing typed quest
  state. Payment goes through the authoritative pipeline. The payer question is in Open Questions.
- Docs: the SURV-06 / EXCH-02 world rules, the Bible chapter 03 earning paragraph, a parity entry,
  and a divergence entry if the behaviour departs from the Bible.

## Out of Scope
- Society-given quests (future, per the owner).
- New quest kinds beyond what the existing templates hold. Extensibility is a design property
  here, not new content.
- Any change to #995 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1). Its W run is
  live on its src, and an amendment would void that run.
- Retiring divergence 2.98 (the minted-coin exception), unless the designer rules it in.

## Acceptance Criteria
- AC1: a broke, hungry body with the taker capability, beside a quest-giving building and with no
  shift open, takes a quest, completes it, is paid, and then eats (an integration scenario).
- AC2: a body without the capability is never offered the quest way. The gate is the one declared
  property, never a kind or class name (owner rule: no person class in checks).
- AC3: the precedence among `WORK_SHIFT`, `BUY` and the quest way matches the designer's ruling,
  and is pinned by a unit test per ordering edge.
- AC4: quest reward coin follows the designer's payer ruling: a payer's purse, or the 2.98
  exception kept and cited.
- AC5: the A7 invariant holds; the quest path yields to a present threat.
- AC6: a W-style measurement shows the change against the base (the kit set at dispatch).

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#995: D73 ATOMIC payment, SEEK_WORK,
  2.224 admission)
- TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM
  (human 5 died with WORK_SHIFT and BUY untried)
- TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (divergence 2.98)
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING, TCK-20260619-E23C-QUEST-REWARDS (the existing quest
  system's history)
- TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT (Step A, A7)

## Related Docs
- docs/world_rules/material-economy/economy-exchange.md (EXCH-02 and its payer amendment)
- docs/mechanics/03_economic_laws.md
- docs/guidelines/intentional_divergences.md 2.98, 2.218, 2.223, 2.224

## Related Stored Artifacts
None yet.

## Related Code Areas
src/ai/goals/ways.py, src/ai/goals/opening_steps.py, src/ai/goals/scorers.py, src/quests/,
src/engine/quests.py, src/engine/service_admission.py (keeps_coin)

## Assumptions / Open Questions
- Q1 (designer): the taker property. Options: the D43 coin-and-trade trait (`keeps_coin`), a
  separate declared intelligence property, or both.
- Q2 (designer): the precedence of the quest way against `WORK_SHIFT` and `BUY`, and whether
  a quest's expected duration and danger enter the choice (judge_power seam for kill and clear
  quests).
- Q3 (designer / owner): the payer of quest reward coin: the guild treasury, the giver's purse, or
  2.98 minting kept for now.
- Q4: where "simpler logic" quest spawning lives. The existing guild generator is assumed
  enough for this ticket.
- Assumption: dispatched only after #995 closes, so the earn_then_buy chain is stable.

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
