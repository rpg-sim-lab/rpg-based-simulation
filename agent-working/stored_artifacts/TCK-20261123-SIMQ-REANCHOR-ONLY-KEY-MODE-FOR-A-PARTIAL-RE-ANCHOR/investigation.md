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

# investigation - TCK-20261123-SIMQ-REANCHOR-ONLY-KEY-MODE-FOR-A-PARTIAL-RE-ANCHOR

reanchor looped over every fixture key and called audit_values, so a key with no rows refused. Unnamed keys can be copied as the same object: dump_fixture preserves order and layout, so the bytes are identical. Splicing earlier rows was rejected by the owner path (mixes shas).
