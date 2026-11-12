---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY
phase: inprogress
date: 2026-11-12
tags: [platform, security]
---

# TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY

## Title
The compose stack configures no API key, so every backend route except /health answers 401

## Status
INPROGRESS

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
Status 2026-11-12: implemented statically, proof run pending. Plan approved by platform-planner (artifacts under `agent-working/staging_artifacts/TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY/`).
- **Backend:** `compose.yaml` loads the optional, gitignored `docker/secrets/backend.env` with `env_file` (`required: false`): it carries `RPG_API_KEY_HASHES=local:<sha256 of the raw key>` and nothing else, so the backend never holds the raw key. With the file absent nothing is set and the backend stays fail-closed (401 on every route except `/health`).
- **Frontend (rpg-planner-ubuntu's answer: nginx adds the header, no frontend change):** `docker/nginx-api-key.conf.template` (one line: `proxy_set_header X-API-Key "${FRONTEND_API_KEY}";`) is rendered at container start by the base image's entrypoint into `/tmp/api-key.conf` (`NGINX_ENVSUBST_OUTPUT_DIR=/tmp`, `NGINX_ENVSUBST_FILTER=^FRONTEND_API_KEY`, set in `docker/frontend.Dockerfile`); `docker/nginx.conf` stays static and includes it inside `location /api/` (an explicit include, so a missing file stops nginx at start). An empty value renders `proxy_set_header X-API-Key "";`, which sends no header. The frontend loads the tracked `docker/frontend.defaults.env` (`FRONTEND_API_KEY=`, empty) first and the optional gitignored `docker/secrets/frontend.env` (the raw key, nothing else) last, so the variable is always defined: an undefined one would leave `${FRONTEND_API_KEY}` in the rendered file and nginx would refuse to start.
- **Not the repo-root `.env`:** `.mcp.json` runs the GitHub MCP server with `--env-file .env`, so the root `.env` is passed wholesale into that container and already holds its credentials; the API key pair has its own files under `docker/secrets/` (lead confirmed the directory; platform-planner decided the split into `backend.env` and `frontend.env`). `.env` was not opened.
- **Binding:** `backend` and `frontend` publish on `127.0.0.1` by default (`BACKEND_BIND`, `FRONTEND_BIND` override), because nginx is now the authentication boundary (anyone who can reach the frontend port is authenticated as that key).
- **Settled from upstream source (read 2026-11-12, no container started):** the nginx-unprivileged entrypoint runs the templates step as uid 101 and honours `NGINX_ENVSUBST_OUTPUT_DIR`; it does not create the output directory (hence `/tmp`) and prints paths, not values. The read was of branch `main` (nginx 1.31.8): the tag `1.31.7` returned 404. The proof run confirms it on the pinned image.
- **Runbook:** `docs/runbooks/compose-api-key.md` (owner-run recipe with a `git check-ignore` guard and `noclobber`, how to check it without a key on argv, what shows the raw key, who loses access to loopback, one key means one admission bucket, rotation). `.dockerignore` now lists `.env` and `docker/secrets/`.
- **Found and fixed:** a single shared file would have put the raw key into the backend container's environment too (the static check showed it); platform-planner decided to split, so each service loads only its own file.
- **`/openapi.json`** (the folded-in hotfix `TCK-20261112-COMPOSE-FRONTEND-API-DOCS-SCHEMA-NOT-PROXIED`): not changed yet; the proof run observes it first, then the location is added.
- Not touched: `src/**`, `frontend/**`, `tests/**`, `website/**`.

## Test Summary
- **validated (static, no stack):** `docker compose config` with neither `backend.env` nor `frontend.env`: the backend has no `RPG_API_KEY_HASHES` (fail-closed) and the frontend's `FRONTEND_API_KEY` is defined and empty; with a throwaway pair in a scratch env file outside `docker/secrets/` (a scratch copy of `compose.yaml`), the backend hash equals sha256 of the generated key and the frontend key equals it (the later file wins over the empty default); both services publish on `127.0.0.1`. No added diff line and no new file carries a 32+ hex string; the template has exactly one `${FRONTEND_API_KEY}`; `nginx.conf` has no env-style `${...}`; the Dockerfile `ENV` lines hold no secret. `git check-ignore -q` exits 0 for `docker/secrets/backend.env` and `docker/secrets/frontend.env`; `docker/frontend.defaults.env` is not ignored; the backend environment has no `FRONTEND_API_KEY` and the frontend environment has no `RPG_API_KEY_HASHES`. Paths guard, REGISTRY no-drift, repo-root allowlist and compose-hygiene tests pass (19).
- **to be observed in the proof run (heavy: needs a frontend image build, a slot ask):** fail-closed default (401 on the backend port and through the frontend, `/health` 200); the templates step on the pinned image; with a pair, 200 through the frontend with no client key, 200 direct with the key, 401 without or with a wrong key; the WebSocket handshake through the frontend (101); the empty-key case, and that a client-sent `X-API-Key` is NOT forwarded when `FRONTEND_API_KEY` is empty; `/openapi.json` before and after the location is added; the raw key absent (by counts) from the image config and history, the SPA bundle, logs and argv; the shared-bucket behaviour. `docker system df` before and after (the build lands on `/`).

## Files Changed
- `compose.yaml`: `env_file` on backend and frontend, loopback port binds, header and inline comments.
- `docker/frontend.Dockerfile`, `docker/nginx.conf`, `docker/nginx-api-key.conf.template` (new), `docker/frontend.defaults.env` (new).
- `.dockerignore`: `.env`, `docker/secrets/`.
- `docs/runbooks/compose-api-key.md` (new), `docs/runbooks/README.md`.
- `agent-working/staging_artifacts/TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY/`: investigation, plan, test plan.

## Completion Summary
