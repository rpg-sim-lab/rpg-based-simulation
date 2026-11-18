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

# M1 reproduction: gestation, litter size and the mate gate (rpg-designer-ubuntu, 2026-11-18, DRAFT)
- **Basis:**
  - owner direction (#715 6966994323): all three join the M1 births PR, now called "reproduction";
  - rpg-designer's non-binding guardrails (relayed by lead-planner);
  - the OWNER's answers in this session (AskUserQuestion, 2026-11-18): gestation is "Compressed, order kept", and the mate gate is "Marriage OR mutual affection".
- **Status:** a design position for rpg-planner-ubuntu's one plan-first brief. Pre-bind items are in §7. Simple foundation: every rate is content, report-only, and deferred to TCK-20261118-BIRTHS-BALANCING-PASS.
- **Code facts at 02d327ba6:**
  - `ReproductionProfileDefinition` (schema.py:81) already has `litter_size: int`, and every profile is 1.
  - The check runs every 30 ticks on the absolute tick. A day is 2400 ticks.
  - `MarriageState` lives in `strategic.marriages`.
  - **Nothing in decision code ever emits PROPOSE_MARRIAGE.** Only the router branch exists (action_router.py:78). So marriages are 0 in every run.
  - `SocialBond.sentiment` (-1..1) is directed, written by relationships.py:62-89, and has a FRIEND threshold (`RelationshipService.FRIEND_SENTIMENT_THRESHOLD`).

## 1. Gestation: one typed durable record on the mother
- **`PregnancyState`** (frozen) on the mother's lifecycle, None when not pregnant. Fields:
  - `father_entity_id`;
  - `conceived_tick`;
  - `due_tick`;
  - `litter_size` (drawn at conception);
  - `father_genetic_profile`, a snapshot taken at conception, so a father who dies before the birth still gives his genes. It uses the same fallback as births today.
- It needs FIELD_RULES rows, a checkpoint and canonical-hash round trip, and inspection visibility (the durable-state rule).
- **Lifecycle:**
  - set at conception through a typed update;
  - cleared at the birth in the same typed update that adds the newborns;
  - **if the mother dies or despawns first, there is no newborn.** The record stays on the dead body as history. Births reads only alive, active mothers, so it can never fire. The spy reports it as "pregnancy ended by the mother's death". No new state branch.
- **Content:** a new `gestation_ticks` field on the profile, a multiple of 30 (typed refusal otherwise). So `due_tick = conceived_tick + gestation_ticks` always lands on a check tick, and the birth fires inside the placed births step, on the absolute tick.
- **Owner: compressed, with the order kept.** Proposed values, fixed before data, each with its stated source line in content:
  - humanoid 2400 (1 day);
  - carnivore 1200;
  - goblin 900;
  - plant eater 600.
  - People stay the slowest.
  - **This is shorter than the "people about 2 days" example I gave the owner.** A 4800-tick human gestation would let only conceptions in the first 200 ticks of a 5000-tick run finish. I disclose that to the owner.
  - The real lengths (about 672,000 ticks for a person) wait for TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY. The compression is a disclosure line.
- **Intervals:**
  - the mother's `min_birth_interval_ticks` runs from the birth;
  - the father's runs from the conception;
  - the values are unchanged and BALANCE.

## 2. Litter size: a declared table, never a kind name
- `litter_size: int` is replaced by `litter_weights: {size: weight}`. Each size is at least 1, and the weights are positive. Typed refusal if the table is empty or a weight is not positive.
- **The draw:** at conception, a keyed stateless draw `get_float(Domain.SPAWN, tick, mother.id, sub_id=LITTER_DRAW_SUB_ID)` over the table in ascending size order.
- **Proposed values (content, sourced, BALANCE):**
  - humanoid {1: 0.97, 2: 0.03} (people: 1, sometimes 2);
  - carnivore {4: 0.25, 5: 0.25, 6: 0.25, 7: 0.25} ("a wolf more than 5");
  - goblin {1: 0.5, 2: 0.35, 3: 0.15};
  - plant eater {2: 0.4, 3: 0.4, 4: 0.2}.
- 6a's `+len(newborns)` already covers a litter.

## 3. Mate gate: a declared profile field
- **Field:** `mate_gate: "none" | "bond"`, plus `min_mutual_sentiment` (required when `bond`).
- **`bond` passes if either holds at the conception tick:**
  - an ACCEPTED `MarriageState` between the two, held by either party;
  - or BOTH directed bonds (mother→mate and mate→mother) have `sentiment >= min_mutual_sentiment`.
- The gate reads only that typed marriage and bond state, never role, kind or occupation. Q18's "never an eligibility read" is lifted ONLY for these two reads (pre-bind).
- **Proposed values:**
  - humanoid: `bond`, with `min_mutual_sentiment` = the FRIEND threshold's value, citing that constant as its source;
  - carnivore, goblin, plant eater: `none`.
- **Owner: "marriage OR mutual affection".** Marriage contributes 0 today, because nothing proposes it. That is disclosed: "the marriage arm is live but unreached until marriage proposals exist". A backlog row for a decision that proposes marriage goes on the balancing-pass ticket.

## 4. The open points rpg-designer asked me to settle
- **Can a pregnant mother mate again? NO.** A mother with a PregnancyState is ineligible to conceive. A father may sire again once his interval from the conception has passed.
- **W4, the food cost: per birth event, charged at the birth,** with today's formula `min(birth_hunger_cost, 100 - hunger)`. It is not per newborn. A per-newborn cost is a balance question for the pass ticket.
- **W1 re-stated for litters and gestation:**
  - **at conception**, the existing W1 eligibility applies (both alive, active and ADULT; both past their intervals; the mother at or below fed_line; same species; in radius), plus the mother not pregnant and the mate gate passing;
  - **at birth**, only the mother alive and active. Fed, mate and range are not re-checked; the father may be dead.
  - "One parent in more than one birth per check" stays.
- **Prediction before data, for people under the gate:**
  - **1000-tick runs: 0 human births by construction** (gestation 2400 > 1000). The same holds for every species with gestation above the run length.
  - **5000-tick runs:** a conception must happen by tick 2600, and needs a mutual sentiment at or above the FRIEND threshold. My prediction is 0-3 human births per world × seed, and 0 is plausible.
  - The tier STOP rule counts all kinds, so it isn't affected. Human births = 0 is reported, not a STOP.

## 5. HARD rows, before data (each counts to 0)
- **G1, the birth is at term:** newborns whose mother's PregnancyState had `due_tick` != the birth tick, or `father_entity_id` != the newborn's parent_b.
- **G2, the litter as drawn:** birth events whose newborn count != `pregnancy.litter_size`.
- **G3, one pregnancy at a time:** conceptions by a mother already pregnant; pregnancies with `due_tick` != conceived + the species' `gestation_ticks`.
- **G4, once:** a pregnancy giving more than one birth, or still set after its birth.
- **G5, the gate:** conceptions on a `bond` species with neither an accepted marriage nor both sentiments at or above the threshold at that tick. Also, gate reads on a `none` species, which must be 0.
- **Carried rows:**
  - W1 as re-stated in §4;
  - W4 per birth event;
  - K8 at conception (same species) and at birth (child kind = mother's species);
  - 6a at the birth tick, by the mother's region at that tick;
  - K6/K6b;
  - determinism (twin hash plus the second-hash-seed test).
- **Tests:**
  - a PregnancyState checkpoint round trip;
  - a mother who dies while pregnant gives no newborn, and the spy reports it.
- **Not vacuous:**
  - 0 births in the tier is a STOP to me, as now;
  - 0 conceptions on a `bond` species makes G5 vacuous. That is reported, and a unit test carries G5.

## 6. BALANCE (report only)
- Conceptions and births per world × seed × species.
- The litter distribution.
- Pregnancies ended by the mother's death.
- Pairs blocked only by the gate.
- Human births (against the §4 prediction).
- The gestation compression note.

## 7. Pre-bind with rpg-designer (QUESTIONS)
- **Q-G1:** the new durable field `PregnancyState` (fields as §1), and the lifecycle choice that it stays on a dead mother as history, with no clear.
- **Q-G2:** the reworded Births Law bullet: conception at the check, birth at term, litter from a declared table, gate by a declared field. The text is rpg-designer's.
- **Q-G3:** ch07, its parity entries and an intentional_divergences row (Intentional Gameplay Change) reversing the 2026-08-29 "Marriage does not gate Reproduction" decision (TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT). The pre-implementation texts are rpg-designer's.
- **Q-G4:** lift Q18 only for the marriage and bond reads of §3.
- **Q-G5:** my §4 answers (no remating while pregnant; W4 per birth event; W1 split between conception and birth). Do they stand?

## 8. Knock-on effects to re-rule after implementation
- The bucket-2 A fixture condition (213 rows at ticks 120-199, newborns from tick 120) is VOID. Births now arrive at the conception tick plus gestation, so the fixture regeneration gets a fresh attribution and a fresh ruling.
- test_world_dynamics' delta tests and the co-fire order test are re-checked against birth-at-term.
- The own-job instrument (02d327ba6) needs G1-G5, the PregnancyState rows and the risen rows, then new shas and my re-approval.

## 9. Revision 2 (2026-11-18): rpg-designer's rulings on Q-G1 to Q-G5. Where this section differs from §1-§8, it wins.
- **Q-G1: APPROVED, with one change. This supersedes §1's "stays on the dead body".**
  - If the mother dies first, the PregnancyState is CLEARED in the death's typed update, and a typed event is emitted: `PREGNANCY_ENDED`, reason `MOTHER_DIED`, with the litter size.
  - **New HARD row G6:** no PregnancyState on a dead body (count = 0).
  - Implementation note: the clear belongs to every path that sets a death or despawn, not to births. The plan names each of those paths.
- **Q-G2, the Births Law bullet RE-RULED.** It replaces the placed bullet verbatim:
  > - **Births Law**: Every 30 ticks (absolute kernel tick), a mother eligible under her species' reproduction profile and not already pregnant, with an eligible same-species mate in range who passes the species' declared mate gate, may conceive, by the profile's chance per check, drawn from the run's seeded RNG. The pregnancy is recorded on her, and at its due tick she bears its litter, drawn at conception from the profile's declared litter weights, at life stage CHILD. The step runs inside this phase, outside its 50-tick gate, and commits only typed updates (the pregnancy and its end, the newborns, their birth sources, the parents' cooldowns and the mother's hunger cost, the region's birth count).
  - **Condition:** content validation refuses a `gestation_ticks` that isn't a positive multiple of 30, as a typed content error.
- **Q-G3: APPROVED.**
  - Humanoid `min_mutual_sentiment` REFERENCES the FRIEND threshold constant. It is not a copied number.
  - The ch07, parity and intentional_divergences texts (Intentional Gameplay Change, reversing 2026-08-29) go to rpg-designer BEFORE code.
  - The marriage arm being 0 today is disclosed.
- **Q-G4: YES.** Q18 is lifted only for the marriage and bond reads.
- **Q-G5: CONFIRMED.** The HARD set is G1-G6, K8 at conception and at birth, and 6a at the birth.
- **Maturity:** not M1 scope (TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK). The step report carries the line: "gestation is compressed; maturity is not, so no newborn breeds in any run."
- **Placement:** each newborn goes through free_spawn_position's existing search. A newborn with no free tile is NOT born, and is reported as unplaced.
  - **G2 becomes: born + unplaced = the litter drawn, exactly.**
  - Unplaced counts are BALANCE. It is a STOP only if every birth in a cell is unplaced.
- **Region:** 6a credits the mother's region at the BIRTH tick, using her position at term, captured by the spy itself.
- **Father dead before term:**
  - the birth proceeds, using the genetics snapshot and the recorded father id;
  - the newborn's parent bond is seeded only toward LIVING parents;
  - its parentage fields record both parents.
