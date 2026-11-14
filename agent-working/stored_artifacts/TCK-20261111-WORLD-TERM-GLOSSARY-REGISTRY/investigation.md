---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY
artifact_type: investigation
tags: [documentation, reference]
---

# Investigation: TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY

- `tools/glossary_registry.py` is the template; its rows carry `category` and `added_date`, which the wiki does not use. The new rows use `added` and `source` as the ticket fixes.
- `registries/world_glossary.jsonl` matched no `owns` glob (`route` said unowned); the tool path was also unowned, and `tools/` ownership is a list of single files.
- Role cards have a token budget (456 for the u24 cards). A first route design that also named the file under agent-working's `owns_not`/`routes` pushed three u24 cards to 458, 461 and 458. Putting the file under the rpg domain's `owns` alone makes `route` name rpg-planner and costs a count change only.
- `tools.sessions.validate` reports `glob-matches-nothing` for an `owns` entry whose file does not exist, so the empty registry file is committed.
