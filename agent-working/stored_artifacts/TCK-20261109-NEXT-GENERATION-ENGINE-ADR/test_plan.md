---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ADR
tags: []
---

# test_plan - TCK-20261109-NEXT-GENERATION-ENGINE-ADR

This ticket changes docs only. No behaviour changes, so no simulation tests apply.

Checks:
- `python3 tools/validate_frontmatter.py` on the ADR and these artifacts;
- `python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20261109-NEXT-GENERATION-ENGINE-ADR`;
- `pytest tests/tools -q -k "registry or frontmatter or doc"` after `make docs-registry`;
- reading: every proposal-tense phrase in the ADR is gone, and the system_overview paragraph is worded as a direction ("will";
  "until a stage lands, the serial fold ... is the only executor") so it does not claim unbuilt behaviour.
