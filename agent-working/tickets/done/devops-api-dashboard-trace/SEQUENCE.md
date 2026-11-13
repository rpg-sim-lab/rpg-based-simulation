# Implementation Sequence: devops-api-dashboard-trace

Written by hand. Split out of the closed epic `TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL` (done/devops-step2-observability-local) on 2026-10-27.

## Order

1. TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF: unblocked 2026-11-12 (R3 merged as #891). It runs after
   TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE (todos/), in one batch with one proof run (owner, option A,
   #715 6819928388).

## Unblock condition

R3 is on origin/main (`opentelemetry` set up in `src/api/`, plus a test that `src/engine/**` imports none of it).
Until then, platform-planner doesn't dispatch this ticket. Once R3 lands, it runs as a single-ticket batch from a
`platform-implementer-local-*` branch, and the stack run is cleared with lead-planner first.
