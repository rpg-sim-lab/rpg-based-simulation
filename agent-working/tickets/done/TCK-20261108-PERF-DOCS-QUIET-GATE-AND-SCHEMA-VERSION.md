---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261108-PERF-DOCS-QUIET-GATE-AND-SCHEMA-VERSION
phase: done
date: 2026-11-08
tags: [performance]
---

# TCK-20261108-PERF-DOCS-QUIET-GATE-AND-SCHEMA-VERSION

## Title
Document the re-record quiet window and correct the schema version in the baseline policy

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Two items from the owner-approved docs-as-review-source plan (#715 6720445592, items 7a and 7b), relayed by lead-planner. The owner chose to ship them now in their own PR, exempt from the perf pause (#715 6721187493, which also records the owner's P1 approval of the 7b correction).
- 7a: no doc covered the re-record quiet window of `tools/perf/quiet_gate.py` and `rerun_baselines.py record`'s `--wait-s` and `--max-probe-ms` (shipped in #806).
- 7b: `docs/performance/perf_baseline_policy.md:15` and `:44` said schema 1.0; `benchmark_record.SCHEMA_VERSION` is 1.5.

## Scope
- `docs/performance/perf_baseline_policy.md`: correct both schema mentions to 1.5; add §2.2 describing the quiet window and the in-run checks as the code implements them; replace §2.1's stale quiet-window sentence (it said 2.5 GB and load only) with a pointer to §2.2.

## Out of Scope
- Any code, test or threshold change. §2.2 describes working rules; it does not make them contract values or owner rulings.
- `docs/performance/benchmark_identity_schema.md` §3.2's JSON Schema draft, still titled schema 1.0 and `$id` `benchmark-result-v1.0`: it is a separately labelled draft, and whether to update or retire it is not part of 7b. Noted here as a finding only.
- Historical schema mentions (`baseline_invalidation_ledger.md` 1.3, `tick_cost_growth.md` 1.2) are dated statements and stay.

## Acceptance Criteria
- [x] `perf_baseline_policy.md` names schema 1.5 at both former 1.0 sites.
- [x] §2.2 states the pre-run checks per pinned and unpinned run, `--wait-s` (default 900 s, 0 checks once), `--max-probe-ms` (pinned only, off by default), the in-run foreign-share, swap and own-scope checks, the virtualenv guard, what `summary.json` records, and the pinned command, each matching `tools/perf/quiet_gate.py` and `tools/perf/rerun_baselines.py` at origin/main 297494469.
- [x] §2.1 no longer states the superseded 2.5 GB / load-only window.

## Related Tickets
- TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES (shipped the gate, #806)
- TCK-20261101-PERF-V0002-RECORD-AFTER-FINDING-WHAT-MOVES-HOST-SPEED (paused; it will use these rules)

## Related Docs
- docs/performance/perf_baseline_policy.md
- docs/performance/benchmark_identity_schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/perf/quiet_gate.py
- tools/perf/rerun_baselines.py

## Assumptions / Open Questions
- The section's values were read from code, not from a run: `SAMPLE_S` 5.0, `MAX_PINNED_BUSY_PCT` 10.0, `MAX_FOREIGN_SHARE` 0.10, `SCOPE_PATTERN` `run-*.scope`, `MAX_LOAD_1MIN` 1.5, `MIN_AVAILABLE_MB` 3000.0, `QUIET_WAIT_S` 900.0.

## Implementation Notes
Doc-only. Each statement in §2.2 was checked against the source lines named above.

## Test Summary
Doc-only change; no behaviour changed. Ran the frontmatter validator on the ticket and the doc, and the registry drift test (`tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`).

## Files Changed
- docs/performance/perf_baseline_policy.md
- docs/REGISTRY.yaml (regenerated)

## Completion Summary
Both items done as scoped. Known gap: the schema doc's §3.2 JSON Schema draft still says 1.0 (out of scope, noted above).
