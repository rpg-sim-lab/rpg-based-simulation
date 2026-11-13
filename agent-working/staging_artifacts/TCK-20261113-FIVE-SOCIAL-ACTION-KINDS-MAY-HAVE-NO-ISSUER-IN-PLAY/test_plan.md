---
status: active
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY
artifact_type: test_plan
tags: []
---

# Test plan

Read-only measurement; nothing in src, data or config changes. The spy and any probe live in the stored artifacts' evidence, not in src. Acceptance: a per-kind path map with file:line (investigation.md section 2); per-kind counts from a designer-approved, hash-matched spy for the kinds the read leaves open; rpg-designer's ruling per kind; Scope 4 answered (investigation.md sections 5 and 6). Checks: spy final hash equals the PLAIN twin per world (exit 3 on mismatch = STOP); done_checker_static; mechanism advisory; generate_registry --check; frontmatter validators.
