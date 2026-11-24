---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261118-CPU-STEAL-AND-SWAP-COUNTERS-IN-EVERY-TIMING-RECORD
artifact_type: test_plan
phase: done
date: 2026-11-18
tags: [performance]
---

# Test plan

Unit tests only, no timing run (heavy slot held): steal reader parse and unreadable cases; pinned steal delta with zero swap recorded; warning above the limit without voiding; unpinned run over every CPU; swap move still raises with the pages in `fields`; `cmd_record` gate entries carry the fields. Command: `pytest tests/perf tests/unit/perf -m "not slow" -k "quiet or rerun"`. mypy on the two touched modules.
