---
content_type: doc
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, governance]
---

# Held prose-reading sample: draw and protocol

From agent-working-designer's docs-truth hand-off, 2026-11-16, section 3, verbatim below. Held by lead-planner on 2026-11-16, and not started. The owner has not decided whether to read the sample (`docs_truth_plan.md` section 7).

## The held prose-reading sample: draw and protocol (to start when balance/foundation work settles)

Population: the 92 tracked markdown files under `docs/mechanics/` and `docs/engine/` (any depth), excluding the knowledge-gateway set and README files. Draw: Python `random.Random(20261116).sample(sorted(files), 10)`. The draw on db6b4579d:
- docs/engine/architecture_reference.md
- docs/engine/contracts/regression_and_verification.md
- docs/engine/contracts/replay_contract.md
- docs/engine/deterministic_execution.md
- docs/engine/engineering_playbook_m10.md
- docs/engine/matrices/full_certification_test_matrix.md
- docs/engine/matrices/signal_truth_test_matrix.md
- docs/engine/project_lawbook_m10.md
- docs/mechanics/04_strategic_cognition.md
- docs/mechanics/05_world_evolution.md
Redraw if the population changes by more than a few files before the sample starts, with the same seed and the new commit recorded. The draw is skewed to `docs/engine` (the engine set is larger); if the owner wants all seven Bible chapters covered, read the three mechanics chapters not drawn instead of redrawing.

Protocol, per document (one reader, rpg-designer; about one hour each is an estimate, not a measurement):
1. Pick up to 5 checkable claims about code that still exists: an ordering (phase A before B), a rule (X is capped at N), a condition (Y only when Z), a default. Skip claims about intent or history.
2. For each claim, find the file the document cites (or the file graphify/search_docs points to) and check it. Record: document, claim as written, file and symbol checked, verdict (true, false, cannot tell), and a one-line reason.
3. A false claim is reported with the correct behaviour. Do not fix the document in the same pass; the fix is a normal change.
4. Positive control: include one claim from each document chosen to be knowably false by editing a copy (a swapped number) to confirm the reader catches it; discard the control from the results.
5. Report: claims checked, true/false/cannot-tell counts, per document, and the false claims in full. State plainly that 10 documents is a sample, not an audit, and name the population.

Owner of the content: rpg-designer reads; I hold no opinion on whether the claims are true; agent-working draws and tabulates only.
