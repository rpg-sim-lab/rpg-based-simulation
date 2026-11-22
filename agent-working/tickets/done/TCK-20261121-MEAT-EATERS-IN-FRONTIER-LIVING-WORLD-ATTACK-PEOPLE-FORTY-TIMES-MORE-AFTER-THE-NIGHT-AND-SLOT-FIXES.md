---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES
phase: done
date: 2026-11-21
tags: []
---

# TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES

## Title
Meat-eaters in frontier_living_world attack people about forty times more often (gate O3 0.6 -> 24.0 per seed) since the night fix (#953) and the suspended-project expiry (#954): trace who attacks, and decide intended vs a loop

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Owner ruling (via lead-planner-u24, 2026-11-21): attribute the big gate moves before testing re-records the baseline. Gate O3.attacks_on_people, FLW, meat group, per seed s42..s46: baseline v2 (run 43895014837, e72270894) 0,0,0,3,0 -> candidate (run 44906014216, 87792e3e8) 51,5,0,59,5 (floor 3).
The ubuntu lead's split, from saved gate-report JSONs with no reruns (#715 7063400557): #953 (divergence 2.209, night) alone gives +17.6; #954 (2.212, suspended-project expiry) alone gives +19.6; with #958, main a9dc29cdf reaches +36.4; #955 PERC-02a brings it to +23.4; #952 = 0; #983 = 0. SE about 12.3.
rpg-designer ruled it a BUG CANDIDATE until a trace clears it. The rule was pre-set before any data. Neither 2.209 nor 2.212 predicted an attack change, and the two-seed concentration looks like a repeating loop.
This ticket is the TRACE ticket: it owns any gate drift entries or carried rows for the #953/#954-tied rows while the trace runs (rpg-designer: every row tied to #953/#954, alone or combined, and every unplaced row, is held).

## Scope
1. A traced kernel run (own S9; brief at main-checkout .claude/handover/drafts/rpg-planner-o3-trace-brief.md, sha256 cd27e75a, accepted by rpg-designer as the pre-set rule of record): FLW s42 + s45, plus s43 as the REQUIRED quiet control, 5000t, NEW = 87792e3e8 vs BASE = e72270894, each on a fresh git archive tree, with plain twin hash equality.
2. Report (a) O3's unit (hits vs engagements; an engagement = one attacker on one victim with gaps <= 50t), (b) per attacker: kind/species/diet/engagements/hits/victims/day-night, (c) per pair: engagements and outcome, (d) inside the SURV-08 active period or not, (e) per hit: the victim's state (asleep / lodged / awake), its movement mode, and whether its next tactical decision is flight or fight. Also the gate's meat-group membership rule (file:line; inspected 2026-11-21: by diet, so group 'none' cannot be in it). O3 counts HITS (run_ledger._count_attacks), so the trace derives engagements itself.
3. Apply rpg-designer's pre-set rules R1-R7 (in the brief; R6 fight length vs BASE, R7 victim state). R1-R5 and R7 are judged on NEW, with BASE as context. A miss on NEW and BASE is "pre-existing" (still a bug candidate, not attributed to #953/#954); a miss on NEW only is attributed. R6 is NEW vs BASE. NEW's night definition is applied offline to both arms (a measurement label; BASE's agents never used it). Active periods come from a kit-side copy of SURV-08 Q5(a), pinned in the kit. "Not assessable" is NOT a pass: a seed where R5 can't be assessed for attackers carrying >= 10% of engagements reads NOT CLEARED and counts as held. An R5 miss is also tagged "SURV-08 law MISSING in code" (see TCK-20261109-M1-ACTIVITY-PERIOD-AND-HAZARD-TOLERANCE). INTENDED only if all rules hold in every seed where they apply; otherwise a BUG CANDIDATE with the attacker ids, then a fix ticket. A meat group holding a non-meat diet is a metric-grouping finding for testing-planner.
4. If intended: consequence lines in 2.209 and 2.212 plus parity notes (rpg-designer's docs), and the held rows re-record report-only.

## Out of Scope
- Changing the gate, its floors or any baseline row (testing-planner owns the re-record mechanics).
- The TOWN_SERVICE drops as a ruling question (held with the #954 rows; rpg-designer rules them separately if needed).

## Acceptance Criteria
1. The traced run's raw JSONs exist with hashes, the twins match, and rpg-designer recounted them.
2. Each seed (s42, s43, s45) has R1-R7 verdicts recorded, labelled executed, with the pre-existing / attributed / not-assessable labels per the rules in Scope 3, and s43 shows the rules don't fire on a normal seed.
3. The outcome is either a fix ticket filed (bug) or the 2.209/2.212 consequence lines landed (intended), and the held gate rows are released accordingly.

## Related Tickets
- TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT (#953)
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (#954)
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY (#955)
- TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON (F2; the loop family under R4)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.209, 2.212, 2.210
- docs/world_rules/life-body/survival-needs.md SURV-08
- tools/test_architecture/rpg_gate_known.yaml (drift entries need a TRACE ticket)

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES/:
- o3_trace_brief_relayed_2026-11-21.md (the brief) and rpg_designer_o3_kit_answers_2026-11-21.md (every designer and owner ruling, word for word, by #715 id);
- o3prime_motive_run_record_2026-11-22.md (the three runs: OUT paths, GO ids, seals, shas, after-run files, twin hashes, launcher lines);
- stage1_summary.jsonl, stage1_runner.jsonl, stage2_cell_validity.jsonl, stage2_runner.jsonl, stage2_subjects.jsonl (raw machine outputs, each with a source and sha256 header line);
- stage1_SHA256SUMS.md and stage2_SHA256SUMS.md (the seals, re-checkable against /data/vboxuser/o3-trace-runs).
Gate runs 43895014837, 44323101062, 44452967207, 44906014216; #715 7063400557.

## Related Code Areas
- src/observability/rpg_gate_metrics.py (O3 counting, meat grouping)
- src/core/calendar.py, src/systems/strategic_systems/intelligence.py (suspension expiry), src/engine/tactical.py (attack decisions)

## Assumptions / Open Questions
- Whether O3 counts hits or engagements (to be read in the kit).
- Whether the undead (FLW ids 39-44, group 'none') are inside the meat group.

## Durable state, lifecycle and clocks
None expected until the cause is known.

## Implementation Notes
The trace kit is READ-ONLY tooling (tools/rpg_measure/person_attack_*, subject_trace_*, arm_child.py; no src/ change and no test-expectation change). Stage 1 (`person_attack_spy`, `_summary`, `_run`, `_launch.sh`, `_watch.sh`, `_tree_check.py`) wraps the apply path in a record-only spy that drives the real RunLedger and checks spy == ledger per full key and per attacker group; it records a row for every attack on any victim with the motive inputs read on the PRIOR state (each arm calls its own engine's relation(), chosen by signature). Stage 2 (`subject_trace_spy`, `_run`, `_launch.sh`) derives subjects from the sealed stage-1 cells and records per-tick rows and a pass-through legality wrapper. Every run used frozen `git archive` trees (NEW 87792e3e8, BASE e72270894), the shared .venv (freeze 97df9797), recording OFF, one process per 3G scope on cores 4-5, a watcher, and a seal written last; each was approved by rpg-designer at its shas and run under a heavy GO (#715 7073542579 first O3 run, 7075026055 stage 1, 7075868168 stage 2). The kit's 13 files at head 83a752cde are listed with their sha256 in the after-run files inside the run record.
Process facts worth keeping: O3 was REDEFINED as O3' during the trace (owner #715 7074277591: there is no "person" class; a wolf attacking any living thing counts), so the first O3 run (SEAL 336487df) is kept as evidence under the old definition and stage 1 (SEAL 60c1cb69) is the record. Two launcher/loader defects were found and filed as follow-ups (below); the runner.json one is fixed in this kit.

## Test Summary
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest tests/tools/test_person_attack_kit.py tests/tools/test_subject_trace_kit.py -q -p no:cacheprovider --basetemp=/data/vboxuser/o3-trace-runs/pytest-pr/kit` -> 127 passed (92 + 35); the raw -v log of the same set at the approved head is /data/vboxuser/o3-trace-runs/o3prime-q2-v4-controls_raw.txt (sha256 084ddae6da11f4d50a44372b9dae746a747aef15080d8c688140f66cbdfd2a34). The controls were mutation-checked (each new or changed control fails when the check it guards is disabled; the one equivalent mutant, HUNT/HOSTILE order, is recorded in the kit note). The guard tests tests/tools/test_agent_working_paths_guard.py, test_monitoring_shard_paths.py and test_no_host_paths_in_launchers.py -> 24 passed. The whole tests/tools run was started and STOPPED by me at about 26% (about 26 minutes, no failure so far; the rest would take about 100 minutes), so it is NOT claimed as a pass. ruff check and ruff format --check on the changed tools/ and tests/ files FAIL as reported (327 findings; 8 files would be reformatted): the project adopts no formatter and its code-health scan covers src/ only, and the kit files are not edited here because their shas are approved. Real-kernel checks: two 300t/2000t smokes (twin hashes equal), then the three sealed runs.

## Files Changed
tools/rpg_measure/: person_attack_spy.py, person_attack_summary.py, person_attack_run.py, person_attack_launch.sh, person_attack_watch.sh, person_attack_tree_check.py, person_attack_kit_note.md, subject_trace_spy.py, subject_trace_run.py, subject_trace_launch.sh (all new; arm_child.py, which the kit also uses, is already on main and is unchanged by this PR).
tests/tools/: test_person_attack_kit.py, test_subject_trace_kit.py (new).
agent-working/stored_artifacts/TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES/: the brief, the designer-answers record, the run record, five .jsonl raw outputs, two SHA256SUMS .md files.
agent-working/tickets/: this ticket (todos/ -> done/), TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD (filed and closed here) and the still-open filing TCK-20261122-TRACE-KIT-CALENDAR-LOAD-WRITES-BYTECODE-INTO-A-FROZEN-TREE in todos/.
agent-working/agent-monitoring/ shards and docs/REGISTRY.yaml as the closure writes them.

## Completion Summary
Closed by the kit + evidence PR. The measurements are done and the verdicts are by id:
- Stage 1 (O3', motive per engagement) ACCEPTED AS THE RECORD by rpg-designer, #715 7075699606: its own recount equals summary.json on every rule; verdict BUG CANDIDATE attributed to #953/#954 (every wolf engagement in both arms is HUNT; the move is more hunting of goblins, one per seed; R6 FAIL attributed, s42 NEW 44 hits vs BASE 3, s45 21 vs 2; R7 no-decision FAIL on victim 30 in NEW s42 and s45).
- Stage 2 (per-tick subject trace) VALID, #715 7076173637. Two defects behind goblin 30: (1) a RESOLVED objective keeps pulling a fleeing subject back, attributed to #953/#954 and handed to step A, TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT; (2) a prey may not strike its predator between the predator's blows (hostility.py:109-118, refused FRIENDLY_FIRE_ILLEGAL), PRE-EXISTING in both arms: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS. Both were filed by rpg-planner (u24).
Gaps, stated as they are:
- AC2 is only PARTLY met: "s43 shows the rules don't fire on a normal seed" does not hold. On s43 R3 and R5 FAIL in both arms (pre-existing, not attributed); R6 and R7 do not fire there. R1-R7 are recorded per seed and labelled.
- O3 was redefined as O3' (owner #715 7074277591: no person class), so AC1-AC3 were met under the new definition; the first O3 run is kept as evidence under the old one.
- AC3's "the held gate rows are released" is NOT done here: releasing the held gate rows belongs to the gate re-record (rpg-planner u24 / testing), not to this PR. The fix tickets (the two above) are filed.
- Follow-ups: TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD is CLOSED in this same PR (its fix ships in the kit; all three acceptance criteria are met at 83a752cde, see that ticket), and TCK-20261122-TRACE-KIT-CALENDAR-LOAD-WRITES-BYTECODE-INTO-A-FROZEN-TREE stays OPEN in todos/ and is NOT fixed: load_is_night still loads the tree's calendar.py by path without guarding bytecode; the stray .pyc it wrote in the NEW tree was moved to quarantine-87792e3e8-pyc-20261122, not deleted.
- No staging plan.md / investigation.md / test_plan.md exist for this standard-tier ticket; none were invented.
