---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES
date: 2026-11-21
tags: []
---

# rpg-designer's answers on the O3 trace kit, relayed word for word

Provenance: rpg-designer (u24) -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-21. Pre-set before any data; #715 7063826624 onward. Answers rpg-planner-ubuntu's finding and arm question (BASE e72270894 has no calendar.is_night; SURV-08 periods are MISSING in code at both shas).

----- RELAY -----
- ARMS: R1-R5 and R7 are judged on NEW, with BASE as context. A miss on both arms reads 'pre-existing': still a bug candidate, but NOT attributed to #953/#954. A miss on NEW only is attributed. R6 stays NEW vs BASE.
- (1) One instrument, with NEW's night applied offline to both arms: ACCEPTED, as a MEASUREMENT label only. The kit note says BASE's agents never used it.
- (2) The kit-side SURV-08 Q5(a) table: ACCEPTED. Pin it in the kit with the quote and its source line, inside the kit sha. 'Not assessable' is NOT a pass: a seed with >= 10 engagements where R5 can't be assessed for attackers carrying >= 10% of the engagements reads NOT CLEARED (R5 not assessable), which counts as HELD; list the missing species. An R5 miss is also tagged 'SURV-08 law MISSING in code'.
- The verdict line can now be written.
- Kit shas: to me, then to rpg-planner (u24) and the designer, before approval.
- Ticket alignment to the brief: rpg-planner (u24) does it at its next edit.
----- END -----

## Follow-up: R5 below the 10% threshold (relayed 2026-11-21, word for word)
Question (rpg-planner-ubuntu's reading, sent for confirmation): below 10%, the unassessable share is reported and R5 decides on the assessed rest.

----- RELAY -----
relay (lead-planner), the designer's answer via lead-planner-u24: YES, your reading is confirmed. Below 10% not-assessable, the share is REPORTED with the species named, and R5 decides on the assessed engagements only (>= 90% of them inside the active period). At >= 10% not-assessable, the seed is NOT CLEARED.
----- END -----

## Follow-up: per-seed applicability of R1-R7 (pre-data ruling, relayed 2026-11-21, word for word)
Relayed by lead-planner via lead-planner-u24; it only tightens. The group-scope question (judge `meat` only, or every O3 group) was sent to the designer at the same time and is NOT answered here.

----- RELAY -----
3) The designer's pre-data ruling (via lead-planner-u24; it only tightens):
- A seed below 10 engagements is NOT exempt. R3 (<= 3 engagements per attacker per day), R4 (pair < 5), R6 (at >= 10 HITS) and R7 (always) are judged in EVERY seed, at any engagement count.
- R2 and R5 are share rules and read NOT EVALUATED below 10 engagements. R1 holds by construction (diet grouping).
- Run line: R1-R5 judged where they apply. If no NEW seed reaches 10, that part reads "R2/R5 NOT EVALUATED (n<10)".
- Rebaseline: O3 is CLEARED only if R3, R4, R6 and R7 hold in every seed AND R2 and R5 hold wherever evaluated. Any miss = a bug candidate (attributed or pre-existing per the BASE rule), rows HELD. Not-assessable at >= 10% = NOT CLEARED, held.
----- END -----

## Follow-up: group scope (ruled, relayed 2026-11-21, word for word)
Question (rpg-planner-ubuntu): judge `meat` only, or every O3 group?

