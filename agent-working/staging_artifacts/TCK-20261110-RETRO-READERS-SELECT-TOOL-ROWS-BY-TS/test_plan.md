---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS
artifact_type: test_plan
tags: [agent-monitoring, data-quality]
---

# Test plan (tests/tools/test_generate_retro.py or a new test_retro_tool_rows_by_ts.py)

- `tools_in_period`: week selects by ts with null run_id; cutoff window likewise; rows without/garbled ts are returned as `missing_ts`, not included.
- main() week path over a tmp data dir with null-run_id tool rows: search/raw-read/skill sections non-zero (AC1).
- Trend row for a `YYYY-Www` retro file with null-run_id rows is non-zero; `ALL` unchanged.
- Per-run parity section over null-run_id rows prints the not-attributable line (AC2).
- Delivery cost: fixture shard with null-run_id `gh` Bash rows counts them (AC3).
- Missing-ts count appears in the output (AC4).
Run: `pytest tests/tools/ -k "retro or delivery_cost" -q` plus the named new file, no -n.
