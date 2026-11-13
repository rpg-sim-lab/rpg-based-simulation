---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY
phase: investigation
date: 2026-11-12
tags: [platform, security]
artifact_type: investigation
---

# Investigation: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY

Read-only. No stack was started; nothing under `docker/secrets/` was read or printed. Files read are at this branch's head (main 0e16078dc plus platform-planner's notes). Sources outside the repo are quoted from the pages named in section 6.

## 0. Added after review (2026-11-12)

`.mcp.json` starts the GitHub MCP server with `docker run -i --rm --env-file .env ghcr.io/github/github-mcp-server` (read from the tracked file; no value was opened), so the repo-root `.env` is passed wholesale into that container and already holds its credentials. That rules out `.env` as the home of the API key pair: the raw key would be injected into that container and two unrelated secrets would share a file. The pair goes in gitignored files under `docker/secrets/` (`.gitignore` line 334 covers the directory; checked with `git check-ignore`), loaded by `env_file` with `required: false` (Compose v5.1.1): lead first confirmed one file, `compose.env`; platform-planner then decided to split it, so the backend never holds the raw key: `backend.env` (the hash) and `frontend.env` (the raw key). Sections 2 and 3 below were written before this; read "`.env`" there as "`docker/secrets/compose.env`".

## 1. What the stack does today

- **Backend.** `compose.yaml` passes no `RPG_API_KEY_HASHES` and no `--api-key-hashes`. `ConfigLoader` (`src/config/loader.py`, env prefix `RPG_`, field `api_key_hashes`, a plain `str`) then leaves it empty, and the backend fails closed: every protected route answers 401 `Invalid or missing API key.`; `/health` answers 200. An empty env value is the same as unset (the env loop assigns `""`; `_parse_api_key_hashes("")` returns `{}`). The CLI's `--api-key-hashes` is skipped when `None` (`cli_overrides` drops `None`), so a value from the environment is not overwritten.
- **Hashing.** `_hash_key` is `sha256(raw_key.encode("utf-8")).hexdigest()`; the stored form is `client_id:sha256hex`, comma-separated. So `printf '%s' "$key" | sha256sum` is the exact derivation (no trailing newline).
- **Frontend.** `docker/frontend.Dockerfile` builds the SPA with `npm run build` (`tsc -b && vite build`, production mode, so `frontend/.env.development` is not loaded) and serves it from `nginx-unprivileged:1.31.7-alpine3.24` with a static `docker/nginx.conf`. `VITE_API_KEY` is not set at build, so the SPA sends no key. All SPA calls are same-origin under `/api/` through `location /api/`, which already handles the WebSocket upgrade; nothing in nginx adds a key. So the compose SPA gets 401 on every API call. (rpg-planner-ubuntu, from code on main 5090cccfc, not tested live: REST uses `API_BASE '/api/v1'`, the WS is `/api/v1/ws`.)
- **WebSocket.** `require_api_key_ws` reads the `X-API-Key` header before `?key=`, so a header set on the proxied upgrade authenticates the socket.
- **Other callers.** The watchdog calls only `/health` (ungated) and the internal metrics port; Prometheus scrapes the internal port 9109; the healthcheck uses `/health`. None needs a key. The load-test override (`tools/loadtest/compose.loadtest.yaml`) already sets `RPG_API_KEY_HASHES` from `LOADTEST_API_KEY_HASHES`; with `-f compose.yaml -f compose.loadtest.yaml` the later file wins, so a new base line does not disturb it.
- **Publishing.** `backend` publishes `${BACKEND_PORT:-8000}:8000` and `frontend` publishes `${FRONTEND_PORT:-8080}:8080`, both on all interfaces. redis, prometheus, grafana and loki bind `127.0.0.1` (the compose header says so).
- **Tracked-file hygiene.** `.gitignore` ignores `.env` (line 139) and `docker/secrets/` (line 334). A new tracked top-level file would have to be added to the repo-root allowlist (`docs/guidelines/repo_tooling_layout.md`, enforced by `tests/codebase/test_repo_root_allowlist.py`), so this plan adds no root file.
- **Compose.** Docker Compose v5.1.1 is installed here. Compose reads `.env` from the project directory automatically.

## 2. Options for the backend (scope item 1)

