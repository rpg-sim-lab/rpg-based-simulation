---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY
phase: plan
date: 2026-11-12
tags: [platform, security]
artifact_type: plan
---

# Plan: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY

> **Amendment, 2026-11-12, after platform-planner's and lead's review (this supersedes the plan below where they differ).**
> - **No root `.env`.** The repo's `.mcp.json` runs the GitHub MCP server with `docker run -i --rm --env-file .env ...`, so the root `.env` is passed wholesale into that container and already holds its GitHub credentials. Putting the API key pair there would inject the raw key into that container and mix two unrelated secrets. The pair lives in one gitignored file, files under `docker/secrets/` (lead confirmed the directory; first one file `compose.env`, then split in two, see below), loaded explicitly with `env_file` (`required: false`) on the backend and the frontend only. `.env` is not opened, printed or mentioned in any recipe except to say why it is not used.
> - **Defaults file.** The base image's templates step substitutes only variables that exist; an undefined `FRONTEND_API_KEY` would leave `${FRONTEND_API_KEY}` in the rendered file and nginx would refuse to start in the default state. So the frontend also lists a tracked, secret-free `docker/frontend.defaults.env` (`FRONTEND_API_KEY=`, empty) first; `frontend.env`, listed last, overrides it. The backend needs no default (its field defaults to empty).
> - **The recipe** (runbook) writes both lines with one redirect under `noclobber` (it refuses if the file exists, so a second run cannot leave two keys) after `git check-ignore -q` on BOTH `docker/secrets/backend.env` and `docker/secrets/frontend.env` and a check that neither exists; stop if either check fails. Bash-builtin `printf` only.
> - **Loopback.** Both `frontend` and `backend` bind to `127.0.0.1` by default (`FRONTEND_BIND`, `BACKEND_BIND`), as platform-planner approved; the runbook says who loses access (only other machines).
> - **nginx-unprivileged entrypoint, settled from upstream source** (see `investigation.md` section 3.4): the templates step runs as uid 101 and honours `NGINX_ENVSUBST_OUTPUT_DIR`; no fallback entrypoint is needed. The proof run still confirms it on the pinned image.
> - **`.dockerignore`** now lists `.env` and `docker/secrets/`, so neither is sent in a build context (no Dockerfile copies the whole context, so neither could reach an image anyway: defence in depth).
> - **Split into two files (platform-planner: yes, the backend must never hold the raw key).** `docker/secrets/backend.env` holds `RPG_API_KEY_HASHES` only and is loaded by the backend only; `docker/secrets/frontend.env` holds `FRONTEND_API_KEY` only and is loaded by the frontend only (after `docker/frontend.defaults.env`). The recipe checks BOTH paths are gitignored and BOTH files absent before writing anything, then writes each under `noclobber` from the same in-shell key. Wherever the rest of this plan says `docker/secrets/compose.env` or `.env`, read these two files. The static check S2 requires the backend environment to have no `FRONTEND_API_KEY` and the frontend environment to have no `RPG_API_KEY_HASHES`.
> - `/openapi.json` stays as planned: observe first (P2), then add the location.


Standard tier. Findings are in `investigation.md`. **Not implemented yet: this plan goes to platform-planner first.** Folded in, as platform-planner asked: the hotfix `TCK-20261112-COMPOSE-FRONTEND-API-DOCS-SCHEMA-NOT-PROXIED` (the `/openapi.json` proxy). No heavy run in this dispatch; the proof run comes later with its own slot ask.

## Decision

