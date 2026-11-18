---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
artifact_type: investigation
tags: [skills, simulation-quality, testing]
---

# Coverage audit (P1, draft; gaps are provisional until the P2 defect set is confirmed)

Method: inventory of `.claude/skills` (23), `.claude/agents` (role agents), `tools/mechanism_registry`, `tools/gate_checks`, `docs/testing/test_taxonomy.md`, `registries/mechanisms.yaml` header, `tests/architecture`, `tests/mechanic_scenarios`, `docs/world_rules`, and the skill-catalog epic investigation. Reads were excerpts, not full audits; every row below is a pointer to verify, not a verdict.

## What exists, by gap area

| Gap area | Existing coverage | What it does NOT do |
|---|---|---|
| Rule truth source | `docs/mechanics/` (Bible), `docs/engine/`, `docs/world_rules/` (accepted Rule IDs, per-batch scenarios and reviews), parity ledger | Says what must hold, not how an agent checks an interaction between two rules |
| Law vs code parity | `mechanics-auditor` agent, `parity-updater`, `mechanics_auditor_static.py` | Compares one chapter to one module; per-law, not cross-mechanism or over time. Bible chapters 01-06 only listed (07 absent from the agent's table) |
| Domain skills | `combat-mechanics`, `cognition-strategy`, `systems-economy`, `progression-entities`, `observability`, `simq-dev` | Orient an agent editing one subsystem; none addresses behaviour across subsystems |
| Mechanism reachability | `registries/mechanisms.yaml` state axis plus `verified` axis (instrument: census/scenario/corpus_run/code_trace; verdict), `mechanism_state_caller_check.py`, `changed_code_check`, `completeness_check`; header records the static-vs-runtime lesson | Registry records evidence; no reusable procedure for choosing and running the instrument per mechanism |
| Soft/causal correctness | `docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md` §4.2 (definition, implementation-independent) | A definition, not a workflow; explicitly leaves evidence production open |
| Test technique choice | `test_taxonomy.md` §6 (example, property, stateful property, metamorphic, characterization), §7 evidence classes, §9 oracle principle | Guidance doc, not an agent procedure. Metamorphic is gated on replay reliability (long-run determinism parked) |
| Property testing | `hypothesis>=6.0.0` is in `pyproject.toml` | 0 files in `tests/`, `src/`, `tools/` import it. Stateful/property technique is documented but not practised |
| Scenario tests | `tests/mechanic_scenarios/` (value-differential, through-kernel, gated-visit, death-trace etc.) | Per-defect regression style; no systematic derivation from a mechanism's lifecycle |
| Structural guards | `tests/architecture/` (write-path, dormancy, accumulation, ordering guards) | Static structure; cannot see runtime lifecycle (stuck slot, recreated project) |
| Run-level checks | `HardLawMonitor`, SimQ pillars, `simulation-analyst`, `simq-audit`, `investigate-simulation-result` | Aggregate bands; `TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` already records a blind spot for scale-dependent behaviour |
| Debugging | `debugging-strategies` (generic), `world-debugger` (assembly/content only) | No simulation-causal debugging method (trace a decision across ticks) |
| Review | `architecture-reviewer` (durable-state, API, registry rules) | Structure review, not mechanism-interaction review |
| V&V framing | Test-architecture plan, evidence classes, `verified` axis | No NASA-STD-7009 / Sargent-style credibility framing found (search of docs: only archive hits) |

## Finding that constrains the proposal: skills are rarely invoked
From `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC` investigation (all-time `Skill` calls 205): the project domain skills (`api-design-principles`, `debugging-strategies`, `python-performance-optimization`, `architecture`, `python-testing-patterns`, `test-driven-development` and others) had zero invocations. Tag-based suggestions are advisory and were acted on 0 of 20 times; the one suggestion made binding (`security` -> mandatory Security-Review phase) is the one that works. Implication: a new advisory skill is likely to go unused. Delivery form (binding gate, agent role, or tool) matters more than topic. Figures are from 2026-08; re-measure before relying on them (`tools/agent-monitoring/skill_usage_metric.py`).

## Provisional real gaps (to confirm in P2/P3)
1. No procedure for cross-mechanism interaction review (two mechanisms writing or reading the same state; lifecycle slot ownership; re-creation loops). Existing reviewers check one law or one structure.
2. No procedure for temporal reasoning (units, scaling, raw vs derived time such as world_time vs day/phase). Bible ch.05 states the laws; nothing guides an agent to check a change against them.
3. No reusable lifecycle/termination checklist for long-lived records (projects, suspensions, failure reasons): creation, ownership, termination, release.
4. Property/stateful testing is specified (`test_taxonomy.md` §6) but unused (0 hypothesis imports): a practice gap, possibly a tooling or fixture gap rather than a skill gap.
5. Vacuous-branch / unreachable-condition detection beyond `code_trace` (see mechanisms.yaml header): runtime-evidence selection is recorded but not taught.

Not gaps (already covered; do not duplicate): world rules and formulas (Bible, engine, world_rules), reachability bookkeeping (mechanism registry), test-level and evidence-class vocabulary (test_taxonomy), structural guards (tests/architecture).

## Open for the proposal
Several gaps may be closed by extending an existing agent or tool (mechanics-auditor scope, a mechanism-interaction check beside `mechanism_state_caller_check.py`, enabling hypothesis in one pilot area) rather than adding a skill. That option stays in P4.
