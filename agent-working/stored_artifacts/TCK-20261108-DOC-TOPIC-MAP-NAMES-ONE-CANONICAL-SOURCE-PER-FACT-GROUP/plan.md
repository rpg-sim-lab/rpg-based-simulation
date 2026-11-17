---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP
tags: []
---

# plan - TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP

1. Write `docs/architecture/doc_topic_map.md`:
   - the precedence section (plan "Normative sources");
   - the verification-status rule (unverified until the P1 fields exist; derived, never typed);
   - the map, grouped as engine, API and observability, world and content, mechanics, and process;
   - a known-conflicts table (C1-C6), each with its evidence and owner;
   - a "Not covered" list.
2. Don't fix the satellites or the conflicts here. They go to their owners as findings (rpg: C1, C2, C3 doc, C5, C6; agent-working: C3 skill files, C4).
3. Check the frontmatter, the docs tests, that every relative link resolves, then `make docs-registry` and `make knowledge-index-update`.
