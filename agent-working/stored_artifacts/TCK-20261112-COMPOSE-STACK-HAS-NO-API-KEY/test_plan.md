---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY
phase: test_plan
date: 2026-11-12
tags: [platform, security]
artifact_type: test_plan
---

# Test plan: TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY

> **Amendment, 2026-11-12.** The key pair is in two gitignored files, `docker/secrets/backend.env` (the hash) and `docker/secrets/frontend.env` (the raw key), not in `.env`, with the tracked `docker/frontend.defaults.env` supplying the empty default. Added or changed checks:
> - S0. `git check-ignore -q` exits 0 for BOTH `docker/secrets/backend.env` and `docker/secrets/frontend.env` (the key pair is split in two, platform-planner's decision), and `git check-ignore docker/frontend.defaults.env` prints nothing (the defaults file is tracked).
> - S1/S2 run against a scratch copy of `compose.yaml` pointing at two throwaway env files outside `docker/secrets/`, printing booleans only: default fail-closed; the frontend file wins over the empty default; **the backend environment has no `FRONTEND_API_KEY` and the frontend environment has no `RPG_API_KEY_HASHES`**; ports bind to `127.0.0.1`.
> - S6. `.dockerignore` lists `.env` and `docker/secrets/`.
> - P3 also confirms the rendered `/tmp/api-key.conf` has one `proxy_set_header X-API-Key` line and that the default (no `frontend.env`) renders an empty value, not an nginx start failure.
> - P8 adds: neither the backend's nor the frontend's `docker top` output has the key on argv, and the build context upload does not include `docker/secrets/` (the `.dockerignore` effect, read from the build log by count).


Static checks run before the proof run and need no stack. The proof run (P1 to P9) needs a frontend image build and its own slot ask; it covers the folded-in `/openapi.json` hotfix too. Run rules, as in the earlier runs: build first, `df` gate at 85% on `/` and `/data`, the abort watcher armed, `down` without `-v`, outputs under `/data`. **Nothing under `docker/secrets/` is read or printed; the raw key is generated in-process, sent through a `curl -K -` config on stdin, and never written to an evidence file.**

## Static

- S1. `docker compose config -q` passes with no `.env`; the rendered backend `environment` has `RPG_API_KEY_HASHES` empty and the frontend has `FRONTEND_API_KEY` empty (read with `docker compose config | python3 -c ...` that prints booleans, never the values).
- S2. With a throwaway value for each variable exported in the shell (generated in the check, never printed), the render shows both set, and only the frontend's raw value is the one that must not be pasted; the check prints counts only.
- S3. `git diff` shows no tracked file containing a key or hash value other than the existing documented dev pair (the Makefile and `docs/architecture/http_api_key_authentication.md`): a scan by counts for `[0-9a-f]{64}` added lines, reviewed by eye.
- S4. `docker/nginx.conf` parses structurally (the only `$` variables in it are nginx's own; the template contains exactly one `${FRONTEND_API_KEY}`); the Dockerfile `ENV` lines hold no secret.
- S5. Paths guard, REGISTRY no-drift, repo-root allowlist test (no new top-level file), compose-hygiene tests.

## In the proof run (P1 to P9)

- P1. **Default is fail-closed.** No `.env`. `/health` 200; a read route directly on the backend port and through the frontend port: 401 both. The SPA's `index.html` loads (200).
- P2. **`/openapi.json` before the fix** (the hotfix's observation): through the frontend port, record the status and the content type (expected `text/html` from `index.html`); directly on the backend, `application/json`.
- P3. Templates step (the first unverified item): the frontend starts; `docker compose logs frontend` shows the envsubst entrypoint ran; `/tmp/api-key.conf` exists in the container (`docker compose exec frontend ls -l /tmp/api-key.conf`) and has one `proxy_set_header X-API-Key` line; its value is read by a script that prints only the length and whether it is non-empty.
- P4. **Pair configured.** Create `.env` with a fresh pair in-process; recreate backend and frontend. Direct backend with the raw key: 200; without: 401; wrong key: 401. Through the frontend, with no client key: 200 (nginx adds it).
- P5. **WebSocket through the frontend** (`/api/v1/ws`, an Upgrade request with no client key): `101 Switching Protocols`. Without the pair: 401/403 on the handshake.
- P6. **Empty `FRONTEND_API_KEY` with the hash set:** the frontend request gets 401 (no silent bypass). A client-sent `X-API-Key` (the raw key) through the frontend with `FRONTEND_API_KEY` empty: record whether it authenticates (nginx docs are silent; either result is recorded, and a pass-through of the client's header would be a finding).
- P7. **`/openapi.json` after the fix:** through the frontend port `application/json`, status 200, and the response body is the same schema as the backend's (compare a hash of both); no key header is needed.
- P8. **The key is not where it should not be.** By counts, 0 occurrences of the raw key in: the frontend image's config and `docker history --no-trunc`, the built SPA bundle in the image (`docker run --rm`-free: `docker cp` from a created container of the frontend image, then a scan), `docker compose logs` of backend and frontend, and the evidence folder; and no process in the containers has it on argv (`docker top` for backend and frontend, scanned by count). Expected to show it, and recorded as such: the frontend container's environment and `/tmp/api-key.conf`.
- P9. **Admission bucket.** Two parallel clients through the frontend share one bucket: send paced requests (at most 1 per second, as in run A) from two shells and record that both see the same 429 behaviour when the bucket is spent; this is the documented one-bucket consequence, observed, not fixed.

## Evidence

`agent-working/stored_artifacts/TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY/run-<date>/` with `.txt` names; scan the folder by counts for the generated raw key and its hash. The files under `docker/secrets/` are not read by this work (the dispatch forbids it), so they are not part of the scan.
