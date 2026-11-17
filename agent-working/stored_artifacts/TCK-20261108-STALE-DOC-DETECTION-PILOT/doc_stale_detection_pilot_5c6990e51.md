---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-STALE-DOC-DETECTION-PILOT
artifact_type: report
tags: [ai, documentation]
---

# Stale-doc detection pilot: J2 evaluation

**Scope: a docs audit, not an implementation audit.** It says which docs a detector marks as possibly stale and how often a hand read agreed. It does not claim any code is correct.
**Pin:** `5c6990e51c2cf1b6f0f842cb969772ba70d46485` (origin/main after #859), read with `git show <pin>:path` and git plumbing; the working tree was not read.
**Ticket:** `TCK-20261108-STALE-DOC-DETECTION-PILOT` (batches J1 and J2 of the docs-as-review-source plan, rev 3.2). J3 is not approved: no doc was edited, retired or marked. The tool is `tools/gate_checks/doc_drift.py --mode detect`; the numbers below come from `tools/gate_checks/doc_drift_pilot.py --pin <sha>`.
**Run:** wall time 20.3 s, peak memory 88 MB (one process). `git status --porcelain -- docs/` before the run and after it: both empty, so no doc was changed.

## 1. What was flagged

The run read 1,182 docs (everything under `docs/` except `brainstorm/`), set aside 583 as history (448 archive, 89 historical status, 31 audits, 15 review records, the shared R3 classes), and so judged **599 live docs**. **480 of the 599 (80%) were flagged**; 119 had no signal. Docs with `verified_by` or `reviewed_by` stay quiet while their baseline is clean; none carries those fields yet, so that count is 0.

| Signal | Docs flagged |
|---|---|
| evidence-newer | 354 |
| unresolved-name | 333 |
| plan-lifecycle | 72 |

A doc can carry several signals: 237 have one, 207 have two, 36 have all three.

| Owning domain (route map) | Docs | evidence-newer | unresolved-name | plan-lifecycle |
|---|---|---|---|---|
| rpg | 160 | 109 | 116 | 12 |
| unowned | 176 | 137 | 115 | 18 |
| agent-working | 37 | 31 | 23 | 14 |
| perf | 22 | 20 | 18 | 3 |
| codebase | 21 | 17 | 14 | 17 |
| lead | 21 | 17 | 13 | 0 |
| asset | 17 | 10 | 14 | 3 |
| platform | 15 | 3 | 15 | 0 |
| testing | 8 | 7 | 4 | 3 |
| architecture | 3 | 3 | 1 | 2 |

## 2. False-positive rate on a hand-read sample

Sample: 20 docs, taken at a fixed stride **within each signal's own ranked list** (7 evidence-newer, 7 unresolved-name, 6 plan-lifecycle; midpoints of equal slices, so the whole ranking is covered, not only the top). I read each doc's flagged claims against the code or tickets at the pin. A flag is a **true positive** when I found a concrete claim that is wrong, or a lifecycle marker that is wrong, at the pin. It is a **false positive** when I found no contradiction in the flagged claims. **Limits:** I graded my own sample; I read the flagged regions, not every line of each doc, so "no contradiction found" is not proof the doc is right; **the reviewer (agent-working-planner) spot-checked 4 of the 5 rows I suggested (rows 2, 4, 13 and 20, against the pin) and confirmed all four as true positives; no false-positive verdict was independently re-read** by anyone but me (the reviewer read the stated reasons for the 10 false-positive rows and found them specific and plausible, which is not a re-check). So the 50% figure is a one-reader measurement.

| # | Signal | Doc | Verdict | Reason |
|---|---|---|---|---|
| 1 | evidence-newer | `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` | false positive | Its claim that `reproduction_humanoid.py` resolves the spawn region and sets `home_region_id` still holds. |
| 2 | evidence-newer | `docs/core/items_and_inventory.md` | true positive (minor) | Says the default `ItemRegistry._items` holds 18 items; the pin has 19 (`ancient_core` is new). |
| 3 | evidence-newer | `docs/plans/unreachable_mechanism_classification.md` | false positive | A dated record ("Filed 2026-09-30"); registry changes since are expected and it is true as a record. |
| 4 | evidence-newer | `docs/world/density_metrics.md` | true positive | Says `TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY` is not implemented and the generator has no area term; the ticket is done and the generator has an area-aware formula. |
| 5 | evidence-newer | `docs/architecture/kernel_concurrency_design_philosophy.md` | false positive | Known-stale at 531010a9a, but edited on 2026-11-09 to match #837; the only newer cited path is `state.py`, changed by an unrelated combat ticket. |
| 6 | evidence-newer | `docs/world_rules/foundations/resource.md` | false positive | The cited `loot_table` field and `state.seed` use are both still as described. |
| 7 | evidence-newer | `docs/guides/cross_session_messages.md` | false positive | The newer paths are cited as examples; I found no wrong claim. |
| 8 | unresolved-name | `docs/plans/codebase_health/python_code_craft_gates_flip_ticket_brief.md` | false positive | The doc itself says the history file moved to `.jsonl` in #326. |
| 9 | unresolved-name | `docs/world_rules/review-exports/places-territory-batch-11a-review.md` | false positive | `TerritorialRelation` appears only in "possible implementation direction" text. |
| 10 | unresolved-name | `docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md` | false positive | The unresolved names (`PerfBudget`, `check_perf_regression.py`) are the things the epic says to retire, and they were retired. |
| 11 | unresolved-name | `docs/world_rules/life-body/survival-needs.md` | false positive | Rule-catalog design names, not code names. |
| 12 | unresolved-name | `docs/plans/agent_infrastructure/ai_first_hardening_epics/task_success_rate_metric_experiment.md` | false positive | A reference to a brainstorm document that exists as a lowercase `.html` file. |
| 13 | unresolved-name | `docs/engine/matrices/replay_test_matrix.md` | true positive | Lists about ten test names (`test_staging_bound`, `test_size_rotation`, ...); `test_replay_contract.py` has two tests, none of those. |
| 14 | unresolved-name | `docs/simulation/domains/world_emergence_contract.md` | true positive | Lists source files (`aggregator.py`, `pressure_model.py`, `opportunity_service.py`, ...) that no longer exist; the package is now `aggregators.py`, `models.py`, `services.py`. |
| 15 | plan-lifecycle | `docs/plans/simulation_semantic_control_plane/finding_triage_log.md` | unclear | A log of findings; `status: active` with both cited tickets done. It may still be extended. |
| 16 | plan-lifecycle | `.../ai_first_hardening_epics/governance_capability_policy_epic.md` | true positive | Says "Tracking ticket: not yet created (planning stage)" while citing six done tickets and its own "landed" status update. |
| 17 | plan-lifecycle | `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` | true positive | Says its tracking epic is "not yet created"; that epic is in `tickets/done/`. |
| 18 | plan-lifecycle | `docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md` | true positive | `status: idea` although the idea shipped (hand closures carry `duration_source` and a week close re-derives durations). |
| 19 | plan-lifecycle | `docs/plans/architecture/faster_feature_testing_draft_tickets.md` | unclear | A draft-ticket list whose three tickets are done; it still reads as a record. |
| 20 | plan-lifecycle | `docs/plans/codebase_health/codebase_domain_root.md` | true positive | Says the codebase domain is not yet in the ownership table; `registries/session_roles.yaml` has a `codebase` domain with `owns` globs. |

| Signal | Sampled | True positive | False positive | Unclear |
|---|---|---|---|---|
| evidence-newer | 7 | 2 | 5 | 0 |
| unresolved-name | 7 | 2 | 5 | 0 |
| plan-lifecycle | 6 | 4 | 0 | 2 |
| **All** | **20** | **8** | **10** | **2** |

**Measured false-positive rate: 10 of 20 (50%); 12 of 20 (60%) if the two unclear docs are counted as false.** The sample is small, so the interval is wide (for 10 of 20, a 95% interval is roughly 30% to 70%). Per signal, plan-lifecycle was the most precise (4 of 6 true) and the two path-based signals were the noisiest (5 of 7 false each). A false positive here is a cheap one: it costs one triage read, and the signals only ever say "possibly stale".

## 3. Recall on the labelled set (measured at 531010a9a, not tuned)

The audit of 2026-11-07 labelled four stale docs; items 2 and 4 are labelled undetectable by design. Run at `531010a9a`:

| Item | Doc | Result |
|---|---|---|
| 1 | `docs/engine/contracts/simulation_kernel_contract.md` | flagged, evidence-newer (14 of its 21 cited paths newer; the plan measured the same) |
| 6 | `docs/architecture/kernel_concurrency_design_philosophy.md` | flagged, evidence-newer (9 of 17 newer, as in the plan) and one unresolved name |
| 2 | `docs/engine/deterministic_execution.md` | flagged only by unresolved names (`dropped_work`, `tick_hash`, `BudgetedCanonicalHasher`, ...), which are not the known stale seed claim; I do not count it as a detection |
| 4 | `docs/observability/hard_law_monitor.md` | not flagged (cites no src paths) |

Recall on the two detectable-by-design items: **2 of 2**. Recall on all four with strict credit: **2 of 4**, as the plan predicted. The limit the plan stated holds: a partly updated doc (item 2) and a doc that cites no code (item 4) are not caught by a timestamp signal. Nothing here is a threshold or a test target: the tests use temp-repo fixtures only.

## 4. Sized J3 proposal (for the owner to scope; nothing here is approved)

480 flagged docs (80% of the live docs) is too many to triage at once, and about three in four of the path-based flags in the sample were false. At this rate the detector does not narrow the corpus much; its value is the ranking, not the flag. A sized option, cheapest first:
- **J3a, plan lifecycle only (72 docs, 4 of 6 true in the sample).** Each owning domain sets `status: historical` on finished plans or marks them `reviewed_by`. About 72 short reads; 17 of those are in `codebase`. Highest yield per read.
- **J3b, evidence-newer where 3 or more cited paths changed, or the lag exceeds 60 days.** Takes the top of the ranking only; a number to estimate from the full list before committing (not measured here).
- **J3c, topic-map satellites and runbooks first** (as the plan says), since they are what reviews cite.
- **Not proposed:** unresolved-name on its own (5 of 7 false), except for docs that name a missing source file or test file (both true positives in the sample were of that kind); a refinement to try before spending reads there.

## 5. Known limits of this pilot

- One implementer graded a 20-doc sample; true-positive judgments need a second reader.
- `unresolved-name` also reads identifier-shaped backticked names, which brings design names and examples into the flags.
- Only `src`, `tests`, `tools`, `registries`, `codebase` and `frontend` paths count as code evidence for `evidence-newer`. A doc that cites code only by module name, or only by a directory, is invisible to it.
- The route map labels 176 docs "unowned", the largest bucket after `rpg`.
