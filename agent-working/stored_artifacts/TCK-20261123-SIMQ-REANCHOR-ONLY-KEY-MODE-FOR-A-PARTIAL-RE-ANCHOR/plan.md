---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261123-SIMQ-REANCHOR-ONLY-KEY-MODE-FOR-A-PARTIAL-RE-ANCHOR
phase: done
date: 2026-11-23
tags: []
---

# plan - TCK-20261123-SIMQ-REANCHOR-ONLY-KEY-MODE-FOR-A-PARTIAL-RE-ANCHOR

Small change, so the artifacts are short. Add `only` to `reanchor` and `--only` to the CLI; validate named keys and exclusions first, then copy unnamed keys unchanged inside the existing loop. No pair-identity change. Docs: module docstring and policy rule 7.
