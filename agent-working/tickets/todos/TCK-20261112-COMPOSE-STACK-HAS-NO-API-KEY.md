---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY
phase: open
date: 2026-11-12
tags: [platform, security]
---

# TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY

## Title
The compose stack configures no API key, so every backend route except /health answers 401

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
In the 2026-11-12 proof run (`docs/runbooks/records/2026-11-12-loki-volume-and-api-dashboard.md`), the first burst
against the compose backend got 401 on every route except `/health`. The backend fail-closes when `api_key_hashes` is
empty (`docs/architecture/http_api_key_authentication.md` §1), and `compose.yaml` passes none: no
`RPG_API_KEY_HASHES` env and no `--api-key-hashes`. `make dev` passes a fixed dev-only pair (Makefile, §6), but the
compose path has nothing. So the stack's own frontend (an nginx build of the SPA) and any scripted client cannot reach
the API. The run worked around it with a run-only override outside the repo, setting `RPG_API_KEY_HASHES` to the
committed dev pair.

## Scope
1. Decide how a compose user supplies keys, weighing:
   - pass-through `RPG_API_KEY_HASHES=${RPG_API_KEY_HASHES:-}` on the backend, empty by default (still
     fail-closed), with the runbook naming how to set it;
   - a compose secret file (like `docker/secrets/`), read by the backend;
   - defaulting to the committed dev pair. This is likely rejected: a known key on by default, with the backend port
     published on all host interfaces (`${BACKEND_PORT:-8000}:8000`).
2. How the compose frontend sends the key. It is a static build, so `VITE_API_KEY` is fixed at build time. That needs
   a decision with lead-planner and the frontend owner (rpg), because it touches `frontend/**` and
   `docker/frontend.Dockerfile`.
3. A runbook section and a proof that a compose start with a configured key answers 200 on a read route and 401
   without one.

## Out of Scope
- Production key provisioning (unbuilt; the auth doc §6).
- Changing the auth code in `src/api/auth.py` (rpg's).

## Acceptance Criteria
- A compose user can set a key without editing tracked files, and the default stays fail-closed (validated).
- A stack run shows 200 with the key and 401 without it (observed).
- Secrets never land on argv or in committed files (validated: a scan by counts).

## Related Tickets
- TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE and TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF (where it was found).
- TCK-20260823-HTTP-API-KEY-AUTH, TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX (done; the auth design and the `make dev` key).

## Related Docs
docs/architecture/http_api_key_authentication.md
docs/runbooks/records/2026-11-12-loki-volume-and-api-dashboard.md

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE/run-2026-11-12/

## Related Code Areas
compose.yaml
docker/frontend.Dockerfile
src/config/loader.py

## Assumptions / Open Questions
- Standard tier, because it is a security-relevant design choice and has a cross-domain part (the frontend). It is
  not dispatched; it needs the owner's yes.
- Owner dispatch yes, 2026-11-12 (#715 6828616413). The frontend half goes to rpg-planner-ubuntu as a question, not as
  work. The committed dev pair stays dev-only, and no real secret goes into git.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
