# Draft (rpg-designer, 2026-11-22): gate combat rows grouped by attacker motive

Owner direction: #715 7074514233 "Group by motive". It replaces the diet grouping and O6's "not eaten = bad" framing.
Still standing: no person class (7074277591), every kind/group (7074345722), and 'none' counted (7074477873).
Status: DESIGN, for the owner with numbers. Nothing lands from it.

## 1. What the engine has at attack time (inspected, NEW 87792e3e8)
- There is no motive field. The ATTACK task (tactical.py:735, tactical_flight_guard.py:76, tactical_hold.py:41) names the target, not the reason. The state does not record which site wrote it.
- The engine DOES decide every attack from typed, pure reads. Those reads are the motive:
  - `hostility.relation(attacker, target, night=, tick=)` -> `appraisal.Relation`:
    - FACTION_HOSTILE: the faction semantics rate it hostile;
    - PREDATION: hungry, my diet can eat its body, and I believe I can overcome it.
    These two (ATTACK_RELATIONS) are the only relations that put a body on the hostile list (perceived_hostile).
  - `tactical_threat.attacked_me_recently(hostile, subject, tick)`: the typed hit record (last_hit_attackers, last_hit_tick) within ATTACKED_RECENTLY_WINDOW_TICKS. It is target_score's self-defence term.
  - Strategic: current_objective_id -> ObjectiveState.target_entity_id and kind (DEFEAT_ENEMY ...), plus current project kind.
