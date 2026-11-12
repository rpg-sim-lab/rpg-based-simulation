---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, security]
---

# Runbook: API keys for the compose stack

Ticket: `TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY`. The compose stack ships **fail-closed**: until you configure a key, the backend answers 401 on every route except `/health`, including through the frontend. This runbook says how to configure one without editing a tracked file and without putting a key on a command line.

## How it works

- The backend authenticates every protected request with an `X-API-Key` header (or `?key=` on a WebSocket) against a list of **hashes** (`RPG_API_KEY_HASHES`, `client_id:sha256hex`, comma-separated; `docs/architecture/http_api_key_authentication.md`). It never stores or sees a raw key.
- The frontend is a static page served by nginx, which proxies `/api/` (REST and the WebSocket) to the backend. **nginx adds the key**: at container start the base image renders `docker/nginx-api-key.conf.template` into `/tmp/api-key.conf`, and `docker/nginx.conf` includes it in `location /api/`. The browser sends no key and the key is not in the page or the image. With no key configured, nginx sends **no** header (never a placeholder).
- One raw key and its hash make a pair, kept in **two** gitignored files so that each service gets only what it needs:
  - `docker/secrets/backend.env`: `RPG_API_KEY_HASHES=local:<sha256 of the raw key>`, loaded by the backend only;
  - `docker/secrets/frontend.env`: `FRONTEND_API_KEY=<the raw key>`, loaded by the frontend only (after the tracked, secret-free defaults file `docker/frontend.defaults.env`, which sets it empty).
- Both are optional (`required: false` in `compose.yaml`). A missing file means no key: fail-closed.

## Why not the repo-root `.env`

The repository's `.mcp.json` starts the GitHub MCP server with `docker run -i --rm --env-file .env ghcr.io/github/github-mcp-server`, so the root `.env` is passed **wholesale** into that container and already holds its GitHub credentials. Putting the API key there would inject it into that container's environment and mix two unrelated secrets in one file. So the key pair has its own files under `docker/secrets/` (gitignored). Do not open or print `.env` while doing this.

## Make a key pair (owner-run)

The raw key stays in a shell variable; `printf` is a shell builtin and `sha256sum` reads it from stdin, so no key appears on a command line. First, from the repository root, check that both paths are ignored by git. Stop if this prints nothing:

```
git check-ignore -q docker/secrets/backend.env && git check-ignore -q docker/secrets/frontend.env && echo ignored-ok
```

Then check that neither file exists yet. Stop if this prints nothing: use "Rotate or remove" below instead, so a second run cannot leave two different keys:

```
test ! -e docker/secrets/backend.env && test ! -e docker/secrets/frontend.env && echo no-key-files-yet
```

Then write both from the same key (`noclobber` makes each write refuse if its file appeared in the meantime):

```
umask 077
mkdir -p docker/secrets
set -o noclobber
key=$(openssl rand -hex 16)
printf 'FRONTEND_API_KEY=%s\n' "$key" > docker/secrets/frontend.env
printf 'RPG_API_KEY_HASHES=local:%s\n' "$(printf '%s' "$key" | sha256sum | cut -d' ' -f1)" > docker/secrets/backend.env
unset key
set +o noclobber
```

Keys must be 128-bit random hex like this: the hash is an unsalted SHA-256, so a guessable key could be recovered from it, and a value containing `$` would be read as a variable by compose. Do not reuse the committed `make dev` pair: it is a known key, for local development only.

Then recreate the two services:

```
docker compose up -d backend frontend
```

## Check it (no key on argv)

Without a key the backend refuses, and through the frontend nginx supplies it. The first command sends the key from the file on stdin (`curl -K -` reads its options from stdin); the other two send none:

```
grep '^FRONTEND_API_KEY=' docker/secrets/frontend.env | cut -d= -f2- | sed 's/^/header = "X-API-Key: /; s/$/"/' | curl -s -K - -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/v1/manifest
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/v1/manifest
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/api/v1/manifest
```

Expected: `200`, `401`, `200`. With neither file present: `401`, `401`, `401`, and `/health` still `200`.

## What shows the raw key (read this before pasting anything)

The raw key is not in git, not in the image, not on argv, not in the backend at all, and (by nginx's default log formats) not in nginx's logs. It is in:

- `docker/secrets/frontend.env` (mode 600, yours);
- the **frontend container's environment** (`docker inspect` shows it to anyone in the docker group) and the rendered `/tmp/api-key.conf` inside that container;
- the output of **`docker compose config`**, which prints the resolved environment of every service: never paste that output anywhere.

The backend holds only the hash (`docker/secrets/backend.env`), which is not a key, but treat it as private too (a weak key could be recovered from it).

## Binding and who loses access

`backend` and `frontend` publish on `127.0.0.1` by default (`BACKEND_BIND`, `FRONTEND_BIND`; the ports are still `BACKEND_PORT`, `FRONTEND_PORT`). Because nginx adds the key, **anyone who can reach the frontend port is authenticated as that key**, which is why it is not on every interface. What changes: only other machines (a LAN peer, a forwarded VM port) lose access; the frontend, ai_worker and the other services reach the backend over the compose network and are not affected. To publish on every interface, set `BACKEND_BIND=0.0.0.0` or `FRONTEND_BIND=0.0.0.0` in the shell (these are addresses, not secrets), knowing the consequence above.

## One key, one bucket

The backend rate-limits per key (a token bucket of 30, refilled at 3 per second). Every browser tab and every user of the frontend share the one nginx key, so they share one bucket and can see 429 together. That is expected here; rpg's `TCK-20261112-A-THROTTLED-CLIENT-THAT-WAITS-OUT-RETRY-AFTER-IS-STILL-REFUSED` covers how a throttled client recovers.

## Rotate or remove

To rotate, delete both files, then repeat "Make a key pair" (it generates a new raw key and its hash):

```
rm docker/secrets/backend.env docker/secrets/frontend.env
```

then `docker compose up -d backend frontend`. Deleting both files and recreating the two services returns the stack to fail-closed.

## Not in scope

Production key provisioning (unbuilt; the auth design doc section 6) and the load-test keys (`tools/loadtest/keys.py`, which has its own override file).
