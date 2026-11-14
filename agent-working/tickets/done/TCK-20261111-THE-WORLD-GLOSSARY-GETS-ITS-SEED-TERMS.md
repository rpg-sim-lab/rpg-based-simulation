---
status: historical
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20261111-THE-WORLD-GLOSSARY-GETS-ITS-SEED-TERMS
phase: done
date: 2026-11-11
tags: []
---

# TCK-20261111-THE-WORLD-GLOSSARY-GETS-ITS-SEED-TERMS

## Title
The world glossary gets its 49 seed terms

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Dispatch from rpg-planner (lane A). Seed `registries/world_glossary.jsonl` (created empty by #868) with the world terms a wiki reader meets. Authority: the owner's #845 decision (#715 6789779149).

## Scope
49 rows added through `python3 tools/world_glossary_registry.py add` only, from a draft the planner reviewed in full (the file is append-only).

## Out of Scope
Any edit to `tools/world_glossary_registry.py`; any change to the laws the rows summarise.

## Acceptance Criteria
- 49 rows, each with a plain one-or-two-sentence description, and a source that is an existing file under docs/mechanics, docs/engine or docs/core (anchor only where it matches a heading).
- Descriptions hold in current play; where law and play differ, the row says so.
- The tool's own tests pass.

## Related Tickets
TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY (the tool).

## Related Docs
docs/mechanics/01..07, docs/engine/kernel.md, docs/core/entities.md.

## Related Stored Artifacts
None.

## Related Code Areas
registries/world_glossary.jsonl

## Assumptions / Open Questions
None open.

## Implementation Notes
Draft written to /mnt/data2/rpg-measure/glossary/draft.tsv; planner review changed 10 rows (Recruitment, Guild, Free swing, Tick, Contract, Trust, Regional trauma, Cohort cycle, Party, Death) and then approved. The adds ran from that exact file, in order, with no wording change. 15 terms carry a file-only source because their headings do not make a clean anchor.

## Test Summary
`pytest tests/tools/test_world_glossary_registry.py -n1`: 14 passed. `world_glossary_registry.py list`: 49 rows; the jsonl has 49 lines.

## Files Changed
registries/world_glossary.jsonl; this ticket; monitoring shards; docs/REGISTRY.yaml.

## Completion Summary
49 seed terms added. Draft sha256 4e77cc0161e17ad26fab497807fac1d25b63bbe2d3c2cebc47ee89dc2e8b22ee (49 terms), approved by rpg-planner at that sha.