1. **Backend:** pass-through `RPG_API_KEY_HASHES=${RPG_API_KEY_HASHES:-}`, empty by default, set from the untracked `.env` (option A).
2. **Frontend:** nginx adds `X-API-Key` when it proxies `/api/` (rpg-planner-ubuntu's answer), with the key injected at container start from `FRONTEND_API_KEY`, never baked into the image.
3. **nginx is the auth boundary:** the frontend binds to loopback by default.
4. **`/openapi.json`:** proxied by an exact-match location, with no key header.
5. A runbook `docs/runbooks/compose-api-key.md`, linked from the runbook index and from the compose header.
6. The committed dev pair stays dev-only; no real secret goes into git; no new top-level file.

## The key pair

One raw key and its hash. `.env` (untracked, mode 600) holds both:

```
FRONTEND_API_KEY=<raw key>                      # read by nginx only
RPG_API_KEY_HASHES=local:<sha256 of the raw key> # read by the backend
```

The owner makes it without printing the key (the key is in a shell variable only; `printf` is a builtin, `sha256sum` reads stdin):

```
umask 077
key=$(openssl rand -hex 16)
{ printf 'FRONTEND_API_KEY=%s\n' "$key"; printf 'RPG_API_KEY_HASHES=local:%s\n' "$(printf '%s' "$key" | sha256sum | cut -d' ' -f1)"; } >> .env
unset key
```

Rotation replaces both lines and recreates backend and frontend. Unset both lines: the stack is fail-closed again.

## Changes

1. `compose.yaml`
   - backend `environment`: `- RPG_API_KEY_HASHES=${RPG_API_KEY_HASHES:-}`, with a comment (empty means fail-closed; the runbook; the value is a hash).
   - frontend `environment`: `- FRONTEND_API_KEY=${FRONTEND_API_KEY:-}` (the raw key, for nginx only; a comment saying `docker compose config` prints it).
   - frontend `ports`: `"${FRONTEND_BIND:-127.0.0.1}:${FRONTEND_PORT:-8080}:8080"`.
   - backend `ports`: `"${BACKEND_BIND:-127.0.0.1}:${BACKEND_PORT:-8000}:8000"` **only if platform-planner decides yes** (open question below).
   - the header comment lists the new variables and points at the runbook.
2. `docker/nginx-api-key.conf.template` (new): one line, `proxy_set_header X-API-Key "${FRONTEND_API_KEY}";`.
3. `docker/frontend.Dockerfile`: `COPY docker/nginx-api-key.conf.template /etc/nginx/templates/api-key.conf.template`; `ENV NGINX_ENVSUBST_OUTPUT_DIR=/tmp NGINX_ENVSUBST_FILTER=^FRONTEND_API_KEY$` (non-secret configuration).
4. `docker/nginx.conf`: `include /tmp/api-key.conf;` inside `location /api/` (explicit, so a missing file stops nginx at start); and `location = /openapi.json { proxy_pass http://backend:8000; <same proxy headers as /api/> }` with no key header, added after the proof run observes the failure first (see test plan).
5. `docs/runbooks/compose-api-key.md` (new) and a row in `docs/runbooks/README.md`: how to make a pair, where it lives, verification commands, rotation, what shows the key (`docker inspect` of the frontend, the rendered `/tmp/api-key.conf`, `docker compose config`), the loopback default and how to override it, the one-bucket consequence, and why the dev pair is not the default.

## Fail-closed behaviour, by case

| case | backend | nginx | result |
|---|---|---|---|
| no `.env` | hashes empty | `proxy_set_header X-API-Key ""`, header not sent | 401 on every protected route, `/health` 200 |
| pair in `.env` | hash configured | header = raw key | 200 through the frontend; 200 on the backend port with the key; 401 without |
| hash set, `FRONTEND_API_KEY` empty | configured | no header | the SPA gets 401 (no silent bypass); direct API clients with the key work |
| `FRONTEND_API_KEY` set, no hash | empty | header sent | still 401 (backend fail-closed) |
| wrong raw key | configured | wrong header | 401 |
| client sends its own `X-API-Key` through the frontend | any | replaced by nginx's value (to be observed; the nginx docs do not say) | must not authenticate on its own when nginx's value is empty |

## Interactions and limits (stated, not fixed)

- One key means one per-key admission bucket for every tab and user of the SPA (`investigation.md` 3.2).
- Anyone who can reach the frontend port is authenticated as that key: hence loopback by default and the override variable.
- The raw key is in the frontend container's environment and in `/tmp/api-key.conf`; it is not in the image, not in the SPA bundle, not on argv, and (by the default log formats) not in nginx's logs.
- The load-test override keeps working (its later `RPG_API_KEY_HASHES` wins).
- Out of scope, unchanged: `src/api/auth.py`, `frontend/**`, production key provisioning.

## Open questions for platform-planner

1. Bind the backend's `8000` to loopback by default too (`BACKEND_BIND`)? It matches redis, prometheus, grafana and loki, but changes access from other machines. My recommendation: yes, with the override.
2. `FRONTEND_BIND`/`BACKEND_BIND` as the override names: acceptable?
3. The first proof needs a frontend image build (node and nginx base images, `npm ci`): a heavy slot with the usual gates, not a light run. Agreed that I ask for it after you approve the plan?
4. If the templates step turns out not to run in the unprivileged image, the fallback is a custom entrypoint script under `docker/` that writes `/tmp/api-key.conf` with `printf`; I would stop and report before building that.

## Risks

- The unprivileged image's templates step is documented only upstream; the test plan checks it first.
- A same-named variable exported in the shell wins over an `env_file` value for interpolation but not for `env_file` itself; the key pair is only ever read from the two gitignored files, so a stray shell variable does not change what the containers get (the runbook still says to check `docker compose config` booleans, not values).
- `docker compose config` prints the raw key; the runbook warns, and the proof never runs it with a real key on a terminal that is captured.
