---
status: active
layer: architecture
authority: P1
audience: agent
tags: [documentation, architecture]
---

# Documentation topic map

Start every review here. For each fact group this page names one **canonical doc** (the doc that owns the fact), its **normative source**, and the **satellite docs** that should link to the canonical doc instead of restating it. It extends the D25 map ([`docs/audits/D25_engine_docs_drift.md`](../audits/D25_engine_docs_drift.md) §1), keeping all five of D25's rows.

Built 2026-11-08 at origin/main 297494469 (TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP). Canonical docs were chosen from each doc's stated scope, headers and frontmatter; full bodies were not read. Confidence says how sure that choice is. A canonical doc is **not** thereby verified correct.

## Precedence of normative sources

When two sources disagree, the higher one wins:

1. **World-rules catalog** (`docs/world_rules/`, accepted Rule IDs).
2. **Mechanics Bible** (`docs/mechanics/`).
3. **Engine and architecture contracts** (`docs/engine/`, `docs/engine/contracts/`, `docs/architecture/*_contract.md`, and the other `*_contract.md` files under `docs/`).
4. **Parity ledger and divergences** (`docs/parity_ledger/`, `docs/guidelines/intentional_divergences.md`). These record whether the code matches 1-3; they don't define intent.

Everything else is **explanatory**: guides, READMEs, ADRs, design philosophy, runbooks, skills. History is never canonical: `docs/archive/`, `docs/audits/`, `docs/brainstorm/`, and plans whose frontmatter `status` is `historical` or `superseded`.

When code disagrees with a normative doc, that is a defect or a proposed divergence. Nobody edits the normative doc to match the code. The difference goes to the rule owner as a defect ticket, or as an `intentional_divergences.md` entry if the owner accepts the code's behaviour.

## Verification status

Every canonical doc below is **unverified**: no doc carries the P1 evidence fields (`evidence_paths`, `verified_by`, `verified_at`) yet. Once those fields exist, the status is derived by the doc drift report, never typed here by hand. The statuses of other living docs belong to the drift report, not this page.

## Map

Normative level: 1-4 as above, or **expl.** (explanatory).

### Engine and kernel

