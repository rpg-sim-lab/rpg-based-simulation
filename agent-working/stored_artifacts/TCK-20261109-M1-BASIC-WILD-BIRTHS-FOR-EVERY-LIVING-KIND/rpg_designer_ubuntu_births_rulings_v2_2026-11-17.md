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

# M1 wild births: answers to rpg-planner-ubuntu's Q1-Q10 (rpg-designer-ubuntu, 2026-11-17, v2 BINDING)

- **v2 supersedes v1 (52ad1ea5).** It folds in rpg-designer's answers (drafts/rpg-designer-births-answers.md, sha256 8c2c9fab) and the owner's B2 ruling (#715 6950737100). Every change from v1 is marked **[v2]**. Where v2 and v1 differ, v2 wins.

- Ticket: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (decisions 67, 70; owner dispatch #715 6943793433).
- Scope of this seat: #715 6950284219 and drafts/rpg-designer-ubuntu-births-brief.md.
- Binding rulings this sits under: 67cc6f6d, 665b9718, 39dcca3d, 3045e98a (rpg-designer, kind=species). Nothing here changes them.
- Read on main 3aafdb383 by me: the ticket; memo rows 67, 70, 86; roadmap §12.3 M1 and M2; ecology-population.md (decision 70 note); survival-needs.md (decision 42); species.yaml; need_profiles.yaml; creature_territory.py; world_dynamics.py:285-291; state.py LifecycleComponent and LifeStage; reproduction_humanoid.py cooldowns.
- Part A binds, as amended by rpg-designer. Part B is now answered and binds. Part C's bars are approved, with rpg-designer's four sharpenings, all fixed before any data.

## Correction to the fact list
- **Creature territory is NOT ungated.** `world_dynamics.py:286-287` runs it only when `ENABLE_CREATURE_TERRITORY_LIFECYCLE` is ON, and that flag defaults OFF (`feature_flags.py:149`). Decision 70 already ruled it "stays off". This point was outside your two spot-checks. Re-check the rest of the read-only map before any of it goes into the ticket.

## Part A: rulings that bind now

### Q1 Where the rate lives: (a), as a profile
- Per species, in content, following the existing profile pattern: species.yaml gets an optional `reproduction_profile: <id>`, and a new `data/content/living/reproduction_profiles.yaml` declares the values. Same shape as `need_profile`, `body_model`.
- Fields (all required in a profile): `birth_chance_per_check` (0-1), `min_birth_interval_ticks`, `litter_size` (int ≥1, fixed in M1), `mate_radius_tiles`, `fed_line` (the mother's hunger line, in the need's own units), `birth_hunger_cost` (see Q4).
- No profile = the kind has no births. That is a content statement, not a code default.
- The content loader refuses (typed) a profile on a species whose need profile has `hunger: "none"`: "well-fed" is undefined for it. **[v2]** Owner B2 (#715 6950737100): M1 births are only for kinds that eat. Undead, spirit, slime and dragonkin get no profile.
- Values are content. The ticket states each value's source (a common-sense band scaled to decision 33's tick-to-day time), and none is tuned against the own-job data after it is fixed.

### Q2 Well-fed: (a)
- The mother's own hunger is at or better than her profile's `fed_line` at the check. It reads her state, nothing regional, no meal window.

### Q3 A mate of its kind nearby: (a)
- Another alive ADULT with the same `species_of()`, within `mate_radius_tiles` (Chebyshev, as the rest of the world's radii), no pair bond, no sex: sex is not modelled for any kind (no field in src), so (b) is not available, and adding it is out of scope.
- One birth per pair per check. The checked entity is the mother; the mate is the lowest entity id among eligible mates (deterministic, no RNG for the choice).
- Interval: both parents become ineligible for `min_birth_interval_ticks`. Use the existing durable field `LifecycleComponent.reproduction_cooldowns` (partner id → expiry): an entity is eligible only when the max of its expiries ≤ tick. **No new durable field.** If the implementation finds this can't work, that is a new field and goes to rpg-designer first (brief, pre-bind list).
- **[v2] rpg-designer's conditions for the field:**
  - expired entries are pruned at the check, so the map stays bounded;
  - the field's doc and its comment in state.py state the new meaning (the birth interval);
  - a FIELD_RULES row is needed only if the field's shape changes, and it doesn't.

### Q4 How the young eat: (a), plus a birth cost
- Born as `LifeStage.CHILD`, on the same hunger system as every body of its kind. Its starting hunger is the kind's normal starting value (the same as a t0 body), not a fed bonus. No parent feeding, no grace period, no free meal in M1.
- **The birth is paid in food:** the mother's hunger worsens by `birth_hunger_cost` at the birth. That keeps "food and hunting set the numbers" (decision 67) true: a mother needs to eat again before she is fed enough for the next one.
- Young dying is allowed. It is judged by survival by kind group within reasonable bands across seeds, never "0 starvation" (owner, varied-but-reasonable rule). If a kind group's young all die in every seed, that is reported to me before fold, with the cause.

### Q5 The four flagged paths: (a), narrowed
- One births system under one rule. `reproduction_humanoid.py`'s pairing and the natural-creature camp path are folded into it and their old code removed. Nest spread is retired (decision 70 says so).
- Magical/demonic (calamity.py) and the boss, lair and territory spawns are **not births**. They are declared-arrival or flagged-off spawns that decision 70 keeps off. They are left unchanged in this item; no code there moves.
- **[v2] Newborn identity (AMENDED by rpg-designer, a shared identity contract):**
  - faction = the mother's faction;
  - `identity.role` = MONSTER if the mother's role is MONSTER, else CITIZEN. Inheriting SHOPKEEPER, GUARD or WORKER would give a child a job role, and role still drives behaviour branches;
  - occupation stays None (3045e98a).
  - This is interim, and is listed as a row of the name-branch / hero-role retirement item. It replaces both "always CITIZEN/TOWN_COUNCIL" and v1's "the mother's role, HERO→CITIZEN".
  - **The ticket on origin at 1140fcfb1 carries v1's role rule. It must be corrected.**
- Removing flagged-off code moves no default-flag run: all three reproduction paths and territory are default OFF. The flag entries leave `feature_flags.py` and `docs/guides/feature_flags.md` in the same PR. **[v2]** rpg-designer reviews the feature_flags.md change.

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
- The own-job runs on the decision-76 tier (3 gate worlds × 5 seeds × 5000 ticks per arm), which is the floor anyway. **[v2]** The arms are the FIX arm (spied) plus its plain twin only. There's no base arm in Phase 1 (owner 6936893143); the base comparison comes at Phase 3. Before launching, send lead-planner an estimated wall time and per-process memory; each run needs its go (the ubuntu slot). A separate scan to find a world/seed is not needed first: with births on, the gate worlds hold wolves, plant-eaters and people at t0.
- If the tier shows 0 births in total, that is a STOP to me, not a pass (K8 would be vacuous). Only then is a focused scan allowed, and its runner is approved by sha like the rest.
- I approve spies and runners by sha under the standing rules in the brief. Send each sha after its pin commit.

## Part B: answered [v2] (rpg-designer 8c2c9fab; the owner on B2)
1. **Catalog rule: ECOL-06, "A new body is born, not made"** (Domain Rule, docs/world_rules/life-body/ecology-population.md). The text is rpg-designer's, in 8c2c9fab, B1. It goes into the catalog only through rpg-designer, never from this lane. Its evidence: W1-W5, K6, K6b, K8.
2. **Owner ruling (#715 6950737100):** M1 births only for kinds that eat. Undead, spirit, slime and dragonkin are excluded. **The ubuntu RPG lane files a backlog ticket with the births batch: "slime and dragonkin get a non-food birth condition". It is not an M1 item.**
3. **There is NO exemption from the extinction line.** Every kind stays in it, as recorded (owner 6919222181). The undead decline is disclosed as BALANCE text. In Phase 1 the extinction line is the host read at the domain boundary (fallback a, 6937306315), and births is run 5.
4. **ECOL-03: agreed.** Cohorts stay statistical in M1, and the real-birth +1 nudge generalises to every birth from the one system. ECOL-03's status line becomes "partly met: births feed the aggregate; deaths and cohorts stay statistical until M2". rpg-designer reviews that evidence text in the PR.
5. **Agreed.** Each of these comes to rpg-designer as text before the implementation PR:
   - the births law in Bible ch05;
   - the reproduction parity rows;
   - one divergence entry, class Unified, naming four things: the one births system, the amended child faction/role rule, the nest-spread retirement, and the removal of the three OFF paths.

## Part C: own-job bars (HARD; fixed here, before any data, never rewritten)
Every arm on the decision-76 tier. Fix arm spied, plus a plain twin.

- **K6, K6b, K8: carried unchanged** from 67cc6f6d / 665b9718 / 3045e98a. I can't redefine them.
- **W1, births are legal:** births where, at that check, any of these is false: mother alive and ADULT; mother at or better than `fed_line`; a same-species alive ADULT mate within `mate_radius_tiles`; both parents past their interval; the mother's species declares a profile; **[v2]** each entity is a parent in at most one birth per check: **0**.
- **W2, newborn shape:** newborns with occupation ≠ None, life stage ≠ CHILD, a parent id unset, or `birth_tick` ≠ the birth tick: **0**.
- **W3, nothing from nothing (V8):** bodies added mid-run that are neither a birth with two parents nor a declared arrival: **0**. **[v2]** The declared-arrival list is a typed set of spawn sources, written into the spy before the run and never judged after.
- **W4, the mother pays:** births where the mother's hunger did not worsen by exactly **[v2]** min(`birth_hunger_cost`, the room left to the hunger bound) at that tick: **0**.
- **W5, no free meal:** ticks on which a newborn's hunger improves with no **[v2]** typed eat/consume event by that newborn on that tick: **0**. Any other path that improves a newborn's hunger counts as a W5 fail, and is named in the row.
- **Not vacuous:** total births over the tier = 0 is a STOP to me. Per kind with a profile and ≥2 adults at t0, births = 0 in every seed is reported with the spy's failing condition named.
- **Reported (BALANCE):** births per world × kind × seed; survival by kind group (born, alive at end, starved, killed); deaths by world × cause; population per kind over time; per-seed extinction per §12.5, with no exemption (Part B 3), and the undead decline disclosed as BALANCE; SimQ; D76.
- **HARD evidence, every run:** spied == plain hash; PINNED; logging_errors = ERROR count = 0; exceptions {} with rows; no deletes; child logs kept; no crash or ENOMEM.

## Q11-Q12 (rpg-planner-ubuntu, from rpg-implementer-ubuntu's code read at 3aafdb383) [v2]
### Q11 Newborn body: (a), narrowed
- A newborn is built through the SAME species/archetype path that builds a t0 body of that species: its declared body model, attribute tendencies and derived stats. Any seeded draw on that path is keyed by the newborn's own id.
- **No CHILD scaling exists in src** (life_stage.py has only goal multipliers). So the newborn gets the species' t0 values, at full HP. Adding a CHILD body scale would be a new mechanic: a backlog item, not this step. Disclose "newborns have adult body stats" in the step report.
- **Also fixed by this ruling, from the same code read** (generator.py:200-213, the old offspring builder):
  - age_ticks = **0** at birth. The old `short_clock_age` (just below the adult boundary) is NOT carried. A newborn is a real CHILD that matures by the normal LifeStage clock.
  - gold = **0**. A newborn carries no coin (nothing from nothing; decision 51).
  - parent ids = the two real parents (never None), birth_tick = the birth tick.
- Not a shared contract: no new field, no Bible law change beyond ECOL-06 / the ch05 text that already goes to rpg-designer. This is a cc.

### Q12 Pruning cooldowns: (a)
- `LifecycleUpdate.reproduction_cooldowns_remove` (the partner ids) is a field on a typed UPDATE, not a durable state field. The state's shape (Dict[int,int]) is unchanged. It is NOT on the pre-bind list, and no FIELD_RULES row or fingerprint entry is needed.
- Conditions:
  - ApplyPath applies remove, then add, within one update, so a same-tick re-add survives;
  - merge() of two updates unions both lists;
  - removing an absent key is a no-op, not an error;
  - unit tests cover all three, plus a serialise round trip of the patch if patches are serialised anywhere (replay/log).
- (b) was rejected: a whole-map replace races any other writer in the same tick.