| option | what it is | for | against | verdict |
|---|---|---|---|---|
| A | `RPG_API_KEY_HASHES=${RPG_API_KEY_HASHES:-}` on the backend, set from an untracked `.env` | one line; empty by default (fail-closed); no tracked-file edit to set keys; `.env` is already ignored; matches how the loader reads it; works with the load-test override | a same-named variable exported in a shell silently wins over `.env`; the hashes are visible in `docker inspect` of the backend (a hash, not a key) | **chosen** |
| B | `env_file: {path: docker/secrets/backend.env, required: false}` | follows the `docker/secrets/` pattern; no shell leakage | a second place to put values; the file name is another thing to document; Compose-version dependent | rejected: no benefit over A for a hash |
| C | compose `secrets:` file plus a wrapper `command` that exports the variable | the hash stays out of `docker inspect` | changes the container command; adds a shell wrapper to maintain; the value is a hash, not a secret | rejected |
| D | default to the committed dev pair | works out of the box | a known key on by default, with the API published on all interfaces | rejected (the ticket also leans this way) |
| E | `--api-key-hashes` on the command line | no env | puts the value on argv (visible in `ps` and `docker inspect`) | rejected |

The key is never stored: only its hash goes to the backend. Raw keys must be high-entropy (`openssl rand -hex 16`, 128 bits); the hash is an unsalted SHA-256 (the auth design), so a guessable key could be recovered from the hash.

## 3. The frontend half (scope item 2) - decided by rpg-planner-ubuntu: nginx adds the header

rpg-planner-ubuntu chose option (c): nginx adds `X-API-Key` when it proxies `/api/`, with no frontend change. Options that were weighed:

