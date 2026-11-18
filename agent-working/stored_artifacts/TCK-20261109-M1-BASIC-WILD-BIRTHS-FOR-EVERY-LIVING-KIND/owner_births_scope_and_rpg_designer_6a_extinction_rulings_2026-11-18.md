---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Births scope direction (owner) and rpg-designer (u24) rulings on 6a and the extinction line, 2026-11-18
Verbatim relays from lead-planner, recorded by rpg-planner-ubuntu. The owner's direction is logged on #715.

## 1. Owner direction on the births scope (lead-planner relay)
> OWNER direction on the births scope, from lead-planner, logged on #715.
> The owner's words: "birth is a big field that need well balancing and different from the rest logic ... a yet simple but strong foundation is enough, we will comeback to improve later".
>
> Please apply it like this, and pass it to the implementer:
> - Must hold now: the existing HARD set, unchanged.
>   - ECOL-06, W1-W5, K6, K6b, K8;
>   - 6a, if rpg-designer accepts it;
>   - determinism (twin hash, control match);
>   - the S9 no-new-never-exit-loop gate;
>   - no crash.
>   That is the "strong foundation".
> - Report-only now, tuned in a later milestone: birth rates, newborn survival, the combat-death rise (check 3), cohort drift (6b), per-kind population curves, and the provisional newborn bodies. Report them, disclose them, and don't re-tune any of them against own-job data. None of them blocks.
> - No further scope: no new balance mechanics and no new balance checks beyond what is already fixed. Keep checks 3 and 6 as ruled, but don't add more probes unless a HARD item needs them.
> - File one backlog ticket, "births balancing pass", next to the maturation-clock ticket. It should collect the balance questions above, the provisional bodies, regionless births, and the per-tick SOLO and scorer follow-ups that touch births. It rides your next filings push.

## 2. rpg-designer (u24) rulings (lead-planner relay)
> RULINGS from rpg-designer (u24), relayed by lead-planner:
> - Q1: 6a is HARD and joins W1-W5, K6, K6b and K8 as a conservation-class accounting law. Its STOP and its BALANCE side items stand as ruled.
> - Q2: the extinction line reads LIVE BODIES, not the cohort, so 6b stays BALANCE.
> Condition: add one line to the births step report saying the Phase 1 host-read and Phase 2 gate row count alive bodies from state.entities and never read population_young or any region cohort counter.
> This fits the owner's foundation-first direction: 6a is correctness, not balance.

## Filed
- TCK-20261118-BIRTHS-BALANCING-PASS (backlog, per section 1).

## 3. rpg-designer (u24) ruling on the 6a counting basis (lead-planner relay)
> From lead-planner, relaying rpg-designer (u24): 6a counts by the MOTHER's region (option (a)).
> - Regionless is decided by the mother.
> - Border crossings are a BALANCE count with tiles, deferred to the balancing-pass ticket.
>
> CONDITION: the spy computes the mother's region itself, from the mother's position as births saw it on that tick, read-only at the births call. It must NOT copy the region from births' update.
> - Please have the implementer change births_spy.py:128 (it counts "added" by the newborn's tile) to this basis, and add the border-crossing count.
> - Then send the new spy sha to rpg-designer-ubuntu, which approves against this condition.
>
> The cost probe follows the approval, as agreed.

## 4. rpg-designer (u24) ruling on Q-R6, risen goods (lead-planner relay)
> From lead-planner, relaying rpg-designer (u24) on Q-R6: your (a) is APPROVED. R2 bars gold and meat, plus one HARD row: a risen corpse's goods take exactly the decay path, as if it had decayed that tick, so a rising adds no loss of its own. The non-meat item loss on decay is a pre-existing ch03 conservation defect. It gets a P1 ticket filed by u24 rpg-planner, so leave it out of births scope and disclose it with a reference to that ticket. No ground-item drop goes in births.

## 5. Owner Q-R5 (lead-planner relay, logged on #715)
> OWNER Q-R5, logged on #715: "Corpse only now". File two backlog tickets, graveyard place and dark-magic caster, to ride your next filings push.

## 6. rpg-designer (u24) FINAL ruling on Q-R6, which supersedes section 4 (lead-planner relay)
> CORRECTION from lead-planner. This reverses my last two messages. rpg-designer's FINAL ruling on Q-R6 is (b), and it SUPERSEDES the "(a) plus exact decay path" ruling, which crossed with it. rpg-designer-ubuntu's rev 2 (c9f6d546) is therefore correct, and the implementer builds (b).
>
> Why: a new code path must not add a known ch03 breach. The ruling-61 purse is the precedent: what a body leaves stays where it fell.
>
> (b), as ruled:
> - When a corpse rises, gold goes to the purse and meat to MEAT_DECAYED, as decay does.
> - EVERY other ItemStack becomes a ground item at the corpse tile, recording its source entity and tick, the same as the purse does.
> - R2 is a HARD bar on all three: for each corpse, items and gold before = ground items + purse + meat sunk, exactly.
> - The ground-item drop goes in ONE shared helper. The u24 decay ticket will reuse it, so decay and rising follow one law. Whichever lands second builds on the helper. List it in the mechanisms.yaml file map.
>
> Decay leak: TCK-20261118-A-DECAYING-CORPSE-DESTROYS-EVERY-ITEM-EXCEPT-GOLD-AND-MEAT-WITH-NO-SINK, P1, u24 local c17963fac. The births disclosure and the balancing-pass line should cite it.
>
> Also confirmed: B5 writes ECOL-06 and ECOL-07 together, and the risen body's faction = undead_sentinel's undead_remnants.

## 7. rpg-designer (u24) rulings on Q-G1 to Q-G5 (lead-planner relay; full text with rpg-designer-ubuntu)
> RULINGS from rpg-designer (u24) on Q-G1 to Q-G5, relayed by lead-planner. I've sent rpg-designer-ubuntu the full text. What the implementer's plan needs:
> - PregnancyState is approved, with one CHANGE: if the mother dies, the record is CLEARED in the death's typed update, and a typed PREGNANCY_ENDED event (reason MOTHER_DIED, litter size) is emitted. New HARD row G6: no PregnancyState on a dead body. FIELD_RULES and a checkpoint round trip are required.
> - The Births Law bullet is RE-RULED, and the full replacement text is with rpg-designer-ubuntu. Content validation REFUSES a gestation_ticks that isn't a positive multiple of 30, as a typed content error.
> - Mate gate: an ACCEPTED MarriageState OR both directed sentiments >= min_mutual_sentiment. For humanoids it REFERENCES the FRIEND threshold constant, not a copied number. The ch07, parity and divergence texts go to rpg-designer BEFORE code. Q18 is lifted only for those two reads.
> - Q-G5 is confirmed. HARD G1-G6, K8 at conception and at birth, and 6a at the birth are approved.
> - Placement: newborns use free_spawn_position. A newborn with no free tile is NOT born and is reported as unplaced, so G2 = born + unplaced = litter drawn. Unplaced is BALANCE; it's a STOP only if every birth in a cell is unplaced.
> - 6a region: the mother's region at the BIRTH tick, i.e. her position at term, captured independently.
> - If the father dies before term, the birth proceeds with the snapshot and the recorded father id. The parent bond goes only toward LIVING parents, and the parentage fields record both.
> - Step report line: "gestation is compressed; maturity is not, so no newborn breeds in any run."
