---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261112-A-THROTTLED-CLIENT-THAT-WAITS-OUT-RETRY-AFTER-IS-STILL-REFUSED
phase: done
date: 2026-11-12
tags: [architecture, api-design]
---

# TCK-20261112-A-THROTTLED-CLIENT-THAT-WAITS-OUT-RETRY-AFTER-IS-STILL-REFUSED

## Title
A throttled API client that waits out `Retry-After: 5` is still refused, even after its token bucket has refilled, because admission recovery counts requests instead of elapsed time

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found by platform-planner's option-A stack run on ubuntu (2026-11-12, burst 10:05:55-10:06:31Z), relayed by lead-planner. rpg-planner-ubuntu checked it on origin/main 373625027. Lead confirmed `src/api/admission_control.py` and `docs/architecture/http_admission_control.md` are unchanged at f62d240d0.

Owner decision, logged at #715 6821150788: "A: recovery counts idle time (Recommended)". That comment is also the go to file and dispatch this hotfix under S4. platform-planner reviews.

How it works today (`src/api/admission_control.py`):
- `_consume_token` (:121-128) refills by elapsed wall-clock time, which is correct.
- The mode hysteresis in `_evaluate` (:156-182) and `_can_recover` (:145-153) leaves a mode only after both:
  - `dwell_time_ticks` (10) admission evaluations since the last mode change;
  - `confidence_window_ticks` (5) samples below the recovery limit.
- It steps down one level per recovery. A "tick" is one admission call (docs/architecture/http_admission_control.md §3), so idle time earns no recovery.
- Rejected calls also spend a token (floor 0).
- Only SURVIVAL rejects; the 429 carries a static `Retry-After: 5` (:202-207).

What the replay showed, on 373625027. The probe called `_check_admission` directly with synthetic times, not over HTTP.
- Burst: 420 requests spread evenly over 36 s gave 40 admitted. Platform measured 39. This part is by design and is not changed here.
- Positive control: a client at 1 request/s got 100 of 100 admitted.
- Defect: after the same burst, I left 180 s of idle time, which refills the bucket to 30/30, then sent 1 request every 5 s (honouring Retry-After). The modes came out SSSSDDDDDDDDDDDPPPPP. The first 4 retries got 429, about 20 s of refusals with a full bucket. The client then needed 15 more calls to get from DEGRADED back through PRESSURE.

So `Retry-After: 5` promises something the controller doesn't do, and an idle client is punished for a burst that has fully drained.

The post-burst tail platform saw (first reported as "about 3 minutes later"; platform corrected it from events.txt: the search probe ran at 10:08:41Z, about 2 min 10 s after the burst ended at 10:06:31Z) comes from the same mechanism, not a second one. Checked by rpg-planner-ubuntu from platform's logs_backend.txt, in log order, because the access log has no timestamps:
- After the burst, the last five authenticated requests are `/observability/search/runs` 429, `/search/events` 429, `/search/anomalies` 429, `/search/runs` 429, then `/api/v1/manifest` 200.
- That is the replay's post-idle `SSSS` followed by the first admitted `D`.
- `search.router` is mounted with the same `Depends(require_admission)` as the other REST routers (src/api/server.py:71,74). It shares the one per-key state, so there is no route-class difference.
- The backend log holds 385 429s: the burst's 381 plus these 4.
- The tick-budget warnings and the WatchdogTrip do not feed admission: `_check_admission` reads only the client's own bucket and mode.

`/health` is exempt: `live_health.router` is mounted with no admission dependency (src/api/server.py:108). That matches its 60/60 200s during the burst.

## Scope
1. In `src/api/admission_control.py`, make recovery count idle time. Required behaviour:
   - (a) If a request arrives after a gap of at least `_RETRY_AFTER_SECONDS` since the client's previous evaluation, and the refilled fill ratio is at or below the SURVIVAL recovery limit (`_recovery_limit_for(SURVIVAL)`), the client is admitted, not 429'd.
   - (b) If the bucket has refilled to full (`tokens >= _BUCKET_CAPACITY` after refill, before the consume), the client's hysteresis is reset to NORMAL, with dwell_count 0 and the sample window cleared.
   - (c) A client that keeps sending faster than the refill rate still escalates at once and stays rejected as today. The 420-over-36 s burst replay must admit within ±3 of today's 40.

   Planner check on (a): from 0 tokens, 5 s of refill gives 15 tokens, and after the consume 14 remain, a fill ratio of 0.533. That is below the SURVIVAL limit of 0.8 (1.00 × 0.8), so the 5 s promise can be met without changing the bucket constants.

   Pick the smallest shape that meets (a)-(c) and say why. One example: in `_check_admission`, before `_evaluate`, a gap of at least Retry-After steps SURVIVAL down to DEGRADED with dwell 0, and a full refill resets to NORMAL. Keep the idle logic on the timed path (`_check_admission` / `_consume_token`). Do not put it in `_evaluate`, which stays time-free.
