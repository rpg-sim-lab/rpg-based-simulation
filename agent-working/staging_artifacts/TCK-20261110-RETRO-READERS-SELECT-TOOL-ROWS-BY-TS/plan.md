---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS
artifact_type: plan
tags: [agent-monitoring, data-quality]
---

# Plan

1. `tools/agent-monitoring/generate_retro.py`: add `tools_in_period(all_tools, week=None, cutoff=None) -> (rows, missing_ts)` next to `iso_week`. Week: `iso_week(ts) == week`; cutoff: `_record_since_cutoff(ts, cutoff)`; rows with no usable ts excluded and counted.
2. Use it at the `--days` and week sites in main(), and in `_update_index` for per-week trend rows (a retro file named `YYYY-Www` -> by ts; `ALL` and any other name keep current behaviour). Print one note line when `missing_ts` > 0.
3. Per-run sections over null-run_id data: in the parity-index per-run join, when tool rows exist but none carries a run_id, print "not attributable since W42 (adhoc-null attribution)" rather than 0.
4. Delivery-cost: no code change (see investigation). Add a regression test pinning that gh counts come from shard-week rows with null run_id.
5. README: one note that W42+ retros change tool numbers on regeneration; published retros are not rewritten.

Simpler-fix check (6698958617): ts selection is the simplest fix; re-attributing run_id needs a hook change and leaves history empty. Leaves out per-run tool attribution (named in the output).
Scoped tests only, no -n.
