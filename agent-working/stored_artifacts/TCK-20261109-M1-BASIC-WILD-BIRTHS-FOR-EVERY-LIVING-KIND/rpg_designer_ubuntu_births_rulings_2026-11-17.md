---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-17
tags: []
---

# M1 wild births: answers to rpg-planner-ubuntu's Q1-Q10 (rpg-designer-ubuntu, 2026-11-17, v1)

- Ticket: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (decisions 67, 70; owner dispatch #715 6943793433).
- Scope of this seat: #715 6950284219 and drafts/rpg-designer-ubuntu-births-brief.md.
- Binding rulings this sits under: 67cc6f6d, 665b9718, 39dcca3d, 3045e98a (rpg-designer, kind=species). Nothing here changes them.
- Read on main 3aafdb383 by me: the ticket; memo rows 67, 70, 86; roadmap §12.3 M1 and M2; ecology-population.md (decision 70 note); survival-needs.md (decision 42); species.yaml; need_profiles.yaml; creature_territory.py; world_dynamics.py:285-291; state.py LifecycleComponent and LifeStage; reproduction_humanoid.py cooldowns.
- Part A binds now (cc to the leads). Part B needs rpg-designer's yes before it binds (sent as questions). Part C fixes the own-job bars before any data.

## Correction to the fact list
- **Creature territory is NOT ungated.** `world_dynamics.py:286-287` runs it only when `ENABLE_CREATURE_TERRITORY_LIFECYCLE` is ON, and that flag defaults OFF (`feature_flags.py:149`). Decision 70 already ruled it "stays off". This point was outside your two spot-checks. Re-check the rest of the read-only map before any of it goes into the ticket.

## Part A: rulings that bind now

### Q1 Where the rate lives: (a), as a profile
- Per species, in content, following the existing profile pattern: species.yaml gets an optional `reproduction_profile: <id>`, and a new `data/content/living/reproduction_profiles.yaml` declares the values. Same shape as `need_profile`, `body_model`.
- Fields (all required in a profile): `birth_chance_per_check` (0-1), `min_birth_interval_ticks`, `litter_size` (int ≥1, fixed in M1), `mate_radius_tiles`, `fed_line` (the mother's hunger line, in the need's own units), `birth_hunger_cost` (see Q4).
- No profile = the kind has no births. That is a content statement, not a code default.
- The content loader refuses (typed) a profile on a species whose need profile has `hunger: "none"`: "well-fed" is undefined for it. Which kinds that leaves out is a Part B question.
- Values are content. The ticket states each value's source (a common-sense band scaled to decision 33's tick-to-day time), and none is tuned against the own-job data after it is fixed.

### Q2 Well-fed: (a)
- The mother's own hunger is at or better than her profile's `fed_line` at the check. It reads her state, nothing regional, no meal window.

