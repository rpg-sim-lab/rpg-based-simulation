---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY
artifact_type: test_plan
tags: [documentation, reference]
---

# Test plan: TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY

Normal: add appends one valid row; load returns term-keyed rows; case-sensitive terms are distinct.
Edge: missing file and empty file load as {}.
Failure: duplicate term in the file raises; re-adding writes nothing; blank term or description; source outside the three roots, containing `..`, or absent; CLI exits 1 each time and writes nothing.
Regression/corpus: every committed row's source resolves (passes on the empty file).
Routing: `tools.sessions.validate` clean, `tests/tools/test_session*.py` (budget and drift tests), `route registries/world_glossary.jsonl`.
