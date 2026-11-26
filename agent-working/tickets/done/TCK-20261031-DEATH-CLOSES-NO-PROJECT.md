---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-DEATH-CLOSES-NO-PROJECT
phase: done
date: 2026-10-31
tags: []
---

# TCK-20261031-DEATH-CLOSES-NO-PROJECT

## Title
Death closes no project: a dead entity keeps ACTIVE and SUSPENDED project records

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split from TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, Q4 (rpg-ubuntu-simq-anchor-bisect-impl d2ed6c8c2, agent-working/staging_artifacts/TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT/evidence/retention_trace/; 15 runs per commit, 3 worlds x s42-46, 2000t). a25619971: 368 dead, 229 with a current project, 240 with an ACTIVE project, 4 with an ACTIVE retreat. d914bace7: 379, 235, 253, 24. About 62-67% of the dead keep a live project at both commits: death closes nothing. Designer: a durable-state lifecycle gap, an ACTIVE record with a dead owner; the history is kept, the status is not.

Rule (designer): death ends every live project of the dead entity (ACTIVE and SUSPENDED) with a typed ended_by DEATH. Records are kept, not deleted.

## Scope
Phase 1 (counts and readers, read-only, before any fix shape):
1. Readers: does anything read a dead entity's live projects today (the :1610 orphan/make-current path, kind counts and capacity, read models and presenters, SimQ pillars, campaign detectors)? Each reader is a finding; any reader means main will not stay hash-identical.
2. Normalise "4 vs 24 dead with an ACTIVE retreat" by retreat projects started per commit (#769 starts more retreats). If the rise is not volume, report it as a finding to rpg-designer.
3. The 2 dead entities per commit whose last dead record is earlier than the last tick: explain.
Phase 2: fix shape after rpg-designer reads Phase 1.

## Out of Scope
- The retreat exit (TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT).
- Orphans from current_project_id clears (TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS) and SUSPENDED never resumed (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK).
- Deleting project records of the dead.

## Acceptance Criteria
(Phase 2, designer to confirm) On death every live project of the entity ends with a typed ended_by DEATH through the authoritative apply path; records are kept; a unit test covers ACTIVE and SUSPENDED; the dead-with-live-project count is 0 on the gate worlds; main hash-identical or every changed run attributed to a reader named in Phase 1; Bible 04 / parity ledger row for the project lifecycle on death.

## Related Tickets
- TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT; TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS; TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK; TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED

## Related Docs
- docs/mechanics/04_strategic_cognition.md; docs/core/entities.md (entity lifecycle)

## Related Stored Artifacts
- rpg-ubuntu-simq-anchor-bisect-impl d2ed6c8c2: evidence/retention_trace/README.md, width_tables.md

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (project lifecycle, :1610 path); the death apply path (to locate)

## Assumptions / Open Questions
- Order: after the retention fix, unless the reader check shows :1610 depends on it (designer). The :1610 path (now live_record_route / orphan_switch_candidate near intelligence.py:1550) skips dead bodies (alive/active filter), so it does not depend on this.
- Candidate follow-up (not filed): a dead body's quest project ends ABANDONED while `quest_status` is unchanged.

## Implementation Notes
Rulings (rpg-planner, 2026-11-25): (a) ABANDONED, `ProjectEnd.DEATH`; (b) staged in `LifecycleSystem.resolve_lifecycle`'s death block via a typed StrategicUpdate; the 1-tick passive-death lag is a limit line; (c) `quest_status` left alone (limit line; follow-up candidate, no ticket yet); (d) `current_project_id_set=""` in the same update. Divergence 2.226 (lane C's births branch takes 2.225). Phase 1 item 1 (readers) is in investigation.md; items 2 and 3 were answered by the measured run (investigation.md, "Run evidence", written at close).
- Code: `ProjectEnd.DEATH` and the pure `end_live_on_death` (src/core/strategic.py); `LifecycleSystem._end_projects_on_death` stages the typed StrategicUpdate; the death block of `resolve_lifecycle` was extracted unchanged into `LifecycleSystem._apply_death` (03a459070) to keep `resolve_lifecycle` within its length ceiling (rpg-planner ruling, option (c): fix in code, no ceiling raise), then `_apply_death` took 5 parameters (f81047800; `e_id` and `ent_upd` are derived: invariant proof in the S10 packet).
- PIN update: src/engine/access_audit/declarations.py:77, the lifecycle step's pinned static reads `('entities', 'tick')` -> `('entities',)`; cause 03a459070 (the scan is not transitive and `state.tick` is read in `_apply_death`), commit 1a4d01003, rpg-planner ruling option A.
- Own-job kit `tools/rpg_measure/death_closes_project_*` (designer's definition df2ba4b5, approved kit 18f7b53c7, SUMS 05d688a9), merged into this branch by ba254f07e.
- Divergence 2.226, parity STRAT-357, Bible ch04 and ch05 (the `_apply_death` mention), `docs/engine/known_limitations.md` 1.3 (the quest_status limit), mechanisms.yaml `goal_hierarchy` (summary and two `implemented_by` entries).

## Test Summary
- EXECUTED (own-job run, S9 #715 7185997232; rpg-designer read WORKS, recorded as #715 7187444028): kit 18f7b53c7 (SHA256SUMS 05d688a9), BASE main 4af5ef2a3 against FIX f5a520daf, 3 gate worlds, s42, 5000 t; summary sha256 e83078e8. D1-D7 PASS in every cell. Dead bodies holding a live or current project: base 32 / 30 / 15 at death, fix 0 at every tick; DEATH ends 61 / 68 / 26 (ACTIVE 35 / 33 / 14, SUSPENDED 26 / 35 / 12), equal to the extra ended transitions; living state and event stream equal to base at every tick; quest-open-after-death 0; other ended_by counts identical. NOT MEASURED: redirection (never called by the pipeline), SimQ project_abandoned (recording off).
- EXECUTED (the fix's own tests and the gaps, host gated per chunk): tests/unit/strategic/test_death_ends_live_projects.py 13 passed and test_project_end_record.py (enum-set pin gains DEATH) inside unit_strategic 1102 passed, on the final head f81047800. Gap on 74ae10da6 (all of tests/unit, tests/architecture, tests/tools): 18,307 passed, 0 failed, 35 skipped, 79 deselected, 1 xfailed; the only non-zero rc is unit_motivation rc 5 (collects no test, unchanged since K3). After the extraction and the pin update, on the heads shown: unit_systems 18, access_audit 76 and the 22 lifecycle-calling files 265 (+2 deselected, 1 xfailed) on f81047800; unit_engine 1437 and architecture 261 on 1a4d01003; unit_tools 1455 on 03a459070. GitHub CI runs the full suite on the PR.
- PIN update (changed existing expectation, rpg-planner ruling option A): src/engine/access_audit/declarations.py:77 lifecycle reads ('entities', 'tick') -> ('entities',); cause 03a459070 (the static scan is not transitive; `state.tick` is read in `LifecycleSystem._apply_death`); commit 1a4d01003; test tests/unit/engine/access_audit/test_declarations.py::test_entry_resolves_and_its_static_reads_equal_the_pinned_reads[lifecycle].
- Static gates on f81047800 (lock env ci_env_c4cd853): codebase.health check rc 0 (5 report-only jscpd rows in untouched files: baseline drift of this lock env; main's own CI Code health is SUCCESS, run 45754289485, job 139689136960), packages validate 0 problems, import_contracts ci 17 kept 0 broken, mypy | mypy_baseline filter no output. `test_plan.md` has no `## Proof Plan` section (advisory only).
Known gap: a passive HP death is classified one tick after its `alive=False`, so its project end lags that tick (0 lag rows measured in the run).
Known gap: a dead body's quest project ends ABANDONED while `quest_status` is unchanged (0 such cases measured; follow-up candidate, none filed).
Known gap: NOT MEASURED: the redirection effect on the death tick (`StrategicRedirectionSystem` is never called by the pipeline) and SimQ `project_abandoned` (recording off).
- Kit unit tests (tests/tools/test_death_closes_project_kit.py): 30 passed, 1 skipped on the kit branch; the skip is the m7 wiring check, which needs the FIX tree.

## Files Changed
- `agent-working/stored_artifacts/TCK-20261031-DEATH-CLOSES-NO-PROJECT/investigation.md`
- `agent-working/stored_artifacts/TCK-20261031-DEATH-CLOSES-NO-PROJECT/plan.md`
- `agent-working/stored_artifacts/TCK-20261031-DEATH-CLOSES-NO-PROJECT/test_plan.md`
- `agent-working/tickets/done/TCK-20261031-DEATH-CLOSES-NO-PROJECT.md`
- `docs/REGISTRY.yaml`
- `docs/engine/known_limitations.md`
- `docs/guidelines/intentional_divergences.md`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/mechanics/05_world_evolution.md`
- `docs/parity_ledger/strategic_cognition.yaml`
- `registries/mechanisms.yaml`
- `src/core/strategic.py`
- `src/engine/access_audit/declarations.py`
- `src/systems/lifecycle_systems/lifecycle.py`
- `tests/tools/test_death_closes_project_kit.py`
- `tests/unit/strategic/test_death_ends_live_projects.py`
- `tests/unit/strategic/test_project_end_record.py`
- `tools/rpg_measure/death_closes_project_controls.py`
- `tools/rpg_measure/death_closes_project_divergence_locate.py`
- `tools/rpg_measure/death_closes_project_launch.sh`
- `tools/rpg_measure/death_closes_project_logic.py`
- `tools/rpg_measure/death_closes_project_spy.py`
- `tools/rpg_measure/death_closes_project_summary.py`
- `tools/rpg_measure/death_closes_project_tree_check.sh`

## Completion Summary
A dead body no longer keeps live projects: when a subject dies, `resolve_lifecycle`'s death path (`_apply_death`) ends every ACTIVE and SUSPENDED project it holds ABANDONED with `ended_by` DEATH through `end_record` in one typed StrategicUpdate, keeps the records and clears the current project and objective (divergence 2.226, STRAT-357).

Acceptance (all met): on death every live project ends DEATH through the authoritative apply path; records are kept; unit tests cover ACTIVE and SUSPENDED; the dead-with-live-project count is 0 on the gate worlds.
- Measured (executed; S9 #715 7185997232; rpg-designer read WORKS recorded as #715 7187444028; kit 18f7b53c7, SUMS 05d688a9; summary sha256 e83078e8): 3 gate worlds, s42, 5000 t, base 4af5ef2a3 against fix f5a520daf: dead with a live or current project base 32/30/15 at death, fix 0 at every tick; DEATH ends 61/68/26 (ACTIVE 35/33/14, SUSPENDED 26/35/12) equal to the extra ended transitions; the living state and the event stream equal to base at every tick; other project ends unchanged. The designer read the later extraction (03a459070) and the 5-parameter change (f81047800) as behaviour-identical (WORKS).
- Tests on the final head f81047800: death_ends 13, unit_systems 18, access_audit 76, unit_strategic 1102, Part B (22 files that call the lifecycle) 265 passed, all rc 0. Earlier heads: unit_engine 1437 and architecture 261 on 1a4d01003; unit_tools 1455 on 03a459070; the full gap (18,307 passed, 0 failed) on 74ae10da6. GitHub CI runs the full suite on the PR (owner S10). Static on f81047800: code-health check rc 0, packages 0 problems, import contracts 17 kept 0 broken, mypy no growth.
- Limits (disclosed): a passive HP death is classified one tick after `alive=False`, so its end lags that tick (0 lag rows measured); a dead body's quest project ends ABANDONED while `quest_status` is unchanged (0 such cases measured); NOT MEASURED: the redirection effect (`StrategicRedirectionSystem` is never called by the pipeline) and SimQ `project_abandoned` (recording off).
- Skippable follow-ups (rpg-planner files them): on BASE `capacity_enforcement` keeps rewriting the contracts of dead bodies (cognition backlog); `StrategicRedirectionSystem` is dead code (P3, non-behaviour PR); the spy costs about 2.2-2.4x a plain run (a kit fact); the quest_status note has no measured case.
- Merge note: a merge-tree against births-2 880c80371 leaves one lifecycle.py hunk (births-2 rewrote the lifecycle= argument inside the block this change moved); births-2 resolves it at its own main merge (agreed with the lead), plus an adjacency conflict in intentional_divergences.md.
- Hand-orchestrated close (rpg-planner): kit + S9 run + gaps. data/runs entries from the gaps are cleaned by id after the owner's S10 yes.
