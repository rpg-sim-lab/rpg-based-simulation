---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS
artifact_type: investigation
tags: [agent-monitoring, data-quality]
---

# Investigation — retro readers select tool rows by ts

## Verified in code (origin/main cefa99b07)
- `generate_retro.py` main(): `--days` (≈:2341) and the week path (≈:2350) set `tools = [t for t in all_tools if t.get("run_id") in run_ids]`. Tool rows have had `run_id` null since W42 (adhoc-null attribution), so `tools` is `[]` for any W42+ period. `--all` uses `all_tools` unfiltered and is unaffected.
- `_update_index` (≈:2461) filters `week_tools` the same way for each retro file's trend row.
- Rows have `ts` on every row (W44 12,821/12,821; W45 shard rows all carry ts); `iso_week(ts)` and `_record_since_cutoff(ts, cutoff)` already exist (:161, :169).
- Per-run joins (≈:1342-1348, `run_ids_with_build_calls`) legitimately need `run_id` and stay as is.

## Delivery-cost: the draft's premise does not hold
`tools/delivery/delivery_cost_measurement.py` does NOT select by run_id. `bcm.load_tools_rows` / `load_tools_rows_from_ref` pick rows by the **shard directory's week**, and `build_gh_call_report` counts `Bash` rows whose head is `gh`. Measured on this worktree: W44 = 492 gh calls (1 `gh pr create`), W45 = 66 (0 `gh pr create`). So it does count; no code change belongs here. Its uncheckable state comes from `gh pr create` rows being rare in committed shards (the README row's own 10-06/10-20 notes: tool sees only committed shards, hand closes), a coverage matter that ts selection would not change. Consequence for the ticket: scope item 3 becomes "traced, no change; README note says why". Reported to the planner/designer.

## Rows without ts
Counted and returned by the helper (`missing_ts`); the retro prints one line when non-zero.