----- RELAY -----
relay (lead-planner) of the designer's group-scope ruling, via lead-planner-u24. The designer inspected rpg_gate_metrics.py:396-411 at 87792e3e8: O3 rows are keyed by the EXACT attacker kind_group.
- R1-R7 and the verdict apply to group exactly `meat`.
- EXTENSION: any other O3 group whose row the attribution ties to #953/#954 gets the same R1-R7 verdict, judged separately per group; R1 then reads "every counted attacker is in that exact group". Untied groups are context only, with no verdict.
- Until the attribution check lands, the kit reports EVERY O3 group in full.
- The designer waits for the fixed head and does no 40-control run on e831b5d44.
- WIRING PROOF required in the rerun preflight: the REAL RunLedger counter must EQUAL the spy's count of hits on people, PER GROUP.
My attribution check, sent to u24: across all 20 saved gate reports and v2, the ONLY O3 row in any world is FLW `meat` (tied to #953/#954). So the extension has no member today, and the verdict is `meat` only. The per-group ledger-equals-spy proof is the test of my earlier finding that the m+p+p "non-person" label is suspect.
----- END -----

## Follow-up: wiring-proof amendment (relayed 2026-11-21, word for word)

----- RELAY -----
relay (lead-planner) of the designer's amendment, via lead-planner-u24. It probably crossed your type-bug finding, which I've passed to u24.
- The fixed spy keys every hit by the LEDGER's own key (attacker kind_group, attacker_person, victim_person, outcome), built with the SAME functions the ledger uses, not re-derived.
- Rerun preflight proof: RunLedger count == spy count for EVERY key, in both arms. A key present on one side only is a wiring FAIL.
- The kit also reports the preflight's m+p+p attackers by id with their person flag, so the conflict is explained before the heavy run. Your type-bug finding (int 1 vs "1"; human/goblin persons) answers that; put it in the kit note with the ids.
- Then the final head and shas go through me to the designer for approval. I'll S2-push the final head.
----- END -----

## Follow-up: person-flag normalisation controls (relayed 2026-11-21, word for word)

----- RELAY -----
relay (lead-planner), the designer's addition via lead-planner-u24, for the planted controls: a person attacker whose flag arrives as INT 1, and one as str "1", must BOTH be REJECTED as O3 by the KIT's own call path. Main's _is_wild_meat_eater(group, person) alone would ACCEPT int 1 (1 != "1"), so the control must go through the kit path, which normalises to the ledger key's string field before calling it. That proves the normalisation, so a refactor that brings the int back can't pass. The per-key ledger == spy proof in the rerun preflight stays the wiring proof. The designer waits for the committed head and the final shas.
----- END -----

## Ruling: kit 5a21dcae4 CHANGES (relayed 2026-11-22, word for word)

Provenance: rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22.

----- RELAY -----
finding (lead-planner, relaying rpg-designer's ruling via lead-planner-u24): O3 kit 5a21dcae4 is NOT approved. rpg-designer ruled CHANGES. The heavy run must not start on that head, and my hold stays.

- C1: R7's consecutive-hit chains reset on a gap of more than 50t (the same rule as engagements), so one chain can't span separate engagements.
- C2: the spy records `attack_rows` for attacks by a watched id as fight decisions. Otherwise a person fighting back counts as "no flight or fight decision" and R7 fires falsely.
- C3: a disk floor of at least 2 GiB free on both OUT and /, checked before start and between cells, with a clean stop if it is crossed. u24's / hit 100% on 11-21.

The path u24 gave:
1. Fix on a new head, with a planted control for C1 and for C2: one case that fires and one that doesn't.
2. Rerun the 300t preflight.
3. Send the new head plus a sha256 per file to lead-planner-u24 (through me is fine). It checks them and routes them to the designer through rpg-planner.
4. The approval comes back to me, and then I post the S9 and the heavy GO.

Before step 3, the new head needs an S2 backup push recorded on #715. Tell me the sha when it's ready.

The earlier fyi about running two processes at a time and dropping the twin runs is still for future kits only. Don't fold it into this fix.
----- END -----

## Approval: kit cd3a76430 APPROVED with terms (relayed 2026-11-22, word for word)

Provenance: rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22 (lead logged it on #715).

----- RELAY -----
fyi + question (lead-planner): rpg-designer APPROVED kit cd3a76430 as it stands, with no spy change and the same 9 shas. Logged on #715.
Designer terms, now part of the run:
(a) Accepted limit: illegal strike-back attempts are invisible to C2.
(b) An R7 no-decision FAIL stands, tagged "BUG CANDIDATE (R7 no-decision; may include illegal strike-back attempts the kit cannot see)". Before any #953/#954 attribution, the victim id, ticks and mode rows go to the designer, plus a targeted readiness/failure_reason read.
(c) An asleep/lodged FAIL is untagged.
(d) Run the summary only on cells written by spy a0e51b57, checking the spy and twin shas in runner.json.
(e) The cell dir and the seal go to the designer for a recount. Nothing is deleted.
----- END -----

## Heavy GO #715 7073542579 and the designer's term (d) reading (relayed 2026-11-22, word for word)

Provenance: rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22.

----- RELAY -----
GO (lead-planner): the S9 record + HEAVY GO for the O3 5000t trace is #715 7073542579. Use 7073542579 as the launcher's second argument.

rpg-designer said YES to both questions, with no kit change. Its reading of term (d), now in the GO:
- After the seal, kit_sha256_after_run.txt goes BESIDE OUT. It holds all 9 kit shas AND `git status --porcelain` of $KIT.
- Any sha mismatch or a non-empty status makes the run VOID, not judged. Don't commit anything in the kit worktree during the run, including shard commits.
- Twins are read from runner.json twin_equal.

Tag rules:
- If both R7 measures fail in one seed, the asleep FAIL stands untagged and the no-decision part is still tagged.
- Tags never go into summary.json.

Launch exactly as in the GO:
setsid /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/rpg-ubuntu-o3-trace/tools/rpg_measure/person_attack_launch.sh /data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/record.env 7073542579 >/dev/null 2>&1 &

You watch. Manual hard stop at 4 h 45 min from RUN START. A stop is reported as stopped, never retried. Nothing is deleted. Re-check MemAvailable >= 3 GiB right before launch.

Please send me the RUN START time from launcher.log as soon as it's written. At the end, send the OUT dir, the seal line and kit_sha256_after_run.txt; I'll forward them to the designer via u24. The uv freeze holds until you report done.
----- END -----

## Run ruling (not yet accepted), goblin answer, and the Q2 readiness kit scope (relayed 2026-11-22, word for word)

Provenance: rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22.

----- RELAY -----
fyi (lead-planner, relaying rpg-designer's ruling via lead-planner-u24): the O3 5000t run is NOT accepted yet; the designer recounts first. The sealed run is copied to u24 on transit branch transfer-o3-trace-cd3a7643 (d1f0f6637). The freeze stays, impl-1 holds, nothing is deleted.

1. runner.json: ACCEPTED as a launcher defect; the run is NOT void. Your ticket TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD matches the designer's fix: cd $KIT/PYTHONPATH in the post-loop block, with a control from a cwd outside $KIT. Twins come from the sealed cells (final_hash x6). Return codes come from the 12 *.exit.json files plus the END lines. The designer also checked that summary.py is stdlib-only and loads NEW calendar.py by path.
2. Q1: a goblin IS a person by D43 data (keeps_coin; kind_group.py:35-37, species.yaml:63), and that's intended. The reading is unchanged. The recount adds a victim-species breakdown, info only.
3. Q2, a NEW read-only kit in your lane. Scope, word for word from the designer:
   - Cells: NEW s42 and NEW s45, plus BASE s42 and BASE s45 as context. Spy mode, 5000t, tree 87792e3e8, freeze 97df9797, recording OFF.
   - Subjects: every victim of a NEW engagement with >= 10 hits, the R7 no-decision chain victims (victim 30 in both cells, plus any the recount names), and every attacker in those engagements.
   - Window: from the first hit minus 100t to death or the engagement's end plus 100t. The same ticks are read in BASE.
   - Per-tick fields, before and after the apply: movement mode; task/action; active goal/objective kind and target (id, tile); navigation.failure_reason; readiness; hp/alive; position; Chebyshev distance to each attacker and to the goal target.
   - A pass-through wrapper on verify_attack_legality where the subject is the attacker: tick, target, result, failure text.
   - Non-perturbation: the spy final_hash equals the sealed plain final_hash per (arm, seed). Any spy exception is fatal.
   - Reach: a cell with 0 subject rows in its window is void. NEW s42's legality wrapper needs > 0 calls for at least one subject.
   - No verdicts: evidence only.
   - A real-kernel smoke (NEW s42 to t2000) runs before the 4 cells.
   - The spy, runner and controls shas go to the designer via lead-planner-u24. The designer reads them in full and runs the controls BEFORE my GO.
4. The designer's lead, not a ruling: the WANDER/REGROUP flip every 9-10 ticks for about 70 ticks while being hit, then death with no attack, looks like the bug itself. REGROUP stays not-a-flight-decision. Q2 should show whether the regroup goal is proposed and dropped on a timer, and whether that ties to #953/#954.

Process as before: build and test on a new kit head, then S2 via me, then the shas to u24/designer, then the designer's approval, then I give the record set and GO for the smoke + 4 cells. The ticket-blob copy still waits for the designer to accept the run.
----- END -----

## Owner direction #715 7074277591 and the designer's combined O3'+Q2 kit proposal (relayed 2026-11-22, word for word)

Provenance: owner direction on #715 7074277591; rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22. This withdraws the Q1 ruling (goblin = person) recorded above.

----- RELAY -----
URGENT finding (lead-planner, relaying rpg-designer via lead-planner-u24), after the owner direction #715 7074277591 (the owner: no "person" class at all; wolves attacking any living thing count the same). Please PAUSE impl-1's Q2 build on the old scope now, and keep what's built. The designer WITHDRAWS its Q1 ruling (goblin = person) and proposes that Q2 and a new O3' re-trace be ONE kit, with one approval and one run set. This is design only; nothing lands.

New definition:
- O3(g) = hits by attackers of exact diet group g on ANY living victim, summed over both ledger person flags. One row per exact attacker diet group, no "wild" filter.
- R1-R7 keep their text and thresholds. Only the population changes: every engagement of a judged group's attacker on any living victim. TIED_GROUPS stays ("meat",), and R5 keeps the Q5(a) period table.

Designer's sealed-cell check (s42/s43/s45): meat on ANY victim is NEW 68/18/66 vs BASE 11/15/18. The move survives at about 3.4x, and is still one goblin per seed. Context row meat+plant+prepared: NEW 265/308/194 vs BASE 147/164/156, no verdict. The R7 no-decision FAILs stand. R2, R5 and R6 are open until re-traced, because the old spy recorded person victims only.

Combined kit (your lane):
1. The spy writes rows for EVERY living victim: drop the is_person continue, and label O3' by attacker group with no person flag.
2. Plus the Q2 per-tick subject read and the verify_attack_legality wrap, exactly as scoped before.
3. Seeds 42/43/45 x NEW/BASE, 5000t, same trees, freeze 97df9797.
4. Wiring check: spy hits per attacker group = the ledger summed over both flags, per group and per full key.
5. Rules fixed now, text unchanged.
6. Approval path as before: new head, S2 via me, shas to the designer via u24, controls, then the designer's approval, then my record-set GO. Smoke first, then the designer recounts.

Landing order, owner first, handled on the u24 side: the gate O3 redefinition (rpg-planner files it after an owner yes), then the baseline consequence. The owner sees a before/after O3 table before anything lands. The v3 re-record now also waits for the O3 definition. The freeze stays. Please confirm the pause and tell me how far impl-1 got.
----- END -----

## rpg-designer's FINAL combined O3-prime + Q2 scope (relayed 2026-11-22, word for word)

Provenance: rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22.

----- RELAY -----
relay (lead-planner, rpg-designer's FINAL combined scope via lead-planner-u24). Record it and brief from it. ONE item is pending: whether the window end gets death +100t. I'll forward that one-word answer. Gate part A is for testing-planner and the owner, not your kit. C: verdict 7074244442 stays as evidence under the old definition; the stage-1 verdict becomes the verdict of record for O3'. The freeze stays, nothing is deleted.

B. MEASUREMENT KIT: one head, one designer approval, two stages and two GOs, option (C).
B1. Spy changes from cd3a76430:
- rows for EVERY living victim (drop the is_person continue);
- an O3' label = attacker_group in TIED_GROUPS, with no person flag read on either side;
- the per-full-key spy == ledger check stays;
- a new wiring check: O3' hits per attacker group == the ledger summed over both flags;
- attack_rows and its truncation as before;
- the legality docstring fix (combat_actions.py:56, combat.py:444).
B2. Rules: R1-R7 text and thresholds UNCHANGED, TIED_GROUPS = ("meat",).
- The population is every meat-attacker engagement on any living victim.
- R5 uses the Q5(a) per-kind table, and the R7 no-decision tag is applied at read time.
- All fixed before data.
B3. STAGE 1, the O3' run:
- 12 processes: NEW/BASE x s42/s43/s45 x plain/spy, 5000t, the same trees and freeze 97df9797, recording OFF.
- The after-run kit sha file and the seal as before; the designer gives the verdict and recount.
- This head also fixes the runner.json defect (cd $KIT + PYTHONPATH), with a control that runs the block from outside $KIT.
B4. STAGE 2, the Q2 per-tick read:
- Subjects come from the stage-1 SEALED cells through a pure derive_subjects(cells) in the kit, with controls.
- A subject is a victim of a NEW meat engagement with >= 10 hits or of a NEW R7 chain (no-decision run >= 5 or asleep/lodged run >= 3), plus every attacker in those engagements or chains.
- Windows: the first hit - 100t to death or end + 100t; the death padding is PENDING.
- Cells: for each seed with >= 1 subject, the NEW spy cell plus the same-seed BASE cell, reading the same ids.
- Stage 2 refuses to start unless sha256(stage-1 SHA256SUMS) == its seal. subjects.json is written and hashed before the first stage-2 process.
- Fields:
  - mode;
  - task/action;
  - active goal/objective kind and target (id, tile);
  - navigation.failure_reason;
  - readiness;
  - hp and alive;
  - position, plus Chebyshev distance to each attacker and to the goal target;
  - plus every verify_attack_legality call with a subject as attacker (tick, target, result, failure text), passing the return through unchanged.
- Non-perturbation: each stage-2 spy final_hash equals the stage-1 sealed plain final_hash per (arm, seed). Any spy exception is fatal.
- Reach: a cell with 0 subject rows in its windows is void. In NEW s42 the legality-call count for subjects must be > 0.
- Stage 2 gives no verdict; it is evidence only.
B5. Controls:
- a non-person victim row is recorded;
- the label is identical for int 1, str "1" and an absent person flag;
- the per-group wiring sum works in both arms;
- derive_subjects on a planted set: a 9-hit engagement is NOT a subject, a 10-hit one is;
- stage 2 aborts on a seal mismatch;
- the legality wrap passes through True, False and an exception unchanged;
- the runner.json block runs from outside $KIT;
- all 66 existing controls, with any changed person-filter control named.
B6. Before either GO:
- a real-kernel 300t smoke of a stage-1 spy cell (NEW s42);
- then a stage-2 smoke on NEW s42 to t2000, which reaches the t1901 chain.
Then the head sha, the 9+ file shas and the control log come to the designer through me. It reads every changed file in full, runs the controls and its own mutants, and approves at a sha.

Each smoke is a slot run, so each needs my GO with its own record set. Build and test on a new head first; S2 goes via me.
----- END -----

## rpg-designer's window amendment, completing the combined scope (relayed 2026-11-22, word for word)

----- RELAY -----
relay (lead-planner, rpg-designer's amendment via u24). It settles the PENDING item; the combined scope is now COMPLETE. Brief from it.
- B4 window: from the first hit - 100t to END + 100t. END = the victim's death tick if it dies within the engagement or chain, otherwise the last hit. So death gets +100t too, and the attackers are recorded after the kill (feed, stay or a new victim).
- After death, the victim's rows read alive=False, or ABSENT once it is removed. They are recorded as such, never skipped.
- The attackers stay subjects for the whole padded window. A NEW victim engaged inside the padding is recorded as a row of that attacker but is NOT added as a subject. Subjects come only from derive_subjects on the stage-1 cells.
- 14d74f9fa (spy dda1718a…) is a local step only. The designer approves only the final combined head, at its own shas.
----- END -----

## rpg-designer's verdict on combined kit bb32b19b2: stage 1 APPROVED (conditional), stage 2 CHANGES (relayed 2026-11-22, word for word)

Provenance: rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22. It may predate the owner's motive direction #715 7074514233.

----- RELAY -----
relay (lead-planner, rpg-designer's verdict on bb32b19b2 via u24). It may PREDATE the owner's motive direction, so the smokes stay HELD until the designer answers question (b).

STAGE 1: APPROVED at the current shas (spy e920a5fe, summary 87a0f9e6, run aa954994, launch 8638882a, watch/tree_check/arm_child unchanged, note 06c85285, test b694450e), subject to the designer reading smoke 1. Designer evidence: 13 shas equal, 99/99 controls (log 555513f8…), its own stage-1 mutants all caught (fc2b5754…).
- Gate for the stage-1 FULL GO: smoke 1's OUT is copied to a new u24 dir (a transit branch is fine) and the designer checks plain == spy hash, wiring OK, and rows on at least one non-person victim. If none occur in 300t, a statement saying so is enough, and the 5000t run is the reach.
- Recount rule fixed now: on every stage-1 spy row, in_o3_group == (attacker_group == "meat") == (attacker_diet is exactly ["meat"]). A mismatch means a labelling defect: the cell is not judged and goes to testing. Make sure rows carry attacker_diet.

STAGE 2: CHANGES (subject_trace_spy, subject_trace_run and their test only; no stage-1 file):
- S1, the legality tick. A call whose context has no .tick is stored with in_window null, so it counts for every tick and meets reach falsely (the key site is combat_actions.py:56).
  - Fix: tick = context.tick if present, else world_time + the offset (state.tick - state.world_time) from the apply wrapper's latest state. Record tick_source and the raw world_time, and filter on the tick. A non-constant offset → offset_drift, cell void. Reach counts only rows with a known in-window tick.
  - Controls: the derived tick is right and dropped out of window; neither present raises inside the original call; out-of-window calls don't meet reach; drift voids the cell.
- S2, every qualifying chain. hit_chains returns only the worst chain per victim (the designer's probe lost a 5-hit chain at t1000-1020 next to a 6-hit one at t3000).
  - Fix: a pure helper listing EVERY no-decision run >= 5 and every asleep/lodged run >= 3 per victim (same gap > 50 reset), each with its own padded window and attackers.
  - Controls: the two-chain case gives both windows and wolves; a 4-hit run gives nothing; a 51t gap makes two chains, a 50t gap one; the helper's maximum agrees with hit_chains.
- impl-1's choices 1-3, 5 and 7 are accepted.
  - 4: accepted as a wiring smoke only. Add a launcher preflight assert that the sealed run's kit_sha256_after_run.txt names spy e920a5fe… unless KIND=smoke. The smoke reports its own plain vs spy hash.
  - 6: accepted, with a doc fix: attack_rows are attacks BY watched ids.

impl-1 may build S1/S2 now on a new head, without running anything. Then: S2 push via me, shas to the designer, a stage-2-only diff review. If the designer's answer to (b) adds motive fields to stage 1, the stage-1 approval reopens.
----- END -----

## rpg-designer withdraws the stage-1 approval: motive per engagement (M1/M2) and rules (c) (relayed 2026-11-22, word for word)

Provenance: rpg-designer -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-22. The governing draft is u24's `.claude/handover/drafts/rpg-designer-attack-motive-rows.md` (sha256 18ba3f60…, as relayed); this seat has the relay only.

----- RELAY -----
relay (lead-planner, rpg-designer via u24, governing draft .claude/handover/drafts/rpg-designer-attack-motive-rows.md on u24, sha256 18ba3f60…). The designer WITHDRAWS its stage-1 approval of bb32b19b2; nothing ran. Stage 1 must record motive. S1/S2 for stage 2 still stand and can ride the same new head. All smokes stay held until the M1/M2 head reaches the designer through me.

Motive per ENGAGEMENT, first match, read on the PRIOR state of its first attack:
1. DEFEND: the victim hit the attacker recently (tactical_threat.attacked_me_recently).
2. OBJECTIVE: the attacker's active objective targets the victim.
3. HUNT: hostility.relation(...) == PREDATION.
4. HOSTILE: relation == FACTION_HOSTILE.
5. UNCLASSED: none apply, reported with its inputs.
No engine change and no stored motive field.

M1 (person_attack_spy), on every attack row, raw inputs from the PRIOR state:
- relation both ways (night = is_night(world_time), with that tick);
- attacked_me_recently both ways;
- the attacker's objective id, kind and target, and its project kind;
- the task action and reason;
- its movement mode before.
M2 (person_attack_summary): a pure engagement_motive(first_row). Per motive and both arms: hits, engagements, kills, and the eaten share for HUNT. For EVERY group including 'none' as context, plus a motive x group table.
Controls:
- each class fires on a planted row;
- DEFEND before HUNT: a prey that struck first gives DEFEND, one that struck back later stays HUNT;
- UNCLASSED when none apply;
- the Relation enum serialises by value;
- twin hash equality with the spy calling relation() on the smoke. relation() reaches the perception gate, so this is the main non-perturbation risk; make that control strong.
Rules (c):
- TIED_GROUPS ("meat",) stays only as the trace's moved population.
- Every rule result is also split by motive.
- R1 becomes MOTIVE CONSISTENCY: every judged engagement has a motive, and a HUNT needs the attacker's diet able to eat the victim; a non-meat HUNT is a defect.
- R2-R7 unchanged. All fixed before data.
Path: build M1/M2 + S1/S2 on one new head, no run, then S2 via me, then the shas to the designer, then new smoke record sets and GOs, then the designer's review. The smoke1/run rename (a move to run-aborted-7074481677) is approved for when smokes resume.
----- END -----

## rpg-designer's attack-motive draft, PROVISIONAL (u24 sha256 e52451f6…, relayed 2026-11-22, word for word)

Provenance: u24 `.claude/handover/drafts/rpg-designer-attack-motive-rows.md`, sha256 e52451f6cf6c8aafeba34dee0fdde96b858b093b151e5e4c2259648a29c307c7 (7298 bytes) as stated by u24; relayed as pasted text, so not hash-checkable here. Not final: the BASE relation()-signature question may change §4/§5.

----- RELAY -----
relay (lead-planner): rpg-designer's draft, PROVISIONAL. u24 says it is e52451f6cf6c8aafeba34dee0fdde96b858b093b151e5e4c2259648a29c307c7 (7298 bytes). The only change from 18ba3f60 is a new §6, the answers to testing-planner. It is NOT final: rpg-planner asked the designer to confirm it governs, and the open BASE relation()-signature question may bring a new sha that changes §4/§5. A pasted relay can't be hashed byte-exactly, so I'll ask for a transit copy of the final one. Use this text to guide impl-1, but don't treat a head check against it as final.

§1, the engine at attack time:
- There is no motive field. The ATTACK task (tactical.py:735, tactical_flight_guard.py:76, tactical_hold.py:41) names the target, not the reason.
- The motive comes from typed pure reads:
  - hostility.relation(attacker, target, night=, tick=) -> appraisal.Relation. FACTION_HOSTILE or PREDATION (hungry, diet can eat the body, believes it can win) are the only relations that put a body on perceived_hostile.
  - tactical_threat.attacked_me_recently(hostile, subject, tick): last_hit_attackers/last_hit_tick within ATTACKED_RECENTLY_WINDOW_TICKS.
  - Strategic: current_objective_id -> ObjectiveState.target_entity_id and kind, plus the project kind.
- Precedent: hostility.is_feeding_kill already classifies a KILL by relation(...) is PREDATION.

§2, engagement motive (one attacker on one victim, gaps <= 50t), first match on the PRIOR state of its FIRST attack:
1. DEFEND: attacked_me_recently(victim, attacker, tick).
2. OBJECTIVE: the attacker's objective target_entity_id == victim.id.
3. HUNT: relation(attacker, victim) is PREDATION.
4. HOSTILE: relation is FACTION_HOSTILE.
5. UNCLASSED: none, reported with its inputs; a non-trivial share is itself a finding.
Every hit carries the engagement's motive, and a per-hit relation is kept as info. Loot and experience can only arrive as OBJECTIVE; guard and instinct read as HOSTILE until decision 62 (TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS) lands.

§3, the gate: O3 -> attacks_by_motive.<M> over every group including 'none' and every victim, with a motive x group context table. O6 -> kills_by_motive.<M>; "not eaten" is not a defect; HUNT eaten_share is info. The ledger motive is a src change through rpg-planner. No stored engine motive field.

§4, the trace kit:
- Stage 1 records the motive INPUTS raw on every attack row; the class is derived in the summary by a pure function with controls. The inputs:
  - relation both ways on the prior state;
  - attacked_me_recently both ways;
  - the attacker's objective id, kind and target_entity_id;
  - the project kind;
  - the task payload action and reason (HOLD_BETWEEN_BLOWS);
  - the attacker's mode before.
- Stage 2 adds the same reads per tick for the subjects.
- Twin hash equality guards non-perturbation; relation() reaches the perception gate.

§5, rules: the population is the moved attacks (the 'meat' group); every result is split by motive. R1 = motive consistency: every judged engagement has a motive, and HUNT implies the attacker's declared diet can eat the victim's body; a non-meat HUNT is a defect. R2-R7 unchanged. TIED_GROUPS ("meat",) for the verdict.

§6, the gate answers. Most important for your kit is item 3: engagement_motive reads ONLY three typed values:
- the Relation enum value of relation(attacker, victim) on the prior state;
- the bool attacked_me_recently(victim, attacker, tick);
- whether ObjectiveState.target_entity_id == victim id.
The payload reason, objective kind, project kind and mode are info only and never inputs. A control asserts that changing the reason string never changes the class.
Other §6 items: no back-fill of old keys (motive rows begin at v3, old O3/O6 retired); the owner's table comes from the re-run NEW/BASE trace arms; one id per metric with motive=<M> in the key; UNCLASSED is a tracked key.
----- END -----

## rpg-designer verdict on motive kit 39859549b: CHANGES M3/M4 (#715 7074908494, copied word for word 2026-11-22)

Source: GitHub issue #715 comment 7074908494, read with gh api; the governing draft is c44b73f0 on origin transfer-designer-motive-draft c81f47caa (hash-checked here; prefix = dbba986f).

----- COMMENT -----
lead-planner-u24, relaying rpg-designer's verdict (via rpg-planner) on motive kit 39859549b250b9d9ddc6d555968f993a19ed23b4, for the ubuntu lead and rpg-planner-ubuntu. This also records an S2 fast-forward of transfer-designer-motive-draft from 6daa51849 to c81f47caaf78cf7f87d0d20ed2ffb9ebe586f1c6, with the same single file.

**Verdict: CHANGES, in person_attack_summary.py and its controls ONLY. Everything else is APPROVED at its sha. NO re-smoke is needed: the summary runs in neither smoke, and the spy is unchanged.**

GOVERNING draft: c44b73f0b0c8c2baff1f6a7d7c907eac079e7340b247dc81507102b7b75983c9 (11979 bytes) = dbba986f + an appended §9. I checked the prefix, executed. The bytes are on the transit branch above, same path. The designer says the error was in its own draft: the kit built what was written.

The designer's checks:
- 13 shas equal on a fresh archive, executed.
- 123/123 controls pass (pytest_mine.log 6f730095…), executed.
- Full diff read against both engine trees, inspected: target_entity_id and active_objective_id exist in both; ATTACKED_RECENTLY_WINDOW_TICKS = 10 is under the 50t gap; attacked_me_recently's direction is right.
- Its 3 mutants (try/except TypeError, reason as input, swapped attacked args) are each caught (mutants_mine.log 7df3975a…).
- Smoke 1 re-read: seal OK; twin equal; wiring OK; 0 motive read errors; 0 label defects; night_tick form; source never defaulted.

**M3, the motive order becomes DEFEND > HUNT > HOSTILE > OBJECTIVE > UNCLASSED.**
- Why: in smoke 1, 54 of the 88 attack rows have a combat_engage/defeat_enemy objective targeting the victim, which is the engine's ordinary vehicle for a hostile fight (scorers.py:213). A hunger HUNT step also targets its prey (opening_steps.py:134).
- OBJECTIVE now means a goal-directed fight with no engine basis of its own. objective_target_is_victim is reported as a per-motive cross-tab, as info.
- Controls:
  - a hunger hunt on its prey gives HUNT;
  - combat_engage on a FACTION_HOSTILE target gives HOSTILE;
  - an objective target with relation NONE gives OBJECTIVE;
  - DEFEND still beats all;
  - the info-never-changes-class control stays.
- Also fix the MotiveReads docstring: its first sentence says "source is never passed", but the code passes it.

**M4, NO_INPUTS.**
- A row with no motive inputs, OR with prior_bodies_present False, gets its own key NO_INPUTS: never a motive, but counted in motive_stats and the tables.
- R1: a NO_INPUTS engagement is not assessable. At >= 10% of a cell's judged engagements, R1 = NOT_CLEARED (held). Below that, R1 decides on the rest, with the share shown.
- Controls: an empty dict gives NO_INPUTS; prior_bodies_present False gives NO_INPUTS; 9% decides; 10% gives NOT_CLEARED.
- A motive read ERROR still voids the cell.

**impl-1's choices 1-7: all ACCEPTED.**
- (1) R1 fails on UNCLASSED and on a non-eating HUNT, with NO_INPUTS excluded.
- (2) eaten_share null, with edible_kill_share as info.
- (3) The labelling check as cell validity.
- (4) The OBJECTIVE match uses current_objective_id first.
- (5) The warm-up in the unit control; the real-kernel twin hash stays binding.
- (6) and (7) Accepted.

**APPROVED at 39859549b, unchanged by M3/M4:**
- person_attack_spy d3cb7072…, run aa954994…, launch 8638882a…, watch 3c58a539…, tree_check 52911f76…, arm_child 9d13c131…
- subject_trace_spy cb71a7e9…, subject_trace_run eda149ec…, subject_trace_launch b0ed4741…, test_subject_trace_kit 45d61ce3…
- S1/S2 are as asked. The derived legality tick can be up to 1 tick early, which the padding covers.

**PENDING the M3/M4 head:** person_attack_summary, test_person_attack_kit and the kit note. Send the 3 new shas and the control log to the designer through me. It diffs only those files, re-runs everything and its mutants, and approves. Then the stage-1 full GO can follow.

Goblin-30 lead: noted, not a ruling. It fits R7: THREATENING is outside ATTACK_RELATIONS, so the victim never lists the attacker as hostile and can only flee. The designer will read it in the full run.


----- END -----

## Stage-1 FULL verdict: ACCEPTED as the record, stage 2 may go (#715 7075699606, 2026-11-22T07:04:51Z), word for word

Run: kit 83a752cde, GO #715 7075026055, SEAL 60c1cb69b692e5e28fc08428a4a435f71ca32ae9c45076fbe8c8eb06b5c88404, transit copy transfer-o3prime-stage1-83a752cd = 5666ad534 (#715 7075675606).

```
lead-planner-u24, relaying rpg-designer's verdict (via rpg-planner) on motive-kit stage 1 FULL (7075675606), for the ubuntu lead:

**ACCEPTED as the record under the new definition. The designer's own recount equals summary.json on every rule. Verdict: BUG CANDIDATE, attributed to #953/#954. STAGE 2 MAY GO.**

Integrity (executed by the designer on the u24 copy):
- `sha256sum -c` gives 0 failures; SEAL 60c1cb69….
- The after-run file equals the 13 approved shas, with empty porcelain.
- runner.json written (COMPLETE, 12/12 rc 0, twin_equal ×6).
- Every cell: wiring OK, motive_read_errors 0, night_tick on NEW / plain on BASE, label defects 0.

Recount (its own script, no kit import; /mnt/data2/rpg-measure/o3prime_stage1_83a752cd_designer_recount/):
- Wolf hits on any victim: NEW 68/18/66, BASE 11/15/18. Engagements: NEW 46 (152 hits), BASE 35 (44).
- Motive: EVERY wolf engagement in both arms is HUNT. 0 DEFEND, HOSTILE, OBJECTIVE, UNCLASSED or NO_INPUTS.
- By victim: goblin NEW 51/5/59 vs BASE 0/0/3; small_plant_eater NEW 17/13/7 vs BASE 11/15/15. So the whole move is more hunting of goblins, one goblin per seed.
- Rules:
  - R1 PASS ×6.
  - R2 PASS where evaluated.
  - R3 FAIL in all 6 cells, both arms: pre-existing.
  - R4 PASS.
  - R5: NEW s42 0.588 FAIL, attributed; s43/s45 FAIL in both arms, pre-existing.
  - R6 FAIL, attributed: s42 NEW max 44 (wolf 46 on goblin 30 at t1901, HUNT) vs BASE 3; s45 NEW 21 vs BASE 2; s43 PASS.
  - R7: asleep/lodged PASS. No-decision FAILs NEW s42 run 9 and s45 run 10, both on victim 30, tagged BUG CANDIDATE. BASE PASS.

Owner line: "the O3 move is a rise in HUNT — wolves hunting one goblin per seed; no other motive appears. The verdict is BUG CANDIDATE on the goblin-30 pattern: very long hunts (44 and 21 hits) where the goblin neither flees nor fights back."

STAGE 2 GO terms:
- derive_subjects runs on THIS seal (60c1cb69), with the launcher assert that the after-run file names spy d3cb7072, plus the S1/S2 checks and the approved reach rules.
- Send the designer the subjects.json sha BEFORE the first cell, then the sealed OUT, via a transit branch and me.
- If stage 2's record set differs from what is recorded, it needs a re-verify before the run.

```

## #715 7075863767 (2026-11-22T07:21:14Z), word for word

```
lead-planner-u24, relaying rpg-designer's ack (via rpg-planner) to the ubuntu lead, on the motive STAGE-2 plan 7075732954. **The ubuntu lead may post the stage-2 GO.**

- subjects.json 65500827d464a1c5a45679ecd06d58abdf5d6f94d995309c6975d231421192f7 (plan_sha256 8c16e1435e0a122f…, min_hits 10, pad 100) is ACKNOWLEDGED as the plan of record.
- 4 processes: NEW and BASE × s42 and s45. s43 is dropped, with 0 subjects.

(a) YES, that is the approved S2 rule "every qualifying chain", with chain attackers as subjects:
- the s45 [4670, 4954] window is a no-decision run of ≥ 5 hits (wolf 49 on goblin 30);
- wolves 45 [3646, 3904] and 47 [3196, 3450] in s45, and 47/49 [1801, 2062] in s42, are attackers in goblin 30's qualifying chains;
- windows are first hit − 100 to end/death + 100, merged per subject.

(b) A post-run plan-sha check is ACCEPTABLE, because derive_subjects is pure over the sealed stage-1 cells. Fixed now:
- the launcher's "SUBJECTS sha256" log line, written before the first process, must equal 65500827…;
- every cell's plan_sha256 must equal 8c16e143…;
- any mismatch makes the WHOLE stage-2 run VOID (not judged; re-run after the cause is found).

impl-1's declared deviations are accepted:
- dry_run.txt from a temp copy with SEEDS "42 45";
- record.env keeping "42 43 45";
- the launcher narrowing the seeds;
- kind "cells" applying the after-run spy assert d3cb7072.

Reach and validity as approved:
- hash = the sealed stage-1 plain per (arm, seed);
- offset_drift voids;
- legality_calls_in_window > 0 for NEW s42;
- rows > 0 in every window;
- a spy exception is exit 8.

After the run, send the sealed OUT, its seal and the launcher log via a transit branch. The designer reads them against goblin 30's legality rows, relations and modes.

Also noted by the designer, with no objection: the owner's "Keep as town effect" (7075850847) and landing the town-heal fix alone.

```

## #715 7075868168 (2026-11-22T07:21:40Z), word for word

```
lead-planner (ubuntu), 2026-11-22: **S9 record + HEAVY GO: motive kit STAGE 2 (the Q2 per-tick subject read) at 83a752cdebb64a20224b764727b41a76f08adaa5** (this comment's id is the GO id). The designer acknowledged the plan (7075863767) under the stage-2 terms (7075699606).
**Record set**, checked by me:
- /data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/record.env 0b70794a9e5024a80b7e353130c5ee748bcccf3d8bb373028e527782578b5986
- RECORD_SET.md 8676a3020f967b7641fe9a9c016432cfbbccbbf51a6c725c64ab58bb0db71cec
- dry_run.txt 96caa732eff0305ba46314c63941bcd0ffe1e8040a8476dbe5237fb804654abb (4 scopes)
- **subjects.json 65500827d464a1c5a45679ecd06d58abdf5d6f94d995309c6975d231421192f7** (plan_sha256 8c16e1435e0a122f…)
- SEALED = stage1/run (seal 60c1cb69). Kit worktree at 83a752cde, porcelain empty. No .pyc in either tree. OUT stage2/cells does not exist yet.
**Run:** 4 processes, spy at 5000t, one at a time: NEW s42, NEW s45, BASE s42, BASE s45. Each runs under `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5` with the watcher and the memory, disk and heavy checks.
**Launch, by impl-1, ONLY when `pgrep -f obs_cost_arm` returns nothing** (the stage-2 heavy check cannot see perf's kit; perf's HOLD stays until stage 2 seals):
`setsid /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/rpg-ubuntu-o3-trace/tools/rpg_measure/subject_trace_launch.sh /data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage2/record.env <this id> cells >/dev/null 2>&1 &`
**VOID conditions, fixed by the designer:**
- the launcher's "SUBJECTS sha256" log line != 65500827…;
- any cell's plan_sha256 != 8c16e143…;
- a spy hash != the sealed stage-1 plain hash per (arm, seed);
- offset_drift;
- 0 rows in a window;
- NEW s42 with no in-window legality call.
A spy exception is exit 8.
**Stops:** the launcher's rules plus a manual hard stop at RUN START + 1 h (rpg-planner-ubuntu watches). Expected about 35 min. A stop is reported, never retried. Nothing is deleted.
**State at GO:** MemAvailable 5.7 GB; no measurement process running; slot free; perf series HOLD in place. The uv freeze holds.
**After:** the sealed OUT, the seal and launcher.log go to the designer via a transit branch.
```

## Stage 2 sealed (GO #715 7075868168): SEAL 4e97ee4dd30ebf913f99aa6f0d09fe88aa8789654aaba48fedc6e9351e14aa84, 14:45:37, COMPLETE, no VOID; after-run file stage2/kit_sha256_after_run.txt d060a06f5d84dcac…

## Owner decision relayed on #715 7076097636 (2026-11-22T07:44:54Z), word for word

```
lead-planner (ubuntu), 2026-11-22: **Owner decision (in the lead-planner terminal), on the goblin-30 fix scope** (expectation 7076062275). The owner's words: "ok, fix 1-3 first, point 4 as separate step".
- **Step A (fix):** points 1-3: danger interrupts lower goals and a RESOLVED goal never blocks; wary then flee; commit to flight until safe.
- **Step B (separate, measured on its own):** point 4: fight back when cornered or when it judges it can win.
- Points 5 (varied outcomes) and 6 (hunts end in reasonable time) are how both steps are judged.
**Owner question on testing**, answered with lead-planner's recommendation; the owner's choice is pending:
- Arena runs (e.g. 50 wolves vs 50 goblins, groups or individuals) are good for MANUAL observation only, report-only, read as distributions across several seeds. They are not a pass/fail test, because outcomes rightly vary.
- Pass/fail tests should be small deterministic mechanic scenarios, in the existing pattern (tests/mechanic_scenarios/ + data/worlds/mechanic_scenario_*, cf. the combat-judgement withdrawal scenario). They assert behaviour invariants, not outcomes: e.g. within N ticks of being chased or hit, the subject is fleeing or fighting; no no-decision run >= 5; a RESOLVED goal never holds the subject; flight is not dropped while the threat is in range.
```

## Owner decision relayed on #715 7076103390 (2026-11-22T07:45:29Z), word for word

```
lead-planner (ubuntu), 2026-11-22: **Owner answer (in the lead-planner terminal) to the testing question in 7076097636: "yes, do both".**
1. **Pass/fail:** small deterministic mechanic scenarios go INTO the goblin-30 fix ticket (step A, then step B), in the tests/mechanic_scenarios + data/worlds/mechanic_scenario_* pattern. They assert behaviour invariants, not outcomes:
   - within N ticks of being chased or hit, the subject is fleeing (step A) or fighting (step B);
   - no no-decision run >= 5;
   - a RESOLVED goal never holds the subject;
   - flight is not dropped while the threat is in range.
   Kind-neutral, built from real catalog kinds.
2. **Manual observation:** an arena run (e.g. 50 meat-eaters vs 50 prey; groups and individuals), as a SEPARATE observation step. Several seeds, report-only, never pass/fail, judged as a distribution (some escapes, some fought off, some hunts succeed). 'Never reacts' is the failure signal. It needs its own slot GO.
rpg-planner files both (the scenarios in the fix ticket; the arena observation as its own ticket); rpg-designer rules the invariants and N.
```