2. Change nothing else:
   - not the bucket constants (30 tokens, 3/s);
   - not `_RETRY_AFTER_SECONDS`;
   - not the ObservabilityController thresholds;
   - not the RuntimeProfile fields or the per-mode behaviour.
3. Tests in tests/api/test_admission_control.py, through `_check_admission` with explicit `current_time`:
   - T1: burst to SURVIVAL, wait 5 s, one request is admitted. Red on the unfixed code.
   - T2: burst to SURVIVAL, wait long enough to refill to full, one request is admitted and the mode is NORMAL. Red on the unfixed code.
   - T3: a client sending 10 requests/s for 30 s stays SURVIVAL after the first escalation, apart from any step-down that (a) allows. State the exact expectation.
   - T4: the 420-over-36 s replay admits 37-43.
   - T5: the 1 request/s positive control admits all. It starts from a new client, a quiet start, and runs at least 300 s. This is platform's paced-client case (≤ 1 req/s on one route).
   - T6: platform asked for `/health` to stay exempt. First check whether an existing test already pins it, for example test_admission_control_covers_every_authenticated_route (:250) or the HTTP-surface characterization. If not, add one through the app: `/health` returns 200 while the same client's key is in SURVIVAL.
   - T7, from platform's run order: the 4-then-admit sequence across two routes. After a burst and an idle gap, requests to `/observability/search/*` and to `/manifest` share one state. Assert the post-fix expectation: the first request after a gap of at least Retry-After is admitted, whichever route it hits.
   `test_recovery_is_gated_by_dwell_and_confidence` (:105-131) must pass unchanged. It drives `_evaluate` directly with no time, and the call-counted rule still holds for a client that never pauses.
4. Docs: update docs/architecture/http_admission_control.md §3 ("Hysteresis") in the same change. Say that idle time counts toward recovery, give rules (a) and (b), and say that `Retry-After` is now a true bound. Update the INFRA-378 parity-ledger entry (docs/parity_ledger/infrastructure.yaml, the "Per-client HTTP admission control" entry) if its text states recovery behaviour, and add the new tests to its `test_path` if that is the ledger's pattern.

## Out of Scope
- The burst rejection counts themselves (by design).
- Computing Retry-After from the controller state (option B, not chosen).
- The tick-budget warnings and WatchdogTrips from the same run. Owner: not ticketed, as VM host noise; perf-planner takes them only if the owner asks.
- WebSocket close-code behaviour, except that `require_admission_ws` inherits the change through `_check_admission`.
- Stale remote branches `http-admission-control` (2026-08-23) and `rpg_core` (2026-03-30), which touch these files but are not active.

## Acceptance Criteria
- AC1: T1, T2 and T7 are red on the unfixed code. T1-T7 are green after the fix. T6 may be an existing test; if so, cite it.
- AC1b: platform-planner's follow-up paced run (≤ 1 req/s on one search route) is recorded in the Completion Summary as a second data point when platform sends it. It is not a blocker.
- AC2: `test_recovery_is_gated_by_dwell_and_confidence` and the rest of tests/api/test_admission_control.py pass unchanged. tests/api/test_server_http_surface_characterization.py passes too, or any diff in it is explained.
- AC3: The bucket constants, `_RETRY_AFTER_SECONDS`, the thresholds and the RuntimeProfile fields are byte-identical.
- AC4: http_admission_control.md §3 and the parity-ledger entry match the code, in the same change.
- AC5: platform-planner has reviewed the diff before the PR opens. Record its reply in the Completion Summary.
- AC6: No world measurement: src/api only, so no simulation path changes. State that in the close.