| Fact group | Canonical doc | Level | Satellites (link, don't restate) | Confidence | Known conflict |
|---|---|---|---|---|---|
| Kernel phases (count, names, order) | [`docs/engine/kernel.md`](../engine/kernel.md) | 3 | `docs/engine/architecture.md`, `docs/engine/contracts/simulation_kernel_contract.md` §4 (may restate the law, not the names), `docs/architecture/system_overview.md`, `docs/engine/contracts/infrastructure_overview.md`, `CLAUDE.md`, `docs/engine/capability_registry.yaml` | high (D25) | C1 |
| Authoritative pipeline, refinement order | [`docs/engine/authoritative_pipeline.md`](../engine/authoritative_pipeline.md); the phase count is generated in [`docs/performance/phase_inventory.md`](../performance/phase_inventory.md) | 3 | `authoritative_refinement_contract.md`, `authoritative_mutation_pipeline_contract.md`, `authoritative_apply_contract.md`, `project_lawbook*.md`, `docs/guides/simulation.md`, `capability_registry.yaml` | high (D25) | C1, C6 |
| Determinism and RNG | [`docs/engine/deterministic_execution.md`](../engine/deterministic_execution.md) (mechanics); [`simulation_kernel_contract.md`](../engine/contracts/simulation_kernel_contract.md) §7 owns the law | 3 | `docs/engine/contracts/minimal_kernel.md` §7, `docs/engine/architecture.md` §4, `docs/engine/architecture_reference.md` §4.2, `docs/compliance/checklist.md` §12, `docs/architecture/kernel_concurrency_design_philosophy.md` | medium | C2, C5 |
| Checkpoint hashing law | [`docs/engine/contracts/substrate_baseline_contract.md`](../engine/contracts/substrate_baseline_contract.md) §7 | 3 | `minimal_kernel.md` §8, `deterministic_execution.md` "Checkpoint files" | medium | |
| Scenario checkpoint format and restore | [`docs/engine/scenario_runtime_contract.md`](../engine/scenario_runtime_contract.md) | 3 | `docs/engine/kernel.md`, `deterministic_execution.md` | medium | |
| Worker / collection concurrency | [`docs/engine/contracts/worker_contract.md`](../engine/contracts/worker_contract.md) | 3 | `kernel.md`, `simulation_kernel_contract.md` §9, `bounded_concurrency_contract.md`, `concurrent_integrity_contract.md`, `kernel_concurrency_design_philosophy.md` (owns the reasoning, not the rule) | high (D25) | |
| Replay | [`docs/engine/contracts/replay_contract.md`](../engine/contracts/replay_contract.md) | 3 | `deterministic_execution.md`, `docs/engine/matrices/replay_mode_matrix.md`, `replay_test_matrix.md`, `docs/guides/reviewer_replay_check.md`, `observability_artifact_contract.md`. Not `docs/ai/replay_*` (agent fixtures, a different meaning). | medium | |
| Architectural pillars / lawbook | [`docs/engine/project_lawbook.md`](../engine/project_lawbook.md) | 3 | `project_lawbook_m10.md` | high (D25) | D25 pillar-list drift, not re-checked |
| Performance measurement and claims | [`docs/engine/performance_contract.md`](../engine/performance_contract.md); hardware classes are in [`certification_contract.md`](../engine/contracts/certification_contract.md) §3 | 3 | `docs/performance/perf_baseline_policy.md`, `tick_cost_growth.md`, `docs/architecture/performance_optimization.md`, `docs/guides/performance_profiling.md`, `docs/engine/architecture.md` §5 | high (D25 for hardware classes) | |

### API and observability

| Fact group | Canonical doc | Level | Satellites | Confidence | Known conflict |
|---|---|---|---|---|---|
| REST API | [`docs/engine/contracts/api_protocol_contract.md`](../engine/contracts/api_protocol_contract.md) | 3 | `docs/engine/contracts/api_reference.md`, `frontend.md`, `docs/architecture/http_api_key_authentication.md`, `http_admission_control.md` | medium | |
| Read-model facade | [`docs/observability/read_model_service_contract.md`](../observability/read_model_service_contract.md) | 3 | `api_protocol_contract.md`, `frontend.md` | medium | |
| WebSocket protocol | `api_protocol_contract.md` §2 | 3 | `frontend.md` §B, `read_model_service_contract.md`, `http_api_key_authentication.md` §4, `docs/compliance/checklist.md`, `README.md` | high | |
| Event stream, backpressure, DLQ | [`docs/architecture/observability_hot_path_safety_contract.md`](observability_hot_path_safety_contract.md) | 3 | `docs/engine/contracts/observability_contract.md`, `observability_artifact_contract.md`, `docs/guides/observability.md`, `docs/observability/how_to_run_simulation.md` §3, `replay_contract.md` (backpressure) | medium | |
| Hard-law monitor | [`docs/observability/hard_law_monitor.md`](../observability/hard_law_monitor.md) | 3 (a contract in practice) | `.claude/skills/observability/SKILL.md`, `docs/ai/skills.md`, `docs/guides/observability.md`, `kernel.md`, `performance_contract.md`, `intentional_divergences.md` | high | C3 |
| Metrics | [`docs/observability/prometheus_metrics.md`](../observability/prometheus_metrics.md) | 3 (de facto) | `docs/observability/loki_label_policy.md`, `hard_law_monitor.md` §4, `docs/guides/observability.md`, `observability_contract.md` | medium | |
| Alerts | [`docs/runbooks/README.md`](../runbooks/README.md) with `alerting-pipeline.md` | expl. | `devops_baseline_adr.md`, `simulation_watchdog.md`, `docs/runbooks/*.md` | low | Gap: no contract owns the alert rules; the rule config was not checked |
| Simulation watchdog | [`docs/architecture/simulation_watchdog.md`](simulation_watchdog.md) | expl. (ADR) | `devops_baseline_adr.md`, `system_overview.md`, `harness_architecture.md`, `bounded_concurrency_contract.md`, `CLAUDE.md` | medium | Gap: the only doc on the topic is an ADR, not a contract |

### World and content

| Fact group | Canonical doc | Level | Satellites | Confidence | Known conflict |
|---|---|---|---|---|---|
| Content pipeline | [`docs/content/pipeline_contract.md`](../content/pipeline_contract.md) | 3 | `docs/content/content_pack_format.md`, `content_semantics_contract.md`, `docs/guides/content_authoring.md`, `docs/mechanics/content_usage_matrix.md` | high | |
| World assembly | [`docs/world/assembly_contract.md`](../world/assembly_contract.md) | 3 | `docs/architecture/world_assembly_architecture.md`, `docs/world/compiler_contract.md`, `generator_contract.md`, `modules_contract.md`, `docs/architecture/world_repository_layout.md` | medium | |
| World evolution, ecology, calamities | [`docs/mechanics/05_world_evolution.md`](../mechanics/05_world_evolution.md) | 2 (1: `world_rules/life-body/ecology-population.md`, `space-environment/environment.md`) | `docs/world/ecology_and_calamity_contract.md`, `threat_and_consequences_contract.md`, `raid_boss_camp_contract.md`, `docs/simulation/domains/world_emergence_contract.md`, `parity_ledger/world_dynamics.yaml` | medium | |

### Mechanics

| Fact group | Canonical doc | Level | Satellites | Confidence | Known conflict |
|---|---|---|---|---|---|
| Economy and conservation | [`docs/mechanics/03_economic_laws.md`](../mechanics/03_economic_laws.md) | 2 (1: `world_rules/material-economy/economy-exchange.md`, `ownership-possession.md`) | `docs/mechanics/resource_conservation_contract.md` (sub-contract), `docs/systems/README.md`, `parity_ledger/town_resource.yaml`, `.claude/skills/systems-economy` | medium | |
| Harvesting and resource nodes | `03_economic_laws.md` §3 | 2 (1: `world_rules/material-economy/resources-production.md`) | `resource_conservation_contract.md`, `intentional_divergences.md` §2.60 and §2.85, `docs/engine/contracts/supported_gameplay_surface.md`, `docs/core/state.md` | medium | |
| Combat resolution | [`docs/mechanics/02_combat_laws.md`](../mechanics/02_combat_laws.md) | 2 (1: `world_rules/capability-progression/conflict-combat.md`) | `docs/mechanics/damage_formula_contract.md`, `docs/engine/contracts/combat_contract.md`, `tactical_contract.md`, `docs/simulation/domains/combat_engagement_contract.md`, `docs/combat/combat_movement_overhaul_spec.md` | medium | Scope line with `combat_contract.md` unclear |
| Strategic cognition and goals | [`docs/mechanics/04_strategic_cognition.md`](../mechanics/04_strategic_cognition.md) | 2 (1: `world_rules/knowledge-agency/`) | `docs/systems/strategic_cognition.md`, `docs/strategy/bounded_cognition_contract.md`, `docs/cognition/self_model_contract.md`, `docs/architecture/cognition_domain_ownership.md`, `parity_ledger/strategic_cognition.yaml` | medium | `systems/strategic_cognition.md` may restate the chapter |
| Regional sovereignty and governance | [`docs/mechanics/regional_sovereignty.md`](../mechanics/regional_sovereignty.md) | 2 (1: `world_rules/institutions-politics/politics-authority.md`) | `docs/world/regional_sovereignty_runtime_contract.md`, `05_world_evolution.md`, `06_worldbuilding_foundation.md` | medium | |
| Faction mechanics | [`docs/systems/faction_contract.md`](../systems/faction_contract.md) | 3 (1: `world_rules/institutions-politics/organizations.md`) | `regional_sovereignty.md`, `parity_ledger/faction.yaml` | medium | |
| Social and political dynamics | [`docs/mechanics/07_social_political_dynamics.md`](../mechanics/07_social_political_dynamics.md) | 2 (1: `world_rules/social-lineage/`, `institutions-politics/`) | `docs/simulation/social_systems_contract.md`, `docs/simulation/domains/social_memory_contract.md`, `cooperation_contract.md`, `party_contract.md`, `parity_ledger/social_narrative.yaml` | medium | |
| Progression and XP | [`docs/mechanics/01_entity_anatomy.md`](../mechanics/01_entity_anatomy.md) | 2 (1: `world_rules/capability-progression/capability-progression.md`) | `docs/mechanics/attribute_progression_contract.md`, `docs/simulation/domains/progression_contract.md`, `docs/core/attributes_and_classes.md`, `parity_ledger/progression.yaml`, `.claude/skills/progression-entities` | medium | `docs/mechanics/README.md` assigns the XP formula to `attribute_progression_contract.md`; the three sites agree today |

### Process

| Fact group | Canonical doc | Level | Satellites | Confidence | Known conflict |
|---|---|---|---|---|---|
| implement-ticket pipeline | [`docs/ai/ticket-lifecycle.md`](../ai/ticket-lifecycle.md); the executable source is `.claude/workflows/implement-ticket.js` | expl. | `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/architecture/agent_orchestration_contract.md`, `CLAUDE.md` Tier Routing, `docs/guides/agent_session_reset_boundaries.md` | medium | C4 |
| Session roles | [`docs/guidelines/session_roles/`](../guidelines/session_roles/); the data source is `registries/session_roles.yaml` | expl. | `docs/guides/agent_working_path_map.md`, `docs/guidelines/agent_working_environment.md`, `docs/guides/cross_session_messages.md` | medium | |
| Delivery process (commits, PRs, CI) | [`docs/guides/delivery_process.md`](../guides/delivery_process.md) | expl. | `CLAUDE.md`, `docs/guides/ticket_reporting.md`, `ticket_tagging.md` | high | |
| Test taxonomy | [`docs/testing/test_taxonomy.md`](../testing/test_taxonomy.md) | expl. | `docs/guides/testing.md`, `docs/testing/regression_policy.md`, `no_duplication_test_policy.md`, `requirement_traceability.md` (owns a different fact), `CLAUDE.md` | high | |

## Known conflicts (2026-11-08)

Found while building this map. Each one goes to the doc's owner. Nothing here is fixed by this page.

| ID | Conflict | Evidence | Owner |
|---|---|---|---|
| C1 | `docs/engine/capability_registry.yaml` says "6-Phase Kernel Loop" (`:35-37`) and "17-phase refinement" (`:30`). `kernel.md` names 7 phases, and `authoritative_pipeline.md:22` bans literal counts. | Checked by lead-planner at 297494469 | rpg |
| C2 | `docs/engine/architecture.md:81` says `DeterministicRNG` uses `xxhash`. `deterministic_execution.md:121` and the code describe a composite seed into a fresh `random.Random`, and `src/platform/rng.py` has no xxhash. | `architecture.md:81` and `rng.py` checked by lead-planner at 297494469; the `deterministic_execution.md:121` line was reported by the investigation agent | rpg |
| C3 | Hard-law count: `.claude/skills/observability/SKILL.md:24` says 7, `docs/ai/skills.md:227` says 7, `hard_law_monitor.md:16` says 8, and the code has 9. The doc's own fix is batch A, item 4 of the docs-as-review-source plan. | Skill line checked by lead-planner; the counts of 8 and 9 come from the 2026-11-07 audit | rpg (doc), agent-working (skill files) |
| C4 | implement-ticket phase count: `CLAUDE.md` says "10-phase (+1 conditional)", while `docs/ai/ticket-lifecycle.md:23` and `docs/ai/system_overview.md` say "11-phase". This may be the same count worded two ways, but no single doc owns the number. | Reported by the investigation agent, not re-read | agent-working |
| C5 | `simulation_kernel_contract.md:11` claims "single source of truth" for kernel behaviour, while `kernel.md` owns phases and `deterministic_execution.md` the RNG mechanics. No contradiction was seen in content, but the scope wording needs stating. | Reported by the investigation agent | rpg |
| C6 | `authoritative_pipeline.md:24` says its own table is missing six executable phases and has one ghost row. | Reported by the investigation agent | rpg |

## Not covered

- World-rules Rule IDs aren't mapped per fact group. The level-1 entries are file-level, picked by name.
- Parity-ledger entries and `intentional_divergences.md` were seen by heading only.
- The alert-rule config (Grafana and Prometheus files) wasn't checked.
- `docs/simulation_quality/`, `docs/event_ledger/` and `docs/compliance/` have no row yet.
- D25's follow-up (`docs/engine/contracts/` and `matrices/` at full depth) is batch G of the docs-as-review-source plan.