| option | what | verdict |
|---|---|---|
| F1 | bake `VITE_API_KEY` into the SPA at build (`build.args`) | rejected: the raw key lands in the static bundle (public to anyone who can load the page) and in image layers and `docker history` |
| F2 | nginx sets the header at proxy time from a container env var | **chosen** (rpg-planner-ubuntu's answer); the key is not in the image |
| F3 | each browser supplies its own key (frontend change) | not chosen: touches `frontend/**` |

Constraints that follow, from platform-planner:
1. **nginx becomes the auth boundary.** Anyone who can reach the frontend port can call the API as that key, through the proxy. So the frontend must not be on all interfaces by default: bind it to loopback (`127.0.0.1:${FRONTEND_PORT:-8080}:8080`). What changes: another machine (a LAN peer, a forwarded VM port) can no longer reach `:8080` unless the owner sets the bind address (a `FRONTEND_BIND` override is planned). On this single-user host, loopback is the default the plan recommends.
2. **One key is one admission bucket.** The backend's per-client admission control keys its token bucket on the API key (`src/api/admission_control.py`), so every browser tab and every user of the nginx-injected key share one bucket (capacity 30, refill 3 per second). Heavy use of the SPA by several tabs can be throttled with 429; rpg's `TCK-20261112-A-THROTTLED-CLIENT-THAT-WAITS-OUT-RETRY-AFTER-IS-STILL-REFUSED` covers how recovery behaves.
3. **Fail-closed default.** With no key configured, nginx must send no header, never a placeholder. nginx documents it: "If the value of a header field is an empty string then this field will not be passed to a proxied server" (nginx.org, `ngx_http_proxy_module`, `proxy_set_header`). So `proxy_set_header X-API-Key "";` sends nothing. That doc does not say whether a client-sent header of the same name is also dropped; the plan treats nginx as the only source and tests it (a client-sent `X-API-Key` through the frontend port must not authenticate on its own with an empty configured key).
4. **Injection at container start, not at build.** The docker-library image's templates mechanism: files in `/etc/nginx/templates/*.template` are run through `envsubst` at start into `/etc/nginx/conf.d` ("This directory must be writable by the user running a container"); `NGINX_ENVSUBST_OUTPUT_DIR` changes the output directory, `NGINX_ENVSUBST_FILTER` limits which variables are substituted ("only variables whose names match this pattern are available for substitution"). The unprivileged image's own README defers to that documentation ("Check out the docs for the upstream Docker NGINX image") and does not state whether the templates step runs or as which user. **Settled on 2026-11-12 from the upstream source** (a web-fetch read of `nginxinc/docker-nginx-unprivileged`, no container started; the git tag `1.31.7` returned 404, so the read is of branch `main`, which builds nginx 1.31.8, and the proof run still confirms it on the pinned image): `docker-entrypoint.sh` runs the `/docker-entrypoint.d/*.sh` scripts when `$1` is `nginx`, with no `id -u` or root check, as the image's `USER $UID` (101); `20-envsubst-on-templates.sh` takes the template dir (default `/etc/nginx/templates`), suffix `.template`, output dir `${NGINX_ENVSUBST_OUTPUT_DIR:-/etc/nginx/conf.d}` and filter `${NGINX_ENVSUBST_FILTER:-}`; it does **not** create the output directory (it logs "ERROR: ... is not writable" and returns if it cannot write there); it calls `envsubst "$defined_envs"` with an explicit list built from the environment, so nginx's own `$host` etc. are left alone unless an env variable has that name; it prints `Running envsubst on <template> to <output path>` (paths, never values; silenced by `NGINX_ENTRYPOINT_QUIET_LOGS`). The Dockerfile makes `/etc/nginx` group-writable (`chown -R $UID:0`) and puts nginx's temp paths and pid under `/tmp`. So the templates step runs as uid 101 and honours `NGINX_ENVSUBST_OUTPUT_DIR`, and no fallback entrypoint is needed. The design below still keeps `default.conf` static and renders only the header line, to `/tmp` (which always exists), because that depends on the least:
   - keep `docker/nginx.conf` static (no `envsubst` ever sees nginx's own `$host`, `$remote_addr`, `$http_upgrade` and the rest);
   - add one small template, `docker/nginx-api-key.conf.template`, whose only content is `proxy_set_header X-API-Key "${FRONTEND_API_KEY}";`, rendered to `/tmp` (`NGINX_ENVSUBST_OUTPUT_DIR=/tmp`, `NGINX_ENVSUBST_FILTER=^FRONTEND_API_KEY$`), a path nginx-unprivileged already uses as writable (its temp paths are under `/tmp`);
   - `location /api/` gets `include /tmp/api-key.conf;`. An explicit include means a missing rendered file stops nginx at start (loud), not a silent 401.
5. **The key must not reach nginx's logs.** The default `access_log` uses the predefined `combined` format (fields `$remote_addr`, `$remote_user`, `$time_local`, `$request`, `$status`, `$body_bytes_sent`, `$http_referer`, `$http_user_agent`: no request-header values sent upstream), and the default `error_log` level is `error` (nginx.org, `ngx_http_log_module` and `ngx_core_module`). `docker/nginx.conf` sets neither. The pages do not say whether header values appear at any `error_log` level, so the plan keeps the default level and the proof scans `docker compose logs frontend` for the key by count. The entrypoint prints the template path it renders, not the substituted value (to be seen in the run).
6. **Where the key still shows.** The raw key is in the frontend container's environment (`docker inspect`, `/proc/<pid>/environ` of nginx) and in the rendered `/tmp/api-key.conf`. `docker compose config` prints resolved variables, so it prints the raw key and must not be pasted anywhere. The runbook says so. None of it is argv.

## 4. `/openapi.json` (the new hotfix TCK-20261112-COMPOSE-FRONTEND-API-DOCS-SCHEMA-NOT-PROXIED, same batch)

`ApiDocsPage` fetches `/openapi.json`; FastAPI serves it at the backend root, ungated (the auth doc lists `/health`, `/docs`, `/openapi.json` as not gated); `docker/nginx.conf` proxies only `/api/`, so `location /` returns `index.html` for it. Not observed live yet. The plan observes it first in the proof run (content type through the frontend port, before the change), then adds `location = /openapi.json { proxy_pass http://backend:8000; ... }` with the same proxy headers and **no** key header, and re-observes `application/json`.

## 5. Open points

- Backend bind. The plan binds the frontend to loopback by default (a constraint of nginx being the auth boundary). Binding the backend's `8000` to loopback too is consistent with redis, prometheus, grafana and loki, but it is a separate behaviour change for anything that uses the API from another machine. The plan proposes the same `${BACKEND_BIND:-127.0.0.1}` pattern and asks for the decision; with fail-closed auth the exposure is gated either way.
- The frontend image must be rebuilt to carry the new `nginx.conf`/template, so the proof is not a light run: a frontend build needs `npm ci` and the node and nginx base images. It needs its own slot ask.
- Unverified until the run: the templates step in the unprivileged image (does it run, as which user, and does it write `/tmp/api-key.conf`); the exact `NGINX_ENVSUBST_*` behaviour with an empty value; that a client-sent `X-API-Key` is dropped by `proxy_set_header X-API-Key ""`.

## 6. Sources

- Repository files named above, read on this branch.
- https://nginx.org/en/docs/http/ngx_http_proxy_module.html (proxy_set_header); https://nginx.org/en/docs/http/ngx_http_log_module.html (default `combined` format); https://nginx.org/en/docs/ngx_core_module.html#error_log (default level `error`).
- https://github.com/docker-library/docs/blob/master/nginx/README.md ("Using environment variables in nginx configuration"); https://github.com/nginxinc/docker-nginx-unprivileged (README). Not read: the unprivileged repo's `entrypoint/` directory.