## Related Tickets
- TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL (done): introduced the controller.
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (done)
- TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE (platform's run that surfaced this)

## Related Docs
- docs/architecture/http_admission_control.md §3
- docs/architecture/http_api_key_authentication.md
- docs/parity_ledger/infrastructure.yaml (INFRA-378)

## Related Stored Artifacts
None. Platform's run evidence reaches origin with platform's work PR: stored_artifacts/TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE/run-2026-11-12/checks_5_burst2_codes.txt.

## Related Code Areas
- src/api/admission_control.py (`_check_admission`, `_consume_token`, `_evaluate`, `_can_recover`, `require_admission*`)
- tests/api/test_admission_control.py

## Assumptions / Open Questions
- Q1 answered by the owner: option A (#715 6821150788).
- The exact mechanism is the implementer's choice within Scope 1(a)-(c). If no small shape meets all three, stop and report rather than widening the scope.

## Implementation Notes
Shape chosen: one helper, `_apply_idle_recovery`, called from `_check_admission` between the token spend and `_evaluate`. `_consume_token` is split into `_refill` (returns whether the bucket reached full) and `_spend_token`; `_consume_token` keeps its signature and calls both. The gap is read from `last_active_time` before it is overwritten (new clients get gap 0).
Why smallest: the only new state is none; both rules need a gap of at least `_RETRY_AFTER_SECONDS`. That gap guard on the full-refill reset (b) is a deliberate narrowing of Scope 1(b): without it, `test_survival_mode_sheds_or_rejects_requests` (a hand-built SURVIVAL state with a default full bucket and no gap) would be reset to NORMAL, and that test must pass unchanged. A real full-refill bucket after a gap shorter than 5 s needs at least 10 s of idle from empty, so the guard changes nothing real. (a) steps SURVIVAL to DEGRADED when the refilled fill ratio is at or below the SURVIVAL recovery limit.
Unchanged: bucket constants, `_RETRY_AFTER_SECONDS`, thresholds, RuntimeProfile, `_evaluate`.

## Test Summary
tests/api/test_admission_control.py gains T1-T7. Red on the unfixed code (src stashed): T1 test_a_client_that_waits_out_retry_after_is_admitted, T2 test_a_client_whose_bucket_refilled_fully_is_back_to_normal, T7 test_the_first_request_after_a_gap_is_admitted_on_any_route (3 failed, 17 passed). Green after the fix: T1-T7 and the 13 existing tests, `test_recovery_is_gated_by_dwell_and_confidence` unchanged. T3 (10 req/s for 30 s) stays SURVIVAL after the first escalation, no step-down. T4 burst replay admits within 37-43. T5 is a new client at 1 req/s for 300 s, all admitted. T6: the existing test_admission_control_covers_every_authenticated_route pins /health as the only route with neither dependency; added a behavioural test, /health 200 while the key is in SURVIVAL. T2 reads dwell_count 1 after the reset because the call's own evaluation counts one.
Run: tests/api/test_admission_control.py + test_server_http_surface_characterization.py + test_all_routes_require_auth.py: 25 passed. `codebase.health`: OK, 0 worse.

## Files Changed
src/api/admission_control.py; tests/api/test_admission_control.py; docs/architecture/http_admission_control.md (section 3); docs/parity_ledger/infrastructure.yaml (INFRA-378, via parity_ledger_writer); this ticket.

## Completion Summary
Done. A client that waits out Retry-After is admitted, and a refilled client returns to NORMAL; a hammering client stays rejected.
AC6: no world measurement, src/api only, no simulation path changes.
AC5: platform-planner review of the diff is pending; the reply is to be recorded here. AC1b data point, relayed by rpg-planner-ubuntu, who checked the raw files: platform run A, 2026-11-12 10:30:13-10:32:48Z, image 4613dfdaefb5 (pre-fix code). After 12 s with no traffic, 150 requests at 1 req/s to /api/v1/observability/search/runs from one key gave 150 x 200 and 0 x 429 (checks_2_traffic_codes.txt; logs_backend.txt has 151 search/runs 200 and no 429). Evidence: agent-working/stored_artifacts/TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF/run-2026-11-12-runA/ on platform-implementer-local-loki-volume-and-api-dashboard; it reaches origin with platform's PR. This matches T5 on the unfixed code: a paced client was never affected, and the fix keeps that.
Not run: the full CI shard jobs and tests/architecture. Known gap: the narrowing of rule (b) by the gap guard, described in Implementation Notes.
