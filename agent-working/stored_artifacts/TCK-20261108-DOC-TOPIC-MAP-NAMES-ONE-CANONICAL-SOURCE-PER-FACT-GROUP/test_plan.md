---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP
tags: []
---

# test_plan - TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP

- `python3 tools/validate_frontmatter.py --content-type doc docs/architecture/doc_topic_map.md` reports no violations.
- `pytest -m "not slow" tests/docs` passes. This covers path existence and doc integrity.
- Every relative Markdown link in the page resolves (a shell loop over the `](...)` targets).
- Acceptance check by reading the page:
  - every row has exactly one canonical doc and a normative level;
  - no history doc is canonical;
  - verification status is never "verified".
- No code tests: the ticket changes docs only.