- Precedent: `hostility.is_feeding_kill` already classifies a KILL by `relation(...) is PREDATION` at observation time (O6's FEEDING_KILL). So a derived motive read is an existing pattern, not a new mechanism.

## 2. Motive of an ENGAGEMENT (first match, read on the PRIOR state of the engagement's FIRST attack)
An engagement is one attacker on one victim with gaps <= 50t, as now.
1. DEFEND: the victim hit the attacker within the window before the first attack (`attacked_me_recently(victim, attacker, tick)`).
2. OBJECTIVE: the attacker's active objective targets this victim (`target_entity_id == victim.id`). This is where goal-driven fights land (quest, bounty and, later, loot).
3. HUNT: `relation(attacker, victim) is PREDATION`.
4. HOSTILE: `relation(attacker, victim) is FACTION_HOSTILE` (faction or kind hostility, aggression).
5. UNCLASSED: none of the above, reported with its inputs. A non-trivial UNCLASSED share is itself a finding: an attack with no basis the engine names.

Reasons for this design:
- Classify by the engagement's first attack, not each hit. Otherwise a hunt becomes "defend" as soon as the prey strikes back.
- Every hit of the engagement carries the engagement's motive.
- A per-hit relation is also kept as information.
- Owner words not yet in the engine: "loot" and "experience" have no engine motive today (they could only arrive as an OBJECTIVE). "Guard" and "instinct" read as HOSTILE today, and split out when TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS (decision 62) lands a typed fight reason.
- The gate does NOT wait for that ticket. When it lands, HOSTILE splits by the declared reason, a planned re-record.

## 3. Gate rows (testing-planner owns the gate; owner first, before/after table)
- O3 -> `attacks_by_motive.<MOTIVE>`: hits in engagements of that motive, summed over every attacker kind/group including 'none', and every victim.
  - Context table: motive x attacker group (no verdict).
- O6 -> `kills_by_motive.<MOTIVE>`: kills, summed the same way. "Not eaten" is no longer a defect.
  - For HUNT only, `eaten_share` (feeding kills / HUNT kills) is reported as information: an unfinished hunt says something about hunting, it is not a harm.
  - The owner's "Add the counter" (7074520394, ON HOLD) assumed a per-group O6 row. That row is gone, so the counter question goes back to the owner reframed per motive. Not decided here.
- The derivation is computed in observability from the ledger's typed inputs, read-only. The ledger key needs the engagement motive, which is a ledger layout change. That is a src change through rpg-planner, with tests (motive per class, first-attack rule, the DEFEND-vs-HUNT order).
- A typed engine motive record (a field with a lifecycle) is NOT proposed. The engine's own pure reads are the source of truth, and a stored copy would be a second source.

## 4. Trace kit (O3' + Q2)
- Stage 1 records the motive INPUTS on every attack row, raw. The class is derived in the summary (a pure function with controls), so it can be recomputed:
  - relation(attacker, victim) and relation(victim, attacker) on the prior state;
  - attacked_me_recently both ways;
  - the attacker's objective id, kind and target_entity_id;
  - the project kind;
  - the task payload action and reason (HOLD_BETWEEN_BLOWS);
  - the attacker's mode before.
- Stage 2 adds the same reads per tick for the subjects.
- Non-perturbation is guarded by twin hash equality. relation() reaches the perception gate, so equality must hold.

## 5. R1-R7 under motive grouping
- The judged population of the bug trace is unchanged: the attacks that MOVED, wolves (the 'meat' group). This only NAMES the population flagged by the 0.6->24 move; it is not a gate category.
- Every result is also split by motive, as context. The owner's numbers come from that split.
- R1 becomes "motive consistency" (was diet): every judged engagement has a motive, and HUNT implies the attacker's declared diet can eat the victim's body. A HUNT by a non-meat diet is a classifier or appraisal defect.
- R2-R7: text and thresholds unchanged.
- TIED_GROUPS stays ("meat",) for the verdict.

## 6. Gate-side answers (to testing-planner's points, 2026-11-22)
1. Old keys:
   - Sealed ledgers, the V1 baselines and the 20 saved reports keep their own definition, and are read under it only.
   - No back-fill and no imputed motive.
   - The motive rows begin at v3. The old O3/O6 rows are marked retired at v3, shown, and never compared with motive rows.
   - The owner's before/after table comes from the re-run trace arms, NEW and BASE. Both definitions can be computed there from the same sealed cells: the old person split from the ledger keys, and the motive split from the rows.
   - The 20 reports appear as old-definition context only.
   - The table states its coverage: FLW, seeds 42/43/45. The gate's own worlds and seeds are measured at the v3 re-record.
2. Row identity: ONE row id per metric, with the motive in the key, as the group is today.
   - O3.attacks_by_motive keyed motive=<M>, and O6.kills_by_motive keyed motive=<M>.
   - A new motive (for example HOSTILE split by decision 62) is then a new key, not a new row id. AC4a applies per key.
   - The motive x group table is context, not part of the key.
3. Classifier inputs: engagement_motive reads ONLY typed values:
   - the Relation enum value of relation(attacker, victim) on the prior state;
   - the bool attacked_me_recently(victim, attacker, tick);
   - whether the attacker's ObjectiveState.target_entity_id == victim id.
   The task payload "reason", the objective kind, the project kind and the mode are information only, in both the trace and the gate, and never inputs. A control asserts this: changing the reason string never changes the class.
4. UNCLASSED is a tracked key of both rows, never a silent drop. Its size, by count and share, goes in the owner's table.

## 7. Arms with different relation() signatures (ruled before data, 2026-11-22)
- The signatures differ. NEW 87792e3e8 hostility.py:81 is `relation(entity, other, source=None, *, night, tick)`. BASE e72270894 hostility.py:80 is `relation(entity, other, source=None)`.
- Rule: each arm's motive is read with THAT ARM'S OWN engine function and signature, as its own agents decided.
  - NEW: night = is_night(world_time) of the prior state, and that tick.
  - BASE: its own two-argument form.
  - Each row records `relation_form`: "night_tick" or "plain".
  - Never load one tree's function on the other tree's state.
- The form difference IS part of what is being measured. A night-dependent relation is part of the #953 change, so a motive shift between the arms (e.g. HUNT up at night on NEW) belongs to the #953/#954 effect. It is not a confound to remove.
- Cross-arm comparison is per motive key, by counts and shares, labelled "motive read by each arm's own engine". The table names the two forms.
- attacked_me_recently and the objective target match are the same in both arms.
- `source`: mirror the argument the engine itself passes on the attack path (the attacker's identity source, as tactical.py passes it via `hostile_identity_sources`) and record which source was used. Where the trace cannot resolve it, call with the default and record `source_default: true`. A default share above 0 goes in the report.
- Non-perturbation of the relation() reads needs all three:
  - twin hash equality (plain == spy) in every cell;
  - a unit control showing that a relation() call leaves the state, entity and perception-gate caches unchanged (compared before and after);
  - smoke 1's FIRST check, which is the twin hash. If it differs, stop: nothing else is read.
