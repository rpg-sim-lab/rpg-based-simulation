---
status: active
layer: strategy
authority: P1
audience: agent
tags: []
last_verified: "2026-11-23"
---

# Navigation experience memory: design v2 (rework of PR #996 under decision 56)

> AMENDMENT 1 (2026-11-23, lead ruling #715 7091393459): reports, reach and limits only, from the owner-provided external review #2 (stored as a second artifact beside the first). It adds rows R1b, R3b, R3c and R3d to §11, a widened reach line, and the new section "Limits (slice 1)". No rule, behaviour or value changes; the owner-approved text (#715 7091099713) is otherwise untouched.

Author: rpg-designer, 2026-11-23. DRAFT v2. It replaces v1 (`rpg-designer-experience-memory-design.md`, b518940d, kept unchanged) after the review by rpg-planner, the lead and an independent verifier (`expmem_review_rpg_planner.md`, sha 9e47f063). No code until the owner approves.
Inputs:
- the owner decision: #715 7090468332 / 7090493248;
- the external review `agent-working/stored_artifacts/TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON/external_review_experience_memory.md` @ 0c56b0722 ("R §n");
- the #996 head 4ab97912e.
"(i)" marks a claim inspected at that head.
Final home after the owner says yes: `docs/plans/systemic_world/experience_memory_design.md`. The roadmap §12.5 line is a separate memo-row item (§13).

## What v2 changes from v1 (the review's findings, each addressed)

| finding | v2 |
|---|---|
| No `propose_target` call passes `staged`. Writers set `movement_mode_set` AFTER the gate, so the gate can't compute intent (i: 20 `propose_target(` sites, 5 `destination_open(` sites) | The PURPOSE travels with the target: each writer passes it to the gate AND writes it with `target_set`. This is a call change at every gate site, enforced by the static check (§4) |
| A review written by gate callers means many writers, and probes spend reviews | ONE review site: the subject's strategic consume step. The gate is a pure read, so probes are safe by construction (§6) |
| ACCESS retirement incomplete: `_blocker_hit`, giveup_count, filing anchors | `_blocker_hit` leaves the gate. The #996-new fields are dropped (never on main). A'' gets a purpose-scoped filing source (§7) |
| A timer per cause isn't reason-based | The ring check's refusal ReasonCodes become the evidence: bodies / static / other (v2.2), each with its own due rule (§5, §6) |
| Same-purpose refusal of a starving body | A need-severity due rule (packet Q13) plus check E9 (hard 0) |
| Facts: no ProjectKind hunger/fatigue; no FLEE; the "route search"; GiveUpRecord's life; the per-anchor limit; the memo row | Corrected below |

## 1. Kept unchanged from #996 (R §13 Stage 1)

- Movement's way-round tracking and bounded give-up (2.213), `ReasonCode.WAYROUND_GIVE_UP`, and the immediate `clear_target` / `clear_path`.
- `GiveUpRecord` on `navigation.giveup_records`: hashed (`giveup_canonical`) and checkpointed (FIELD_RULES `giveup_records`), held until the subject's next strategic pass consumes it (the 10 + cadence window of 2.220), cap `GIVEUP_RECORDS_CAP` 4.
- The A'' anchor rule `anchored_target` for the record's own anchor.
- The pending-record branch of `destination_suppressed`: a give-up not yet consumed refuses its anchor for ANY purpose until consumed. It stays purpose-blind on purpose: it is the same-tick and same-window protection the owner kept.
- The static architecture check over the place-target writer FAMILY (`propose_target`, `destination_open`, `destination_suppressed`, `suppressed_move_to`, `retreat_destination`, `_open_or_none`), with its mutants, adapted to require the purpose argument.
- Two structural code constants are declared structural, not tuning:
  - `GIVEUP_NEAR_RADIUS` = 1: the task layer's one-tile jitter tolerance;
  - `GIVEUP_RECORDS_CAP` = 4: the per-pass consumption bound.

## 2. Durable state

### 2.1 The purpose of a target (NEW, on navigation)

```python
@dataclass(frozen=True, slots=True)
class TargetPurpose:
    project_kind: str     # the subject's current project's kind VALUE ("hunger" / "fatigue" are the need-project kinds, NEED_PROJECT_KINDS strategic.py:576 (i); ProjectKind values otherwise, e.g. "recovery", "combat"); "none" when no project is current
    movement_mode: str    # MovementMode .value the writer sets with this target: PURSUE, RETREAT, HOLD, REPOSITION, INTERCEPT, GUARD, REGROUP, WANDER (movement_modes.py (i))
```

- The field is `NavigationState.target_purpose: Optional[TargetPurpose]`, LAST in the dataclass, with a FIELD_RULES row. It is canonical and hashed.
- It is written by `NavigationUpdate.target_purpose_set` together with every NEW `target_set` (one that differs from the stored target), and cleared with the target. The patch refuses a new-target `target_set` with no purpose (a static check and a unit test).
- Re-emission sites (executor.py:97-110, worker_logic.py:22-32, tactical_hold.py:103 KEEP_WALKING (i)) carry the STORED purpose, and end the move typed when it is None (§4, v2.4).
- Old checkpoints load None. A target with purpose None is matched only by the pending-record branch, never by an experience.

### 2.2 The experience (NEW, on memory)

- The location is `MemoryModel.navigation: NavigationExperienceMemory`, LAST in MemoryModel, with a FIELD_RULES row. Not the untyped `ExperienceMemory` shell, not `FailedSearchMemory` (Q1).

```python
class NavCause(str, Enum):
    OSCILLATION = "oscillation"          # a way-round tile existed, but the bounded count passed wayround_limit with no net progress (movement.py:207-210 (i))
    RING_BLOCKED = "ring_blocked"        # the ONE-RING check found no legal tile: the sidestep plus the 4 orthogonal neighbours (movement.py:167-187 (i)); NOT a route search
    UNCLASSIFIED = "unclassified"        # reserved; slice 1 writes none

class RingEvidence(str, Enum):           # from the ReasonCode each ring tile was refused with (verify_movement_legality legality.py:219-246 (i)); v2.2
    BODIES = "bodies"                    # OCCUPANCY_VIOLATION or IDEMPOTENCY_VIOLATION (legality.py:159: the tile is claimed by another mover this tick): a body
    STATIC = "static"                    # verify_occupancy's static reason: terrain, building or bounds
    OTHER = "other"                      # any other refusal (ACTION_EXHAUSTION, ATTACKER_STATUS_BLOCKED, ...). Rarely produced: the oscillation branch follows a step that already passed the status and
                                         # readiness checks, and readiness doesn't depend on the tile (verifier v2.1 item 3), so slice 1 gives OTHER no due rule of its own (§5)

class NavExperienceStatus(str, Enum):
    ACTIVE = "active"
    REVIEWED = "reviewed"

class ReviewReason(str, Enum):
    DUE_TICK = "due_tick"
    APPROACH_CHANGED = "approach_changed"
    NEED_SEVERE = "need_severe"
    TARGET_ACCEPTED = "target_accepted"   # v2.2 latch: the subject holds an accepted target at the anchor with the record's purpose (§4)

@dataclass(frozen=True, slots=True)
class NavigationExperience:
    experience_id: str                    # f"nx_{x}_{y}_{purpose.project_kind}_{purpose.movement_mode}" built from .value strings: one live record per (anchor, purpose)
    anchor: Tuple[int, int]
    purpose: TargetPurpose
    cause: NavCause
    ring_evidence: Tuple[RingEvidence, ...]   # sorted, distinct; () for OSCILLATION
    from_position: Tuple[int, int]
    target_tile: Tuple[int, int]
    need_service: Optional[str]           # v2.4: "EAT" / "REST" when the anchor is a tile of a building serving that action, else None. Resolved by the existing service lookup (service_tile + get_building_at) through main's existing building-kind service table SERVICE_KINDS = {"REST": {inn, home}, "EAT": {inn}} (building_services.py:29 (i)), which admission, arrival and REST already read. The design REUSES it and adds no new name read. It is BUILDING kinds, not a body's kind, role or faction. No planned data-driven replacement for EAT/REST was found (search_docs; WORK is already a declared set in the same table). The consume step gains `state` (its caller intelligence.py:382 has it)
    project_id: str                       # "" when none
    observed_tick: int
    cycle: int                            # identity and history only; never enters a due rule
    next_review_tick: Optional[int]       # None when the due rule is trigger-only (§6)
    status: NavExperienceStatus
    reviewed_tick: Optional[int]
    review_reason: Optional[ReviewReason]
    project_giveups: int                  # §8

@dataclass(frozen=True, slots=True)
class NavigationExperienceMemory:
    records: Tuple[NavigationExperience, ...] = ()   # sorted by experience_id
```

- **Lifecycle:**
  - CREATE and NEW CYCLE (cycle + 1, all evidence and due fields derived afresh) on a consumed give-up.
  - REVIEW (status REVIEWED) when a due rule holds.
  - EVICT at the cap (packet Q14), in this order (v2.2):
    1. the REVIEWED record with the oldest `reviewed_tick`, ties by `experience_id`;
    2. else an ACTIVE record whose due rule holds now, oldest `observed_tick` first, ties by id;
    3. else the ACTIVE record with the oldest `observed_tick`, ties by id. This one is counted and reported, since it ends a live refusal.
  - A project ending does NOT touch experiences: they are the subject's, scoped by purpose, not by project. Only `project_giveups` reads `project_id`.
  - Death: the record goes with the entity.
- **Canonical state:** every field is in `to_canonical_dict`, records sorted by id, hashed and checkpointed. Old checkpoints load `records=()`.
- **Inspection:** the presenter that shapes the entity's `memory` sub-models for the entity detail read model gains the sub-model, shaped, not raw. The implementer names the file at investigation.

## 3. The producer: evidence, not inference (R §6.2, lead point 1)

- `_find_way_round_loop` AND `_find_sidestep` (movement.py:159 drops its reason too: `s_ok, _` (i)) are widened to return, with their tile or None, the ReasonCode of EACH tile they refused, as a `RingEvidence` mapped from that code. The legality calls are the ones they already make, so no new world reads are added.
- `_oscillation_replan` builds the `GiveUpRecord` with:
  - `cause`: RING_BLOCKED if the ring check found no tile, else OSCILLATION;
  - `ring_evidence`;
  - `from_position`: the subject's tile;
  - `target_tile`;
  - `purpose` = the subject's STORED `navigation.target_purpose`, i.e. the purpose of the pursuit that failed, as written by its writer. No inference.
- The tick: the producer receives the kernel's `current_tick` explicitly. A context with no tick raises in tests and never stamps 0 (movement.py:198 today uses `getattr(..., "tick", 0)` (i)).
- `wait_count >= 5` still files no record (unchanged, as on main).
  - The verifier's wait-replan loop: a target blocked by waiting is cleared, re-accepted while due, blocked and cleared again, never renewing a cycle or counting towards project_giveups. This is main's existing wait-replan behaviour, not this producer's.
  - What bounds it: each turn costs at least 5 ticks of waiting plus a re-choice. It is not hidden: R4 counts wait-replans per (anchor, purpose).
  - Making wait-replans a third evidenced cause (BODIES, timed) is a named follow-up, not slice 1.
- A give-up whose stored purpose is None (a target restored from an old checkpoint) files NO experience (v2.3). The pending GiveUpRecord still gives its purpose-blind same-window protection. It is counted in R1 ('give-ups without purpose'). No id is built from None.

## 4. The gate: purpose passed in (lead / verifier gap 1)

- `propose_target(entity, pos, tick, purpose, staged=None)` and `destination_open(entity, pos, tick, purpose, staged=None)`.
- v2.4, closing the CLASS of gated-vs-stored mismatches (the lead's rule): the purpose comes from ONE pure function, `purpose_of(entity, staged, mode_set) -> Optional[TargetPurpose]`. `mode_set` is the mode the writer's update sets, or None.
  - It returns (the project kind current after `staged`, the EFFECTIVE mode the update leaves stored). The effective mode is `mode_set` if given; else the stored mode after `hold_reset_kwargs` (hold_mode.py:37-44 (i): HOLD becomes WANDER when the writer resets a hold); else the stored mode.
  - So the strategic need walks (intelligence.py:530, 551), the investigate MOVE_TO (action_intent.py:143) and every writer get the mode the stored target will really carry.
  - The writer calls it ONCE, binds the result to one name, and passes that SAME name to the gate and to `target_purpose_set`.
- Static checks (v2.4):
  - every `target_set` is accompanied by a `target_purpose_set` whose value is the same bound name as the purpose argument of the gate call guarding it (by ast name identity, as the existing check does for the position);
  - every such name is bound from `purpose_of(...)`, or, at a re-emission site, from `stored_purpose(entity)`.
- Test (v2.4): for every writer, a planted subject (with and without a stored HOLD, with and without staged project and mode) gets gate purpose == stored purpose after apply.
- RE-EMISSION sites (v2.4):
  - which ones: the executor and worker live-tracking refresh (executor.py:97-110, worker_logic.py:22-32 (i)), which re-emit `payload["target_position"]` (possibly a NEW position each tick), and tactical_hold.py:103 KEEP_WALKING, which re-emits `navigation.target`;
  - what they carry: the subject's STORED `target_purpose` (`stored_purpose(entity)`). The pursuit's purpose doesn't change because its tracked position moved;
  - None (a target restored from an old checkpoint, or a payload left after a give-up cleared the target and its purpose): they end the move typed (`suppressed_move_end`), and the subject re-decides and gets a fresh purpose.
  - So the patch rule is now WITHOUT exception: every `target_set` carries a purpose.
- A hold that targets the subject's own tile (tactical.py:526, tactical_flight_guard.py:84 (i)) gets (project kind, HOLD) from `purpose_of`. It makes no pursuit, so it can't produce a give-up.
- Helpers that call the gate inside themselves (retreat_destination, _open_or_none, _destination_or_hold, stalemate_break_update, _retreat, _walk_to (i)) take `purpose` as a PARAMETER, passed under the caller's bound name. The static check follows the name through the helper (a per-helper rule).
- Mode consistency: the static check also requires `purpose_of`'s `mode_set` argument and the update's `movement_mode_set` to be the same bound name, or both absent.
- Named LEAKS (not starvation risks):
  - mode-only writes (blacksmith.py:251, pipeline_phases/actions.py:92, redirection.py:145 (i)) change the stored mode under a kept target, so that target's stored purpose and its live mode can differ until the next target write;
  - a writer that sets no mode takes whatever mode was left stored (after the hold reset). Two walks to one place under different leftover modes file and match DIFFERENT records, so one may re-try a place the other gave up on. R1 reports records per place with more than one mode.
- The call sites change: 20 `propose_target` + 5 `destination_open` = 25 (i, corrected from 26), plus the helpers. There are 28 `target_set` writes in all, including the unwired redirection.py:98/129/144, which the static check covers if they are ever wired. The static check's UNWIRED exemption for redirection.py is REMOVED the moment any of those writes is wired.
- The static check rejects a gate call without `purpose`, and a new-target `target_set` without `target_purpose_set`.
- `destination_suppressed` reads, in order:
  1. the PENDING give-up records, any purpose: unchanged;
  2. an ACTIVE experience whose `near_anchor(pos, anchor)` and `purpose == purpose` AND whose §5 due rule does NOT hold at this call (v2.1) AND which is NOT LATCHED (v2.2).
  - LATCHED (v2.5, the stop rule's narrowing) = the subject's STORED target is within `GIVEUP_NEAR_RADIUS` of the anchor, its stored `target_purpose` equals the record's purpose, AND the stored `target_gated` is True.
    - `NavigationState.target_gated: bool` is NEW, LAST, with a FIELD_RULES row, hashed.
    - It is written True ONLY by a `target_set` whose position passed a gate call (the bound purpose from `purpose_of` under a guarding gate).
    - It is written False by every by-value own-tile write that skips the gate: tactical.py:268/305/526 (RETREAT), :461 stalemate break (WANDER), tactical_flight_guard.py:84 (RETREAT), tactical_avoid.py:62 (RETREAT) (i, pass 5). These now take `ungated_purpose(entity, mode_set)`.
    - A re-emission carries the stored flag unchanged. Old checkpoints load False.
    - Why a flag and not "target ≠ own tile": a hold target can survive a displacement (a yield or a swap), so it later differs from the own tile and would latch. The flag records HOW the target was accepted, which is the fact the latch argument needs: only a gated acceptance could have happened while the record was due.
    - The v2.3 HOLD exclusion is dropped (it missed RETREAT and WANDER holds). The v2.4 narrowing "PURSUE or need_service" is dropped too: it doesn't close the hole, because need walks via _walk_to are WANDER (tactical_objective.py:46 (i)). The flag closes it for every mode.
    - Static check: a by-value `target_set` must bind `ungated_purpose`; a gated one must bind `purpose_of`. Neither may mix.
    - Patch rule (v2.5 confirm pass): `target_gated` and `target_purpose` are written ONLY together with the target the patch actually keeps; otherwise they are left as stored. When `anchored_target` (giveup_records.py:86-99 (i)) DROPS an update's `target_set` and keeps the stored target, that update's `target_gated_set` and `target_purpose_set` are dropped with it. So a stored own-tile hold can never pick up True and the dropped write's purpose. Unit test: a dropped gated write beside a stored ungated hold leaves `target_gated` False and the stored purpose unchanged.
    - Bounded side effect, named: a latched target also opens same-purpose proposals within radius 1 of the anchor while the record is not due. They are at most the 3x3 tiles around the held target, for as long as the subject holds it.
  - Why that fact is a monotone latch: a give-up clears the target at once, and until consumption the pending branch refuses the anchor for every purpose. So a stored target there with that purpose can only have been accepted AFTER the give-up, while the record was due. The fact stays true until the subject itself drops or changes that target.
  - So a non-monotone rule (APPROACH or NEED) that stops holding mid-walk can't re-refuse the accepted target: the :514 clear and the executor's re-affirmation see the latch.
  - The consume step then records the review (reason TARGET_ACCEPTED if no due rule holds by then).
  - The one remaining gap: if the subject drops that target for another reason before any strategic pass records the review, AND the due rule no longer holds, a new proposal is refused again. That is consistent (the record is not due at that moment), and it is counted (E11b, reported).
  - The due rule is evaluated in the gate as a PURE read: the subject's own tick, position and needs (v2.2: no readiness or status rule, so no move_speed_mult or state is needed at the gate).
  - So a record that is due stops refusing AT ONCE, whatever the strategic cadence. The consume step only RECORDS the review later; it is the one writer, and the gate writes nothing.
  - Refusal liveness does not depend on how often the strategic pass serves the subject (the lead's risk on v2).
  - Nothing else: `_blocker_hit` is REMOVED (§7). A REVIEWED record never refuses.
  - Work-queue tier (v2.2, a design argument, not an owner question): an ACTIVE experience does NOT raise the subject's tier.
    - The verifier showed that a calm tier-7 subject can be starved of strategic passes indefinitely (budget, rotation and the 1-in-10 cadence). v2.2's correctness doesn't depend on those passes for experiences: the gate's due read plus the latch decide refusal from the subject's own state at every call.
    - What a pass still does for experiences is bookkeeping: recording reviews and freeing slots. A starved subject's due records refuse nothing meanwhile, and eviction prefers a due ACTIVE record (§2.2).
    - The PENDING record keeps #996's tier 6b and slow-path forcing, unchanged. That protection needs consumption.
    - #996's tier 2 came from the unfiled give-up ACCESS blocker, which no longer exists. Its window is the pending record's window, already served by 6b, so nothing is lost.
    - E12 measures the gaps, and E11 / E11b measure the refusals.
- The strategic pass's `destination_open(..., staged)` calls (intelligence.py:290, 514, 527, 548, 555 (i)) pass their purpose too.
- The stored-target clear at :514 becomes: clear a STORED target near an ACTIVE experience only when the stored `target_purpose` equals the experience's purpose.
- The gate WRITES NOTHING. Probe calls in if-chains and loops (tactical.py:346, 361, 507, 546, 588; tactical_destinations.py:113-120 (i)) are safe.

## 5. Cause and evidence → due rule (reason-based, lead points 1-2)

| cause / evidence | due when (any one holds) | rationale |
|---|---|---|
| OSCILLATION | `tick >= observed_tick + oscillation_review_delay`, or APPROACH_CHANGED | the loop is a property of this start and this local traffic; a new start or a short wait is a fair new trial |
| RING_BLOCKED with BODIES among the evidence | `tick >= observed_tick + bodies_review_delay`, or APPROACH_CHANGED | bodies move; time is the evidence-backed review |
| RING_BLOCKED, STATIC only | APPROACH_CHANGED only (next_review_tick None) | terrain doesn't change on its own; re-polling it from the same tile is wasted (R §7.2) |
| RING_BLOCKED with OTHER and no BODIES (v2.2) | `tick >= observed_tick + oscillation_review_delay`, or APPROACH_CHANGED | rare (see RingEvidence); no evidence-specific rule until a producer makes it common, so the conservative time rule applies |
| any cause, any purpose, `need_service` set (v2.4) | NEED_SEVERE: `need_service == "EAT"` and hunger ≥ `STARVING_LINE` (95.0, starvation.py:19/29 (i)), or `need_service == "REST"` and sleep_debt ≥ `SLEEP_LINE` (98.0, need_pull.py:34 (i)) (packet Q13) | keyed on the body's need line plus a food or bed TARGET, not on the project kind. So a survival walk filed under RECOVERY (adventure/mapper.py:32, 46 (i)), or under no project, is covered too. Wild food (a forage node, a carcass, prey) is NOT a SERVICE tile and is not covered in slice 1: E9b reports it |

- APPROACH_CHANGED = Chebyshev(the subject's tile, `from_position`) > `approach_change_radius`. Every rule reads only the subject's OWN state, so the information boundary holds (R §7.3).
- Liveness (R §14.8): every row has a rule that eventually holds for a subject that moves, recovers or gets hungrier. STATIC-only waits for movement; a subject that never moves again doesn't need the place.
- The verifier's caveat stands and is measured: walking away makes APPROACH_CHANGED fire soon, so for many records the delay seldom binds. That is the intended "try from elsewhere" behaviour. Its loop count is report R3, bounded by §8.

## 6. Review: ONE site, a fresh cycle every time (owner constraint 3; R §8)

- The single writer of experience state is the subject's strategic pass consume step (`consume_giveup_records`). It runs on the live pipeline each pass for the subject: NOT MemoryUpdatePhase, NOT `ENABLE_MEMORY_UPDATE`. In order, per pass:
  1. REVIEW: every ACTIVE record of the subject whose due rule holds is set REVIEWED (`reviewed_tick`, `review_reason` = the first rule that holds, in the table's order). This is O(cap).
  2. FILE: each pending GiveUpRecord upserts its (anchor, purpose) record:
     - new: cycle 1;
     - existing: cycle + 1, with evidence, due fields and status ACTIVE replaced, derived ONLY from this give-up's evidence and the data values;
     - nothing from the old record's timing survives.
  3. CLEAR the pending records (unchanged).
- It emits one typed `NavigationExperienceUpdate` (an upsert list plus a review list, by id and cycle) on the subject's `EntityUpdate`, applied with the strategic update.
  - Idempotent: a review applies only if the stored record has that cycle and is ACTIVE.
  - An upsert of cycle n + 1 supersedes a review of cycle n in the same update.
  - No other writer exists, so there's no cross-phase merge order to define.
- The cost of one review site (v2.1): NONE for behaviour, because the gate already treats a due record as non-refusing (§4). The consume step's review is bookkeeping: it fixes `reviewed_tick` and `review_reason` and frees the slot. A cycle's `reviewed_tick` may lag its due moment by the subject's strategic gap, and E12 reports that lag.
- **"Fresh evaluation" honestly:** neither cause can be re-judged without walking. The review opens the place, and the next attempt is the evaluation. If it fails, the new cycle's rule is derived from the new evidence. No doubling, and no count in any delay (R §8.3-8.4).
- **Amendment (#996 CI fix, item 2, architecture review; the owner-approved text above is unchanged):** the consume step takes NO `state` and looks up no building. The PRODUCER (`MovementSystem._oscillation_replan`, engine layer) reads the needs the place serves at the give-up, through the same building-kind table (`need_services_at`: `service_tile` + `SERVICE_KINDS`), and carries them on the `GiveUpRecord` (`need_services`, a frozen set of `NeedService`, last field). The step copies them onto the experience. The needs are therefore frozen at give-up time, not at consume time (the next strategic pass, a few ticks later), so a building that appears or vanishes in that window is no longer seen. The starving and sleep lines are read from `src/core/need_lines.py`, the one source of 95.0 and 98.0 (engine modules import them from there and keep their names).

## 7. Retiring ACCESS suppression for give-ups (owner constraint 6; verifier gap 3)

- The consume step files NO ACCESS blocker for a give-up. These #996-new parts are DROPPED; none is on main, so no checkpoint compatibility is needed:
- **Implemented (step (e), 381a646bc; the approved text above is unchanged):** `_blocker_hit`, `BlockerState.giveup_count` with its FIELD_RULES row, the `:g<n>` fingerprint part and the presenter key are gone; `giveup_filing_update` is now `giveup_project_end_update` (it ends the project and files no blocker); `filed_suppression_anchors` and `navigation_with_filing_anchor` read the experience update and are purpose-scoped. The statements below are the record of what was dropped.
  - `_blocker_hit` (the gate's blocker branch);
  - `BlockerState.giveup_count` and its FIELD_RULES row;
  - `giveup_filing_update`'s blocker filing;
  - `filed_suppression_anchors` / `navigation_with_filing_anchor`;
  - `blocker_timeout_suppression`'s backoff use for give-ups.
- **Main's ACCESS blockers** (`infer_blockers`, blocker_lifecycle.py:79 at 4ab97912e (i)): unchanged. They keep main's meaning and readers (resolution, detour, ResolveBlockerScorer, score modifiers) and refuse no destination, as on main. They share the `blocker_access_<x>_<y>` id space with nothing new, since experiences use `nx_` ids.
  - A give-up does NOT reach `infer_blockers`: its failure reason is WAYROUND_GIVE_UP, which is not in `("PATH_NOT_FOUND", "STUCK", "OSCILLATING")` (i).
  - This is a statement of fact for the owner, not a question.
- **The A'' third source** (the pass's filing anchors on `target_clear_anchors`) is REPLACED. When step 2 files or renews an ACTIVE record, its anchor rides `target_clear_anchors` only if the subject's STORED `target_purpose` equals the record's purpose. So a stored target for another purpose stays. The record's own-anchor rule (the first source) is unchanged.

## 8. Ending a project on repeated give-ups (Q13; lead point 6)

- #996 counts give-ups per ANCHOR across all the subject's projects (`giveup_count`, blocker_lifecycle.py:364 (i)), then ends the CURRENT project at `access_giveup_limit` 4.
- v2's recommendation: `project_giveups` counts per (anchor, purpose) within ONE project_id and resets under another project. At `access_giveup_limit`, THAT project ends, typed `DESTINATION_GIVEN_UP`.
- **Implemented (step (e), 381a646bc; the approved text is unchanged):** `giveup_project_end_update` ends the project current at the pass when an upserted experience's `project_giveups` reaches `access_giveup_limit` (4); `project_giveups` is per (anchor, purpose) within the experience's `project_id` and restarts under another project. The "#996 counts per ANCHOR" bullet above describes the dropped behaviour.
- Liveness when projects re-form: a re-formed project restarts the count, but every retry is still gated by §5's due rule. So retries per (anchor, purpose) are bounded by the due rules, not by the limit.
- This is measured, not assumed: R3 reports give-ups per (anchor, purpose) per 2400 t (the max and the distribution). If R3 shows a loop, the owner sees it before landing.

## 9. Data values (proposed; shown in the packet as numbers)

New file `data/content/strategy/navigation_experience_settings.yaml`, warmed catalog, part of the fingerprint:

| key | proposed | options shown | method / why |
|---|---|---|---|
| oscillation_review_delay | 100 t | 50 / 100 / 200 | the first #996 window, kept so the first cycle is comparable to the measured #996 behaviour; never grows |
| bodies_review_delay | 50 t | 25 / 50 / 100 | shorter than oscillation: bodies are the evidence that the block moves |
| approach_change_radius | 5 tiles | 3 / 5 / 10 | beyond the one-ring (1) plus the sidestep, so the new start is outside the failed ring's neighbourhood; well within the scavenge and hunt radii |
| navigation_experience_cap | 8 | 4 / 8 / 16 | twice the pending cap; per subject; bounds the O(cap) review and gate work |
| access_giveup_limit (existing file) | 4 | 3 / 4 / 6 | kept value; the new rationale is four failed cycles of one plan at one place (the old "backoff reaches 800" rationale goes) |

The starving and exhausted lines are the existing need lines; no new value.

## 10. Determinism, replay, cost

- No RNG, no wall clock, ticks from state, ids from `.value` strings, records sorted, one writer.
- Hashed, checkpointed, round-trip tested; observability counters outside the hash.
- Cost:
  - the gate: O(pending ≤ 4 + records ≤ cap) per call, like today's `_blocker_hit` loop;
  - the consume step: O(cap + 4) per strategic pass;
  - no global index, no scheduler entry, no per-tick scan.
- NFR: tick time against main and #996 head within the perf tripwire (E8).
- Bodies: no species, role, faction or entity name is read. The inputs are the subject's own position, purpose, stored target and needs, plus movement's evidence. Buildings: `need_service` and E6 classify a "food or bed tile" through main's existing building-kind SERVICE_KINDS table (above), with no new name read.

## 11. Own-job checks, BEFORE data

Kit approved at a sha, controls that bite, fresh trees, spy hash = plain twin.

| id | bar | kind |
|---|---|---|
| E1 | same-update re-target within Chebyshev 1 of the own give-up anchor = 0 (A'') | hard |
| E2 | a target_set accepted while an ACTIVE same-purpose record covers it = 0 | hard |
| E3 | a refusal by an ACTIVE record whose purpose differs from the proposal's = 0 | hard |
| E4 | every new cycle's due fields equal §5's rule applied to that give-up's evidence and §9's values; none differs by cycle number | hard |
| E5 | reviews ≤ 1 per (experience_id, cycle); every review's reason holds on the prior state | hard |
| E6 | a body refused a food or bed tile (by SERVICE properties) by a record of ANOTHER purpose = 0 | hard |
| E7 | hashseed 0 vs 12345: identical state at the end, all cells | hard (STOP) |
| E8 | tick time against main and #996 head | NFR, reported, owner-visible |
| E9 | a body at or past the starving (hunger) or exhausted (sleep_debt) line refused a SERVICE food tile (hunger) or bed tile (sleep_debt) by ANY record: count and duration | hard 0 if Q13 = yes (the gate's due read opens a NEED_SEVERE place at once); reported if no |
| E9b | the same for wild food targets (forage node, carcass, prey position) | reported (slice 1 doesn't cover them) |
| E10 | every `target_set` carries a purpose | hard |
| E11 | a refusal by a record whose §5 due rule held, or which was LATCHED, on that call's prior state = 0 (v2.1 / v2.2) | hard |
| E11b | a refusal of a (record, cycle) that had earlier been accepted while due (the §4 remaining gap): count, and the ticks since that acceptance | reported |
| E12 | strategic passes per subject per 2400 t (distribution), and the LONGEST gap with no strategic pass while the subject holds an ACTIVE experience or a pending record, per cell; plus the lag from due to recorded review | reported. Not a hard bar: E11 makes refusal liveness independent of the gap. The pending-record gap is already bounded by tier 6b (2.220), and E12 confirms that bound holds. No product counter exists (verifier, inspected), so the own-job kit counts passes itself through a pass-through on the per-subject strategic entry. No product field is added for it |
| R1 | give-ups, give-ups WITHOUT purpose (no record filed), records, records per place with more than one mode (the §4 leak), cycles, reviews by reason, refusals by purpose (the `project_kind == "none"` bucket shown apart), cross-purpose passes, evictions, project ends, re-emissions ended for a None purpose | reported |
| R2 | the old F2 G1-held / G1 / G3 rows on the reworked head | reported; G3 = D6 |
| R3 | give-ups per (anchor, purpose) per 2400 t: max, distribution, retry loops | reported, owner-visible |
| R4 | wait-replans (wait_count >= 5 clears) per (anchor, purpose) per 2400 t, and how many happened at a place with an ACTIVE or latched record | reported, owner-visible (v2.3) |
| R1b | (amendment 1) same-anchor fragmentation: records per anchor tile across ALL purposes (count, max, the anchors with > 1 live record), and ACTIVE evictions (Q14) per cell with each evicted record's purpose and age | reported, owner-visible |
| R3b | (amendment 1) retries per (anchor, purpose) that follow an APPROACH_CHANGED review: count, Chebyshev distance and elapsed ticks between consecutive attempts, and how many of those retries failed again with NO navigation progress (best distance to the anchor not improved over the previous cycle) | reported, owner-visible |
| R3c | (amendment 1) DESTINATION_GIVEN_UP project ends STRATIFIED: ends whose counted give-ups had at least one APPROACH_CHANGED review between cycles vs ends with none. If premature abandonment shows (ends with no approach change), the POLICY is revisited (Q12), never the review delay | reported, owner-visible |
| R3d | (amendment 1) STATIC-only records: count, how long each stayed ACTIVE, and how many were still ACTIVE at the end of the run while the subject never left the approach radius (the Limits blind spot, measured) | reported |

- Reach rule: each cell has ≥ 1 give-up, ≥ 1 record, ≥ 1 refusal and ≥ 1 review, else VOID. A planted A-B-loop scene at a building is added if a base cell can't reach it.
- Reach rule, widened (amendment 1): across the run set, at least ONE APPROACH_CHANGED review, ONE STATIC-only record, ONE DESTINATION_GIVEN_UP end from repeated give-ups and ONE eviction must each occur, else the set is VOID for that case. A planted scene is added for any case a base cell cannot reach (a building corner with terrain only for STATIC; a subject walked away and back for APPROACH_CHANGED; four failing cycles in one project; more than `navigation_experience_cap` anchors for eviction).
- Unit and integration tests (R §15), as v1, plus:
  - the ring-evidence mapping per ReasonCode;
  - each due rule, including STATIC never time-due;
  - purpose written with every target_set;
  - the gate is pure (no update returned);
  - one writer (the static check);
  - eviction order;
  - the A'' purpose-scoped filing anchor.

## 12. F2 evidence and rulings: carry / void

- **Carried, because the code is unchanged:**
  - the movement give-up layer's evidence and tests: the A'' own-anchor rule, the pairing-run attribution of movement-side holds;
  - the owner's own-tile ruling, report and don't count (#715 7078467940), for E1 and G1-held;
  - G3 → the D6 ticket (#715 7078467940);
  - the pin-diff S9 part (a), hashseed determinism (#715 7090493248: "part (a) ... still runs").
- **Voided** (#715 7090493248: "F2's existing evidence and W reads describe the old head only"):
  - every F2 full-run refusal, suppressed-skip and filing number;
  - the 100·2^(n-1) backoff;
  - the reach rule "filed, suppressed_skips, refusals";
  - pin-diff (b)(c);
  - the W reads of #996.
- Divergence 2.220 is REWRITTEN as the experience memory, not appended to.

## 13. Docs, Bible, parity, and the memo-row item

- `intentional_divergences.md` 2.220: rewritten; class Intentional Gameplay Change (decision 56) + Bounded (data values).
- KNOW-05: one clause. "A place it failed to reach is remembered as its own experience, scoped to the purpose it moved with and the evidence of why, and reconsidered when that evidence's condition changes; it never forbids the place for another purpose."
- Bible ch04 (knowledge management): the model, §5's due table and the fresh-cycle rule.
- `docs/simulation/domains/memory_contract.md`: the sub-model, its single writer and the canonical fields.
- `docs/parity_ledger/strategic_cognition.yaml`: a new P0 entry (purpose-scoped refusal, evidence due rules, fresh cycle). The F2 suppression entry is marked superseded.
- Data: the new settings file; the `blocker_settings.yaml` comment on `access_giveup_limit` updated.
- **The roadmap §12.5 line is its OWN packet item:** decision 56 is milestone 1 kernel spec item 4 (m1_kernel_spec_items_2_6.md:87), and editing §12.5 needs a memo row plus a #715 entry (memo row 87). Proposed line under decision 56: "navigation part: a subject's failed approaches are its own purpose-scoped experiences (experience_memory_design.md)".

## 13b. Stop rule (v2.4, the lead's): TRIGGERED in pass 5, applied in v2.5

Pass 5 found own-tile RETREAT/WANDER holds latching ungated targets. As the rule says, slice 1 was NARROWED, not revised again: the latch now requires a GATED acceptance (`target_gated`, §4). That narrowing closes the class for every mode. The originally worded narrowing (PURSUE or need_service) did not close it, and is not used.

KEEP_WALKING (tactical_hold.py:103) re-emits navigation.target. Ending it typed on a None purpose CHANGES that branch, which today stands (:100). That happens once per old-checkpoint target, and is disclosed in 2.220.

## Limits (slice 1), amendment 1 (#715 7091393459)

- **STATIC-only blind spot.** A STATIC-only record has no time rule. If the world changes (a building is removed, terrain changes) while the subject does not move beyond `approach_change_radius`, the record stays ACTIVE and keeps refusing that purpose at that place. This is deliberate. The natural extension is a later topology-change invalidation (an event or a perceived change); a polling timer is NOT added to hide the gap. R3d measures it. The doc updates of §13 (KNOW-05 or Bible ch04) carry this limit in one sentence.
- **APPROACH_CHANGED is positional.** It fires on distance from `from_position`, not on a materially different route; a subject that moved for an unrelated reason may retry from a position with no better route. Kept for slice 1 (no route-segment identity, Q11); R3b measures it.
- **The project-end threshold counts give-ups, not independent opportunities.** Four give-ups from effectively the same approach can end a project early. R3c stratifies the ends; a revisit changes the policy, never the delay, and never reintroduces backoff.
- **The purpose key is the slice-1 NAVIGATION contract.** (project kind, movement mode) is the key for navigation experiences only, not a universal intent identity: different goals can share both and still have different success conditions. Expanding it needs evidence (R1 multi-mode records, R1b fragmentation and ACTIVE evictions).
- **"Fresh evaluation" in slice 1 means the next attempt supplies the evidence.** The review opens the place and the attempt is the evaluation. It is NOT a pre-action reassessment system; future capability, vitality or information causes will need one that checks whether the old failure condition changed before another action is spent.
- **Not reintroduced:** ACCESS blockers for give-ups, generic cooldowns, exponential backoff.

## 14. Out of scope (slice 1)

- capability, vitality-beyond-readiness and information causes, and CapabilityEstimate reuse;
- soft penalties;
- corridor and route-segment identity (G3 / D6);
- perception-based triggers;
- learned delays;
- shared or told memory.

## 15. Delivery shape

One standard ticket on #996's branch:
- (a) TargetPurpose on navigation and every writer: gate signature, writes, static check;
- (b) producer evidence;
- (c) the memory model, update, apply, canonical form, checkpoint and presenter;
- (d) the consume step: review, file, clear; ACCESS filing dropped;
- (e) the gate reads experiences, with `_blocker_hit` removed;
- (f) the project end;
- (g) data, docs, divergence, parity;
- (h) the own-job kit at a sha;
- (i) the runs.
Tests go with each commit.
