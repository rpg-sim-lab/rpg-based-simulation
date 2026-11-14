---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session domain: architecture

Source of the architecture part of a role card. Ownership and routes come from `registries/session_roles.yaml`
and are not restated here. Only `## Card` is injected.

## Card
Domain: architecture (proposals and reviews in docs/plans/architecture/). Recorded decisions bind you: system_overview ("deliberately not distributed", as amended by distributed_workers_adr), the devops ADR and amendment (also amended there), next_generation_engine_adr, kernel_concurrency_design_philosophy, PERF-D1/D2. Code goes to rpg-planner or perf-planner; ADRs go to lead-planner. Implementers write only docs/plans/architecture/** until owns grow; code goes to rpg or perf implementers.
