---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS
phase: open
date: 2026-11-10
tags: [agent-monitoring, data-quality]
---

# TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS

## Title
The retro and delivery-cost readers pick a period's tool rows by `run_id`, which has been null on every tool row since W42, so every tool-based section is empty

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by lead-planner-u24 in the owner-requested deep retro (RETRO-2026-W45 Notes, anomaly 1), drafted by
agent-working-designer-u24 (main checkout `.claude/handover/drafts/retro-readers-join-on-a-null-run-id-2026-11-10.md`,
item 1). Owner go: #715 6764924407 (A), "File + dispatch now".

Tool rows carry `ts` and `session_id` on every row, but `run_id` is null on all of them since W42 (W44: 0 of 12,821; W45: 0
of 2,676). That is by design (TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION). The readers didn't follow:
`tools/agent-monitoring/generate_retro.py` main() selects `tools = [t for t in all_tools if t.get("run_id") in run_ids]` for
the `--days` and week paths (~:2341, ~:2350), and the trend table does the same (~:2462, `week_tools`). Each returns an
empty list, so search and raw-read counts, Parity Index read-path usage ("0/0 Bash rows scanned") and skill usage are all
empty. `tools/delivery/` delivery-cost measurement sees 0 gh calls for W44-W46 (README watchlist, DELIVERY-COST row), so
that watchlist row has been uncheckable since 10-06.

## Scope
1. One shared helper, `tools_in_period(all_tools, week=None, cutoff=None)`, selecting tool rows by their own `ts`
   (`iso_week(ts) == week` or `_record_since_cutoff(ts, cutoff)`). Rows without `ts` are counted and reported, not guessed.
2. Use it at the three generate_retro sites (week, `--days`, trend table).
3. Trace the delivery-cost gh-call count's tool-row selection (not yet traced by the designer) and switch it to the same
   rule. If delivery imports from agent-monitoring, put the helper in a small shared module.
4. Per-run joins (tool calls per run or ticket, e.g. ~:1348) keep using run_id. Where they come out empty for null-run_id
   rows, the section prints "not attributable since W42 (adhoc-null attribution)" instead of 0.
5. README note: retros generated from W42 on change their tool numbers on regeneration; published retros are not rewritten.

## Out of Scope
- Re-attributing tool rows to runs (adhoc-null stays by design).
- Regenerating or rewriting any published retro. RETRO-2026-W45/W46 ride the Makefile PR as lead wrote them and are not
  regenerated (#715 6764924407 (B)).
- The validator index check and the week-close sweep (sibling tickets in this batch).

## Acceptance Criteria
1. A week whose tool rows have null run_id gets them by ts; a `--days` window likewise; the trend-table row for such a
   week is non-zero.
2. A per-run section over null-run_id rows prints the not-attributable line, not 0.
3. A delivery-cost fixture with null-run_id tool rows counts its gh calls.
4. Rows without ts are counted in the output, not dropped silently.
5. Scoped tests only: `pytest tests/tools/ -k "retro or delivery_cost" -q` (or the named files). No pytest -n>1 and no broad
   suites while lane C's hit-wake measurement runs (owner load rule, 6764924407).
6. Staging artifacts plan.md, investigation.md, test_plan.md; agent-working-designer-u24 reviews the plan before code.

## Related Tickets
- TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION (done; why run_id is null)
- TCK-20260924-DELIVERY-COST-MEASUREMENT (done; watchlist row)
- TCK-20261110-MONITORING-VALIDATE-WARNS-ON-A-STALE-INDEX, TCK-20261110-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-NON-TOOL-SHARDS (same batch)

## Related Docs
- docs/agent-monitoring/README.md (watchlist, DELIVERY-COST row)

## Related Stored Artifacts
- Designer draft (main checkout): `.claude/handover/drafts/retro-readers-join-on-a-null-run-id-2026-11-10.md`

## Related Code Areas
- tools/agent-monitoring/generate_retro.py, tools/delivery/ (delivery-cost measurement), tests/tools/

## Assumptions / Open Questions
- Simpler-fix check (6698958617): selecting by ts is the simplest fix that restores the period sections; re-attributing
  run_id would cost a hook change and still leave history empty. No measurement runs. Leaves out per-run tool attribution.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
