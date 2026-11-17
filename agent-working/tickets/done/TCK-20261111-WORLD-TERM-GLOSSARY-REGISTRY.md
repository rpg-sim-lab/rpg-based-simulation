---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY
phase: done
date: 2026-11-11
tags: [documentation, reference]
---

# TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY

## Title
A world-term glossary registry the website wiki can render: term, plain description, source pointer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decision #715 6789779149 (relayed by lead-planner): the website wiki (#845) is a view
generated from stored repo data. It needs plain descriptions of world terms (tick, region, lead,
faction, calamity, ...). `registries/glossary_registry.jsonl` holds only the agent-ops
dashboard's process enums, and its module says that category set is fixed.

Design call (agent-working-planner, acked by lead): a **separate** registry, not a new category
in the existing one, because:
- `src/api/agent_ops_dashboard/ingest.py` serves the whole existing file as dashboard tooltips,
  so world terms would leak into the agent-ops UI;
- that file is one case-sensitive namespace keyed by term, and world terms (kernel phases such as
  Resolution and Collection, the word "phase") sit beside its 40 workflow phase names;
- a world term must point at the law it summarises, and the existing rows have no such field.

## Scope
- `registries/world_glossary.jsonl`: append-only JSONL, one row per term. Row fields: `term`
  (exact display string, case-sensitive, unique), `description` (one or two plain sentences, no
  formula), `source` (repo path to an authoritative doc in `docs/mechanics/`, `docs/engine/` or
  `docs/core/`, optional `#anchor`), `added` (ISO date).
- `tools/world_glossary_registry.py`: `add` / `list` CLI and `load_registry()`, modelled on
  `tools/glossary_registry.py`. The loader refuses duplicate terms. `add` refuses an empty
  description and a `source` path that does not exist.
- Tests in `tests/tools/` for load, add, duplicate refusal, a missing source path, and a corpus
  check that every committed row's `source` still resolves.
- A route for the new file and tool in `registries/session_*.yaml`. The tool belongs to
  agent-working. The registry rows are rpg content: rpg-planner writes or reviews descriptions.
- A short section in the module docstring saying how this registry differs from the dashboard
  glossary (and why the two never merge).

## Out of Scope
- Writing the world-term descriptions themselves (rpg's; a separate rpg ticket seeds them).
- The wiki generator and its Glossary page (lead's #845 track; it skips the page until the file
  exists).
- Any change to `registries/glossary_registry.jsonl`, `tools/glossary_registry.py` or the
  dashboard API.
- Reconciling with `docs/plans/design_enhancement/performance_optimization/system_design_terms_and_concepts.md`
  (a WIP P2 architecture-terms guide, not world terms); noted under Open Questions.

## Acceptance Criteria
1. `python3 tools/world_glossary_registry.py add <term> --description "..." --source docs/...`
   appends one valid row; re-adding the same term exits non-zero and writes nothing.
2. `add` with a `source` that does not exist in the repo exits non-zero and writes nothing.
3. `load_registry()` returns `{term: row}` and raises on a duplicate term in the file.
4. The corpus test passes on the committed file, including when it is empty or absent.
5. `python3 -m tools.sessions.route registries/world_glossary.jsonl` names an owner.
6. No change to the dashboard glossary file, its module, or `src/api/`.

## Related Tickets
- TCK-20260718-GLOSSARY-REGISTRY (the dashboard glossary this mirrors)
- TCK-20261111-MECHANISM-SUMMARY-FIELD-SHAPE-CHECK (the other wiki source gap)

## Related Docs
- docs/mechanics/, docs/engine/, docs/core/ (the only valid `source` roots)
- docs/plans/design_enhancement/performance_optimization/system_design_terms_and_concepts.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260718-GLOSSARY-REGISTRY/

## Related Code Areas
- tools/glossary_registry.py, tools/tag_registry.py (templates)
- registries/session_roles.yaml, registries/session_authority.yaml
- Consumer: website/scripts/generate_wiki.py (lead's lead-website-wiki branch). It reads `term`,
  `description` and `source`, so keep those field names stable, and it renders nothing while the file is
  absent or empty.

## Assumptions / Open Questions
- The `source` roots are limited to the three authoritative doc trees so that the wiki points at
  the law. Whether to also allow `docs/architecture/` is open, and is decided at Plan.
- Whether the terms guide above should later cite this registry, or be cited by it, belongs to
  that guide's owner and is not decided here.

## Implementation Notes
New `tools/world_glossary_registry.py` (`add`, `list`, `load_registry()`, `source_problem()`), modelled on `tools/glossary_registry.py`, with the fixed row fields `term`, `description`, `source`, `added`. `load_registry()` refuses a duplicate term. `add` refuses a blank term or description, a `source` outside `docs/mechanics/`, `docs/engine/` and `docs/core/` (the open question is decided: `docs/architecture/` is not allowed, so the wiki points at the law), a path with `..`, a missing file, and an already-registered term; each refusal writes nothing. The module docstring says why the registry stays apart from the dashboard glossary. `registries/world_glossary.jsonl` is committed empty (no seed rows: the descriptions are rpg's).
Route: `registries/world_glossary.jsonl` is added to the rpg domain's `owns` in `registries/session_roles.yaml` (rpg-planner), and `tools/world_glossary_registry.py` to agent-working's; the role cards are regenerated. A first attempt that also added the file to agent-working's `owns_not` and `routes` pushed three u24 cards over their token budget (458, 461 and 458 against 456); the rpg `owns` entry already makes `route` name rpg-planner, so the extra entries were dropped.

## Test Summary
`tests/tools/test_world_glossary_registry.py`: 13 passed (add, load, case-sensitive terms, missing and empty file, duplicate file, re-add refused, four bad sources, blank inputs, CLI exit codes, corpus check that every committed row's source resolves, passing on the empty file). `tests/tools/test_session*.py`: 933 passed. `python3 -m tools.sessions.validate`: OK, 0 findings. `route registries/world_glossary.jsonl` names rpg-planner.

## Files Changed
tools/world_glossary_registry.py, registries/world_glossary.jsonl, registries/session_roles.yaml, .claude/agents/session-*.md (12 regenerated cards), tests/tools/test_world_glossary_registry.py

## Completion Summary
The world-term glossary registry and its tool exist, empty, with a route. Nothing in the dashboard glossary, its module or `src/api/` changed. The terms themselves are for rpg to seed.
