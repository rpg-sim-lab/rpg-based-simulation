---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, governance]
---

# Tech-stack seed review

Epic E, child E6, seed review (`TCK-20261009-EPIC-SESSION-LEAD-PLANNER`). It re-checks the lead's 2026-10-09
stack findings on `main` 9a9058808 (2026-10-11) and gives each one a recommendation and an owner. **Advice
only**: the fixes are tickets in the owning domain (the epic's out-of-scope list says so), and the
registry/drift-check tooling is E6's own work for agent-working.

When `registries/tech_stack.yaml` exists, it should be seeded from this list and from the inventory
below.

## Findings

| # | finding (checked 2026-10-11) | still true? | recommendation | owner | routed |
|---|---|---|---|---|---|
| 1 | `mypy` is unpinned in the `dev` group, while `mypy-baseline==0.7.4`, `ruff==0.16.10` and `import-linter==2.15` are exact. A mypy release can shift the baseline with no code change. | yes | pin `mypy==2.1.0` (exact, like the other code-health tools) | codebase | already scoped: rides the import-linter flip batch (soak ends 2026-10-19) |
| 2 | `torch` is outside the lock. | **changed** | `uv.lock` now resolves `torch 2.12.1` from PyPI (the CUDA build: it pulls `cuda-bindings` on Linux) through `sentence-transformers`. The `knowledge` extra comment still says to `pip install` the CPU wheel by hand, and `.venv-knowledge` (3.12) is built that way. So the lock and the real environment disagree. Pick one: either the lock owns it (a `[tool.uv.sources]` CPU index for torch) or the extra is documented as outside the lock. Also: `Makefile` `PYTHON_KNOWLEDGE` hard-codes the other host's path `/home/u24desktop/...`. | agent-working (knowledge-search stack) | #514 (`for:agent-working-planner`) |
| 3 | `mcp>=1.0.0` is declared twice (`search-mcp` extra and `dev`). | yes | **keep**. The `dev` entry is intentional and commented: it lets the default install reach `tests/tools/test_search_mcp.py`. Record it once in the registry, with one version policy for both declarations. | lead (registry seed) | no ticket |
| 4 | Two React apps (`frontend/`, `dashboard-frontend/`) and `website/` (Docusaurus 3), with separate `package-lock.json` files and no workspace. | yes | **no workspace now** (YAGNI). The versions match today: react `^19.2.0`, vite `^7.2.4`, tailwindcss `^4.1.18`, typescript `~5.9.3` in both apps (website: react `^19.2.7`, `@docusaurus/core ^3.10.1`). The E6 drift check reports divergence; revisit only if it fires. Merging the apps or adding a workspace is a framework change, so it needs an ADR. | lead (drift check via agent-working) | no ticket |
| 5 | `compose.yaml` `redis:7-alpine` floats; Prometheus `v2.50.0`, Grafana `10.3.3`, Loki and Promtail `3.0.0` are pinned. Redis backs `src/observability` (stream consumer, anomaly worker, readiness harness). | yes | pin an exact `7.x.y-alpine` tag, matching the observability images | rpg (consumer of redis); `compose.yaml` is lead-owned, so the lead reviews the diff | #515 (`for:rpg-planner`) |
| 6 | Root clutter. | partly | The tracked tree is clean: `uvicorn.log`, `replay_v2.json/`, `scratch/`, `tmp/` and `reviews/` are git-ignored or gone. Still **untracked**, not ignored, in the main checkout: `agent-monitoring/` and `stored_artifacts/` (27 files, old pre-`agent-working/` layout, written 2026-10-03). | owner (deleting data) | on `board.md`'s residue list |

## Inventory seed (main 96db1f5e8, 2026-11-14)

The findings table above is the 2026-10-11 review and stays as a dated record. This inventory is refreshed in place; the previous one was on `main` 9a9058808.

- **Python:** see `pyproject.toml`. The code-health tools are exact pins: `mypy==2.4.0`, `mypy-baseline==0.7.4`, `ruff==0.17.0`, `complexipy==8.0.1`, `import-linter==2.15`, `pyrefly==1.3.2` (finding 1 is resolved: mypy is now pinned). Runtime and test libraries are floors.
- **Knowledge stack (`requirements-knowledge.txt`, the manual `.venv-knowledge`):** `torch==2.15.0+cpu` (CPU wheel index), `sentence-transformers==6.1.0`, `mcp==1.30.0`, `graphifyy==0.9.104`, `headroom-ai==0.37.0` (held: 0.43 needs `mcp` 2.x). Dependabot ignores torch, graphifyy and headroom-ai (#894); they move by hand with their tests (#890).
- **OpenTelemetry (API tracing, #622 R3, merged in #891):** `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`, `opentelemetry-instrumentation-fastapi` and `opentelemetry-instrumentation-redis`, locked at 1.45.2 / 0.66b2 (pyproject caps `>=1.45.1,<2` and `>=0.66b1,<0.67`). OTLP over HTTP on port 4318, off by default (`OTEL_EXPORTER_OTLP_ENDPOINT` unset). Code in `src/api/tracing.py`; doc in `docs/observability/api_request_tracing.md`.
- **Node:** three npm projects, each with its own `package-lock.json` (row 4): `frontend/` (react `^19.2.0`, vite `^8.3.5`, tailwindcss `^4.1.18`, typescript `~5.9.3`), `dashboard-frontend/`, and `website/` (Docusaurus `^3.10.1`, react `^19.3.1`). Dependabot watches `frontend/` and `website/`, not `dashboard-frontend/`.
- **Containers (`compose.yaml`, all pinned by tag and digest):** redis `8.10.3-alpine`, prometheus `v3.16.0`, grafana `13.3.0`, loki `3.7.9` (WAL on the `loki_data` volume, #895), tempo `3.1.1`, alloy `v1.21.3` (replaced Promtail, #786), ntfy `v2.37.2`, redis_exporter `v1.97.0`, node-exporter `v1.12.1`, docker-socket-proxy `v0.5.0`. Run from the checkout that holds `docker/secrets` (`docs/runbooks/ntfy-topic-rotation.md`, "Run from").
- **MCP servers (`.mcp.json`, lead-owned):** `knowledge-search`, `github` (token from `${HOME}/.config/rpg-sim/github-mcp.env`, #899), `headroom` (trial), `aseprite-pixel-art`.
- **Host runtime (ubuntu):** Docker 29 with the containerd image store, moved to `/data/containerd` (`docs/runbooks/docker-image-store-move.md`); docs site on GitHub Pages at `rpg-sim-lab.github.io/rpg-based-simulation`, deployed on main (#897).
