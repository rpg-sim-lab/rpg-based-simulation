---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY
artifact_type: plan
tags: [documentation, reference]
---

# Plan: TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY

Spec: the ticket (scope and ACs), cited not copied. Template: `tools/glossary_registry.py`.

1. `tools/world_glossary_registry.py`: `load_registry`, `source_problem`, `add_term`, `add`/`list` CLI. Fields `term`, `description`, `source`, `added`.
2. `registries/world_glossary.jsonl` committed empty (no seed rows).
3. Tests in `tests/tools/test_world_glossary_registry.py`.
4. Route: add the file to the rpg domain's `owns` and the tool to agent-working's in `registries/session_roles.yaml`; regenerate the cards; `tools.sessions.validate` must be clean.

Decision (the ticket's open question): `source` roots are `docs/mechanics/`, `docs/engine/`, `docs/core/` only. `docs/architecture/` is not allowed, because the wiki must point at the law. Widening later is one constant.