### Q3 A mate of its kind nearby: (a)
- Another alive ADULT with the same `species_of()`, within `mate_radius_tiles` (Chebyshev, as the rest of the world's radii), no pair bond, no sex: sex is not modelled for any kind (no field in src), so (b) is not available, and adding it is out of scope.
- One birth per pair per check. The checked entity is the mother; the mate is the lowest entity id among eligible mates (deterministic, no RNG for the choice).
- Interval: both parents become ineligible for `min_birth_interval_ticks`. Use the existing durable field `LifecycleComponent.reproduction_cooldowns` (partner id → expiry): an entity is eligible only when the max of its expiries ≤ tick. **No new durable field.** If the implementation finds this can't work, that is a new field and goes to rpg-designer first (brief, pre-bind list).

### Q4 How the young eat: (a), plus a birth cost
- Born as `LifeStage.CHILD`, on the same hunger system as every body of its kind. Its starting hunger is the kind's normal starting value (the same as a t0 body), not a fed bonus. No parent feeding, no grace period, no free meal in M1.
- **The birth is paid in food:** the mother's hunger worsens by `birth_hunger_cost` at the birth. That keeps "food and hunting set the numbers" (decision 67) true: a mother needs to eat again before she is fed enough for the next one.
- Young dying is allowed. It is judged by survival by kind group within reasonable bands across seeds, never "0 starvation" (owner, varied-but-reasonable rule). If a kind group's young all die in every seed, that is reported to me before fold, with the cause.

### Q5 The four flagged paths: (a), narrowed
- One births system under one rule. `reproduction_humanoid.py`'s pairing and the natural-creature camp path are folded into it and their old code removed. Nest spread is retired (decision 70 says so).
- Magical/demonic (calamity.py) and the boss, lair and territory spawns are **not births**. They are declared-arrival or flagged-off spawns that decision 70 keeps off. They are left unchanged in this item; no code there moves.
- Newborn identity: faction = the mother's faction; `identity.role` = the mother's role, except HERO, which gives CITIZEN (a child does no hero work, decision 63). This is interim and is named in the ticket as a row for the name-branch retirement item. It replaces "always CITIZEN/TOWN_COUNCIL".
- Removing flagged-off code moves no default-flag run. The flag entries leave `feature_flags.py` and `docs/guides/feature_flags.md` in the same change.

### Q6 Creature territory: no change
- It is gated OFF (see the correction), and decision 70 keeps it off. Leave it. Add a line to the name-branch / retirement backlog that its spawn branch is parentless and must be rebuilt as births or removed before anyone turns it on.

### Q8 Newborn fields: yes, as already ruled
- This restates 3045e98a and the brief; it adds nothing. kind = the parents' `species_of()`; occupation = None; `parent_a_entity_id`/`parent_b_entity_id`, `birth_tick` set through the birth record. Parents of different species never pair (Q3 requires the same species), so cross-species births are impossible in M1 by construction. K8 measures it.

### Q9 Cadence and determinism: yes
- Checked on the existing 30-tick system cadence.
- The draw for `birth_chance_per_check` comes from the run's seeded RNG, keyed by (world seed, tick, mother id). No region in the key (a mother moves), no wall clock, no iteration-order dependence: mothers are visited in id order.
- A chance per check, not a fixed interval alone, so births do not fire in lockstep and seeds vary.

### Q10 Unflagged, and the own-job world
- Births ship unflagged: a core mechanism (feature-flag rule).
- The own-job runs on the decision-76 tier (3 gate worlds × 5 seeds × 5000 ticks per arm), which is the floor anyway. A separate scan to find a world/seed is not needed first: with births on, the gate worlds hold wolves, plant-eaters and people at t0.
- If the tier shows 0 births in total, that is a STOP to me, not a pass (K8 would be vacuous). Only then is a focused scan allowed, and its runner is approved by sha like the rest.
- I approve spies and runners by sha under the standing rules in the brief. Send each sha after its pin commit.

## Part B: needs rpg-designer's yes before it binds (sent to lead-planner as QUESTIONs)
1. **The births catalog rule** (rule work before code, §12.3): a Rule ID and its text for Q1-Q5 and Q9. Rule IDs and catalog text are rpg-designer's.
2. **Which kinds "every living kind" covers** (decisions 42, 70). My recommendation: (a) only kinds whose need profile has hunger, since decision 67 conditions births on being well-fed. Today that leaves out undead, spirit, slime and dragonkin; their camps keep shrinking, and they come only from declared world creation. (b) Give the non-eating kinds a different birth condition now (e.g. their own need line). (c) Ask the owner. I recommend (a), with the exclusion named in the catalog text and the v-disclosure.
3. **The extinction line for this step**: under (a), undead camp members can only fall. A per-seed undead extinction is then intended, not a regression. Does the §12.5 single-step per-seed STOP exempt kinds that declare no births, or do they stay in it and get disclosed?
4. **ECOL-03 (Q7)**: keep cohort counts statistical in M1 (individual births/deaths driving figures is roadmap M2, "Nothing from nothing"), and generalise the existing real-birth +1 nudge (`test_population_pressure_region_responds_to_real_births`) to every birth from the one system. This changes ECOL-03's evidence text.
5. **Mechanics Bible and parity**: Bible 05 (ecology) gets the births law, the parity rows for reproduction (world_dynamics.yaml / social_narrative.yaml) move, and a divergence entry is needed (class Unified: one births system; it names the humanoid child's faction/role change and the nest-spread retirement). The texts come to rpg-designer before the implementation PR.

## Part C: own-job bars (HARD; fixed here, before any data, never rewritten)
Every arm on the decision-76 tier. Fix arm spied, plus a plain twin.

- **K6, K6b, K8: carried unchanged** from 67cc6f6d / 665b9718 / 3045e98a. I can't redefine them.
- **W1, births are legal:** births where, at that check, any of these is false: mother alive and ADULT; mother at or better than `fed_line`; a same-species alive ADULT mate within `mate_radius_tiles`; both parents past their interval; the mother's species declares a profile: **0**.
- **W2, newborn shape:** newborns with occupation ≠ None, life stage ≠ CHILD, a parent id unset, or `birth_tick` ≠ the birth tick: **0**.
- **W3, nothing from nothing (V8):** bodies added mid-run that are neither a birth with two parents nor a declared arrival: **0**.
- **W4, the mother pays:** births where the mother's hunger did not worsen by exactly `birth_hunger_cost` at that tick: **0**.
- **W5, no free meal:** ticks on which a newborn's hunger improves with no eat action by that newborn on that tick: **0**.
- **Not vacuous:** total births over the tier = 0 is a STOP to me. Per kind with a profile and ≥2 adults at t0, births = 0 in every seed is reported with the spy's failing condition named.
- **Reported (BALANCE):** births per world × kind × seed; survival by kind group (born, alive at end, starved, killed); deaths by world × cause; population per kind over time; per-seed extinction per §12.5 (and Part B 3); SimQ; D76.
- **HARD evidence, every run:** spied == plain hash; PINNED; logging_errors = ERROR count = 0; exceptions {} with rows; no deletes; child logs kept; no crash or ENOMEM.
