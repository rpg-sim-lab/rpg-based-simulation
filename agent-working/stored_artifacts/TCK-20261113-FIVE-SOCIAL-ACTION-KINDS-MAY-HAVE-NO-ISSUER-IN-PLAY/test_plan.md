---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY
artifact_type: test_plan
tags: []
---

# Test plan

Read-only measurement; nothing in src, data or config changes. The spy and any probe live in the stored artifacts' evidence, not in src. Acceptance: a per-kind path map with file:line (investigation.md section 2); per-kind counts from a designer-approved, hash-matched spy for the kinds the read leaves open; rpg-designer's ruling per kind; Scope 4 answered (investigation.md sections 5 and 6). Checks: spy final hash equals the PLAIN twin per world (exit 3 on mismatch = STOP); done_checker_static; mechanism advisory; generate_registry --check; frontmatter validators.

## Proof Plan

- Level: read-only code read (no execution); docs and ledger checks for the correction.
- Proof kind: static code read with file:line, a designer-ruled grep over data/content/worldassembly/worldbuilding/certification/config for file-payload issuers, and validators on the edited docs.
- Oracle source: the code on origin/main 4dc2c82cb; rpg-designer's per-kind ruling (2026-11-13, session message, saved at /mnt/data2/rpg-measure/briefs/five-kinds-docs-ruling.md).
- Expected effect: each of the six kinds has no issuer in play; the ledger entries stay verified with a support_boundary; the Bible states the current play; the wrong SOC-268 cross-reference reads SOC-272.
- Selected commands: `make parity-ledger-schema-check`; `python3 tools/validate_frontmatter.py` on each edited doc; `python3 tools/generate_registry.py --check`; `pytest tests/docs -n 1`.
