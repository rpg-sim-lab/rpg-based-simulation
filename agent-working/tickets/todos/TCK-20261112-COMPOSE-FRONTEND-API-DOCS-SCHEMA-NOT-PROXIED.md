---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-COMPOSE-FRONTEND-API-DOCS-SCHEMA-NOT-PROXIED
phase: open
date: 2026-11-12
tags: [platform]
---

# TCK-20261112-COMPOSE-FRONTEND-API-DOCS-SCHEMA-NOT-PROXIED

## Title
In the compose frontend, the API docs page's /openapi.json fetch gets index.html, because nginx proxies only /api/

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found by rpg-planner-ubuntu on 2026-11-12, read from code on main 5090cccfc and not observed live.
- `frontend/src/components/ApiDocsPage.tsx` (about l.456) fetches `/openapi.json`.
- FastAPI serves the schema at its default `openapi_url`, `/openapi.json`, at the backend root (`src/api/server.py`, `FastAPI(...)` with no `openapi_url`).
- `docker/nginx.conf` proxies only `location /api/`. `location /` does `try_files $uri $uri/ /index.html`, so in the compose image the schema request returns the SPA's index.html, and the docs page's schema load likely fails.

## Scope
- First observe it: in the next stack run that already has a slot (TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY's proof), request `/openapi.json` through the frontend port and record the content type.
- If confirmed, add `location = /openapi.json { proxy_pass http://backend:8000; }` to docker/nginx.conf, using the same proxy headers as `/api/`. It must not inject the API key header unless the backend requires a key for that path; check `src/api/auth.py` for whether /openapi.json is authenticated.
- No frontend change (rpg-planner-ubuntu: the fetch path is fine).

## Out of Scope
- Moving the schema under /api/ (that's a backend change, rpg's).

## Acceptance Criteria
- Through the frontend port, `/openapi.json` returns `application/json` and the API docs page loads its schema (observed).

## Related Tickets
- TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY (same file, same proof run).

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
docker/nginx.conf
frontend/src/components/ApiDocsPage.tsx

## Assumptions / Open Questions
- Not yet observed live; the code reading is rpg-planner-ubuntu's.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
