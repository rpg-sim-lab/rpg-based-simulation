---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, governance]
---

# Tech stack overview

Kept by `lead-planner`. One page that lists every stack the project uses, grouped by domain, with where and how each is
used. Taken from the manifests on `main` at 36d4fd78 (2026-11-04): `pyproject.toml`, the three `package.json` files,
`compose.yaml`, `docker/`, `infra/terraform/`, `.github/workflows/`, `.mcp.json` and `visual_assets/`.

"Used in" counts are files with a top-level import of the package (`import x` / `from x`), counted in
`src/`, `tools/` and `tests/`. They show where a library sits, not how heavily it is called.

This page is **advice and inventory only**. It is not the registry: `registries/tech_stack.yaml` does not exist yet, and
`stack_seed_review.md` says it should be seeded from this page. Changing a version is an edit in the owning domain
(see the owner column), not here.

## At a glance

| domain | core stack | lives in | owner |
|---|---|---|---|
| Simulation engine | Python 3.12+ (3.13 in CI and images), Pydantic, PyYAML | `src/` | rpg |
| API and live server | FastAPI, Starlette, Uvicorn, msgpack, WebSockets | `src/api/` | rpg |
| Observability and analytics | Redis Streams, Prometheus client, DuckDB, PyArrow, psutil | `src/observability/` | rpg |
| Game client | React 19, Vite 8, Tailwind 4, Radix UI, TypeScript 5.9 | `frontend/` | rpg |
| Agent-ops dashboard | React 19, Vite 7, ECharts 6, Tailwind 4 | `dashboard-frontend/`, `src/api/agent_ops_dashboard/` | lead |
| Documentation site | Docusaurus 3, local search plugin | `website/`, `docs/` | lead |
| Testing | pytest, pytest-xdist, Hypothesis, Vitest, Testing Library, Playwright | `tests/`, `frontend/` | rpg / testing |
| Code health | Ruff, mypy, import-linter, ast-grep, complexipy, Pyrefly, jscpd | `codebase/`, `Makefile` | codebase |
| Performance | psutil, memray, py-spy, Locust | `src/perf/`, `tools/perf/`, `tools/loadtest/` | perf |
| Packaging and build | uv, `uv.lock`, npm with one lockfile per app, Make | repo root | lead |
| Containers and runtime | Docker, Docker Compose, nginx | `compose.yaml`, `docker/` | platform |
| Monitoring stack | Prometheus, Grafana, Loki, Alloy, Tempo, ntfy, exporters | `compose.yaml` (`observability` profile), `docker/` | platform |
| Cloud infrastructure | Terraform on AWS (ECS, IAM OIDC, Budgets) | `infra/terraform/` | platform |
| CI/CD and supply chain | GitHub Actions, Trivy, Semgrep, Gitleaks, CodeQL, cosign, SBOM, Dependabot | `.github/` | testing / platform |
| Agent tooling | Claude Code, workflow scripts (JS), MCP servers, sentence-transformers, sqlite-vec, BM25 | `.claude/`, `tools/`, `.mcp.json` | agent-working |
| Visual assets | Aseprite with Lua scripts in a bwrap sandbox, MCP server | `visual_assets/` | asset |

## 1. Simulation engine (core Python)

The deterministic tick kernel, world generation and assembly, entities, cognition, combat, economy and world
evolution. Pure Python: the engine has no numeric or game library.

| stack | version policy | where | how it is used |
|---|---|---|---|
| Python | `>=3.12` (`pyproject.toml`); 3.13 in CI (`setup-uv`) and in `docker/backend.Dockerfile` (`python:3.13.16-slim`) | all of `src/` | The language for the engine, API, observability and tools. The knowledge-search venv stays on 3.12 (see section 11). |
| Pydantic v2 | `>=2.0.0` | `src/` 71 files: observability 22, api 8, lab 7, content 6 | Typed records and schemas: event envelopes, API read models, lab and experiment specs, content definitions. |
| PyYAML | `>=6.0` | `src/` 28, `tools/` 64, `tests/` 142 | Declarative content and world topology (`content/`, `config/`), lab specs, registries, the parity ledger and the mechanism registry. |
| typing-extensions | `>=4.8.0` | `src/` | Typing backports. |

Entry points (`[project.scripts]`): `rpg-sim` (`src.__main__`), `rpg-world` (`src.worldbuilding.cli`),
`rpg-lab` (`src.lab.cli`).

## 2. API and live server

Server mode serves the visual client at `http://127.0.0.1:8000` and the read-model API (README, "Running the Engine").

| stack | version policy | where | how it is used |
|---|---|---|---|
| FastAPI | `>=0.143.5` | `src/api/` 27 files; also `tools/search_server.py`, `tools/perf/` | REST and WebSocket routes. Presenters and schemas shape read models (CLAUDE.md: never return raw domain objects). |
| Starlette | `>=1.0.0,<2` | `src/api/` 2 files | Middleware and low-level request handling under FastAPI. The only capped runtime dependency. |
| Uvicorn (`standard`) | `>=0.30.0` | `src/api/`, `src/cli/`, `tools/search_server.py`, `tools/perf/` | ASGI server for the engine API, the agent-ops dashboard backend (port 8420) and the knowledge search server. |
| msgpack | `>=1.0.0` | `src/api/ws/stream.py`, `tools/perf/` 1 | Compact binary frames on the live WebSocket stream. |
| websockets | `>=12.0` (dev group) | `tools/perf/`, tests | Live-stream client for perf probes and API tests. |
| requests | `>=2.31.0` | `src/observability/watchdog.py`, `src/observability/alerts/sinks.py` | Outbound HTTP: the watchdog's probes and the webhook alert sink. |

## 3. Observability and analytics

Events, metrics, the live SimQ quality hub, anomaly detection, and offline analytics over run output.

| stack | version policy | where | how it is used |
|---|---|---|---|
| Redis (client) | `>=5.0.0` | `src/observability/` 3 files | Redis Streams carry the live event stream (`OBS_LIVE_STREAM`, `src/observability/config.py`) to the anomaly worker and to stream consumers. |
| Redis (server) | `redis:8.10.2-alpine`, digest-pinned | `compose.yaml` `redis` | Broker for the backend and the `ai_worker` service (`python -m src.observability.anomaly.worker`). |
| prometheus-client | `>=0.20.0` | `src/api/` 4, `src/observability/` 2 | Exposes `/metrics` for the Prometheus server in the monitoring stack. |
| DuckDB | `>=1.0.0` | `src/observability/analytics/` (query, dataset), `tools/agent-monitoring/duckdb_view.py` | SQL over run output and the agent-monitoring JSONL shards. |
| PyArrow | `>=15.0.0` | `src/observability/analytics/` (exporter, dataset), `src/observability/mining/` | Columnar (Parquet) export of run telemetry for DuckDB. |
| psutil | `>=5.9.0` | `src/perf/` 3, `src/engine/` 2, `src/observability/` 1, `src/certification/` 1 | Process memory and CPU readings for budgets, the watchdog and certification. |
| pandas | **not declared** | `src/observability/mining/dataset.py` (lazy import) | See finding F2. |

## 4. Game client (`frontend/`)

The browser visual client for the running simulation.

| stack | version | how it is used |
|---|---|---|
| React / React DOM | `^19.2.0` | UI |
| TypeScript | `~5.9.3` | Language |
| Vite + `@vitejs/plugin-react` | `^8.3.5` + `^6.1.2` | Dev server and build |
| Tailwind CSS + `@tailwindcss/vite` | `^4.1.18` + `^4.3.3` | Styling |
| Radix UI primitives (scroll-area, slider, slot, tabs, tooltip) | `^1.x` | Accessible components, shadcn-style with `class-variance-authority`, `clsx` and `tailwind-merge` |
| lucide-react | `^1.61.0` | Icons |
| ESLint 10 + typescript-eslint, react-hooks and react-refresh plugins | `^10.13.0` | Lint (`npm run lint`) |
| Vitest + Testing Library + jsdom | `^5.0.5` | Unit and component tests |
| Playwright | `^1.62.1` | End-to-end tests (`npm run test:e2e`) |

Container: built on `node:24.21.0-alpine3.24` and served by `nginxinc/nginx-unprivileged:1.31.6-alpine3.24`
(`docker/frontend.Dockerfile`, `docker/nginx.conf`). The client half of the visual-asset store lives in
`frontend/src/visualAssets/` (asset domain).

## 5. Agent-ops dashboard (`dashboard-frontend/`)

A dashboard of agent and workflow activity. Backend: `src/api/agent_ops_dashboard/serve.py` (port 8420).

| stack | version | how it is used |
|---|---|---|
| React 19, TypeScript 5.9, Tailwind 4, Radix UI | same ranges as `frontend/` | UI |
| Vite + plugin-react | `^7.2.4` + `^5.1.1` | Build. **One major behind `frontend/`** (finding F1) |
| ECharts + echarts-for-react | `^6.1.0` + `^3.0.6` | Charts |
| Vitest | `^4.0.18` | Tests. One major behind `frontend/` |

## 6. Documentation site (`website/`)

| stack | version | how it is used |
|---|---|---|
| Docusaurus (core, preset-classic) | `^3.10.1` | A single site over `docs/` (Mechanics Bible, engine contracts, architecture), tickets, stored artifacts and archived docs |
| `@easyops-cn/docusaurus-search-local` | `^0.55.2` | Offline full-text search |
| React | `^19.2.7` | Docusaurus runtime |

Deployed to GitHub Pages by `.github/workflows/deploy-docs.yml` (platform-owned). Publishing is re-enabled under
`TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`, which is still in progress.

## 7. Testing

| stack | version policy | where | how it is used |
|---|---|---|---|
| pytest | `>=8.0.0` | `tests/` | The main suite, organised by `docs/testing/test_taxonomy.md`. Scope runs by domain or with `-m "not slow"` (CLAUDE.md). |
| pytest-xdist | `==3.8.0` | CI `test.yml` | Parallel jobs with `--dist loadgroup`. |
| pytest-asyncio | `>=1.0.0` | API and async tests | Async test support. |
| Hypothesis | `>=6.0.0` | declared (dev) | Property tests. No top-level import found; any use is inside functions. |
| httpx | `>=0.27.0` | declared (dev) | FastAPI `TestClient` transport. |
| coverage | `>=7.0.0` | CI | Coverage reports. |
| jsonschema | `>=4.0.0` | `tests/tools/` 2 files | Validates parity-ledger entries against `docs/parity_ledger/schema.json`. |
| SimQ (in-house) | n/a | `src/simulation_quality/` | Ten-pillar simulation-quality scoring and grade anchors (skills `simq-dev`, `simq-audit`). |
| Slow regression, paired arms, RPG gate | n/a | `slow-regression*.yml`, `paired-arms.yml`, `rpg-gate-report.yml` | Long behavioural runs, kept off the shared hosts. |

## 8. Code health (`codebase/`)

All exact pins in the `lint` group, because a new release can move a measured baseline without any code change.

| tool | version | how it is used |
|---|---|---|
| Ruff | `==0.17.0` | Lint and format |
| mypy | `==2.4.0` (dev group) | Type gate. Existing errors are held in `codebase/baselines/mypy_baseline.txt` and filtered by `mypy-baseline==0.7.4` |
| Pyrefly | `==1.3.2` | A second type-checker opinion; advisory, never a gate |
| import-linter | `==2.15` | Layer contracts in `codebase/structure/importlinter.toml`; blocking in the required Code health job since #671 |
| ast-grep | `==0.50.0` | Project rule pack in `codebase/rules/` (binary `ast-grep`, never `sg`) |
| complexipy | `==8.0.1` | Cognitive-complexity report |
| jscpd | `JSCPD_VERSION` in the `Makefile` (Node) | Copy-paste detection |
| prek | `==0.5.5` (dev group) | Opt-in git hooks (`make install-prek-hooks`) |

## 9. Performance

| stack | version policy | where | how it is used |
|---|---|---|---|
| In-house bench harness | n/a | `src/perf/`, `tools/perf/` | Tick-cost baselines, tripwires and capacity runs (`docs/engine/performance_contract.md`). |
| memray | `>=1.0.0` (opt-in `profiling` group) | `tools/perf/` | Memory profiling. |
| py-spy | `>=0.3.14` (opt-in `profiling` group) | `tools/perf/profile_tick.py` | Sampling CPU profiler for a tick. |
| Locust | `==2.46.7` (opt-in `loadtest` group) | `tools/loadtest/` | API load test. No CI job installs it. |

## 10. Packaging, build and dependency hygiene

| stack | where | how it is used |
|---|---|---|
| uv `0.11.2` | `uv.lock`, `[tool.uv]`, CI `setup-uv`, Docker builder stage | The only Python dependency source. Every CI job runs `uv sync --locked`; there is no `requirements.txt` export. Default groups are `dev` and `lint`. |
| npm | `frontend/`, `dashboard-frontend/`, `website/` | Three separate `package-lock.json` files, with no workspace. |
| GNU Make | `Makefile` | Single entry for tasks: tests, knowledge index, docs registry, close-week, merge drivers. |
| Dependabot | `.github/dependabot.yml` | Grouped minor/patch and monthly major PRs for uv, npm, actions, compose and docker (open now: #809-#815). |
| `requirements-knowledge.txt` | repo root | The knowledge venv's hand-built install, outside `uv.lock` (section 11). |

## 11. Containers, runtime and monitoring stack

Base services (`compose.yaml`, always on):

| service | image | role |
|---|---|---|
| `backend` | `docker/backend.Dockerfile` (`uv:0.11.2` builder, `python:3.13.16-slim`) | Engine and API |
| `ai_worker` | same image | Live anomaly worker (`src.observability.anomaly.worker`) |
| `redis` | `redis:8.10.2-alpine` | Event stream broker |
| `frontend` | `docker/frontend.Dockerfile` (node 24 builder, nginx-unprivileged) | Game client |

The `observability` profile (`docker compose --profile observability up`). Every image is pinned by tag and digest:

| service | image | role |
|---|---|---|
| `prometheus` | `prom/prometheus:v3.15.0` (`docker/prometheus.yml`) | Metrics |
| `grafana` | `grafana/grafana:13.2.4` (`docker/grafana/` provisioning and dashboards) | Dashboards |
| `loki` | `grafana/loki:3.7.8` | Logs |
| `alloy` | `grafana/alloy:v1.20.1` (`docker/alloy/config.alloy`) | Log and telemetry collector (replaced Promtail) |
| `tempo` | `grafana/tempo:3.0.3` (`docker/tempo.yaml`) | Traces |
| `ntfy` | `binwiederhier/ntfy:v2.28.0` | Push alerts |
| `redis-exporter` | `oliver006/redis_exporter:v1.93.0` | Redis metrics |
| `node-exporter` | `prom/node-exporter:v1.12.1` | Host metrics |
| `docker-socket-proxy` | `tecnativa/docker-socket-proxy:v0.4.1` | Read-only Docker API for Alloy |
| `watchdog` | backend image, `mem_limit: 256m` | Simulation watchdog poller (`docs/architecture/simulation_watchdog.md`) |

Secrets are Compose secrets (`grafana_admin_password`, `ntfy_topic`, `ntfy_token`), not environment variables.

## 12. Cloud infrastructure (`infra/terraform/`)

| stack | where | how it is used |
|---|---|---|
| Terraform, `hashicorp/aws` provider | `bootstrap/`, `service/` roots with lock files | `bootstrap`: GitHub OIDC provider, IAM roles and policies, and an AWS Budget with a budget action. `service`: ECS cluster, task definition and service, CloudWatch log group, security group with its rules. |
| TFLint + `tflint-ruleset-aws` | `.tflint.hcl`, `iac.yml` | Terraform lint in CI |
| Trivy (config scan) | `iac.yml` | IaC misconfiguration scan |

The design is ADR D1-D10 plus the DevOps amendment (`docs/architecture/devops_plan_amendment_proposal.md`), delivered by
the platform domain.

## 13. CI/CD and supply chain (`.github/workflows/`)

| workflow | stack | purpose |
|---|---|---|
| `test.yml` | setup-uv (Python 3.13), setup-node, CodeQL SARIF upload | Main test and code-health jobs |
| `slow-regression.yml`, `slow-regression-watchdog.yml` | setup-uv | Long regression runs, and a check that the schedule still fires |
| `paired-arms.yml`, `rpg-gate-report.yml` | setup-uv, artifacts | Off-host paired experiment arms and the RPG gate report |
| `security-scan.yml` | Semgrep, Gitleaks, Trivy, CodeQL SARIF | Static analysis, secret scan, vulnerability scan |
| `publish-images.yml` | Docker Buildx, build-push, metadata, login; anchore SBOM; Trivy; cosign | Build, scan, sign and publish images, with an SBOM |
| `iac.yml` | setup-terraform, setup-tflint, Trivy | Terraform validate, lint and scan |
| `deploy-docs.yml` | setup-node, Pages actions | Build and publish the Docusaurus site |
| `pr-body-lint.yml` | checkout only | Checks the PR body shape |

Every third-party action is pinned to a full commit SHA.

## 14. Agent tooling and knowledge search

The multi-agent delivery process: session roles, tickets, workflows, monitoring and semantic search.

| stack | where | how it is used |
|---|---|---|
| Claude Code | `.claude/agents/`, `.claude/skills/`, `.claude/settings.json`, `CLAUDE.md` | Session role cards (generated from `registries/session_roles.yaml`), subagent roles, skills and hooks |
| Workflow scripts (JavaScript) | `.claude/workflows/*.js` | `implement-ticket`, `implement-epic`, `create-tickets`, `simq-audit` and the simulation-lab workflows |
| MCP (Python SDK `mcp>=1.30.0,<2`) | `tools/search_mcp.py`, `.mcp.json` | MCP servers: `knowledge-search` (local), `github` (`ghcr.io/github/github-mcp-server` in Docker), `headroom` (trial), `aseprite-pixel-art` |
| sentence-transformers | `knowledge` extra; `tools/knowledge_search.py`, `search_mcp.py`, `search_server.py` | Embeddings for semantic search over docs, tickets and investigations |
| sqlite-vec | same three files | Vector index |
| rank-bm25 | `tools/knowledge_search.py` | Lexical half of hybrid search |
| torch (CPU wheel) | `.venv-knowledge` (Python 3.12), `requirements-knowledge.txt` | Backs sentence-transformers. Installed by hand, outside the lock (finding F3) |
| graphify | `graphify-out/` | Code knowledge graph: query, path, explain |
| JSONL + DuckDB | `agent-working/agent-monitoring/data/YYYY-Www/` | Run, event and tool shards per week; `duckdb_view.py` queries them |
| Python tool suite | `tools/` | Gate checks, validators, registries (`layer_registry.py`, `tag_registry.py`), delivery helpers |

## 15. Visual assets (`visual_assets/`)

| stack | where | how it is used |
|---|---|---|
| Aseprite + Lua | `visual_assets/drawing/` (backend, compose, palettes) | Pixel-art drawing through typed operations and hash-pinned Lua scripts |
| bubblewrap (`bwrap`) | `visual_assets/start_mcp.sh` | Sandbox for the drawing process |
| MCP server | `aseprite-pixel-art` in `.mcp.json` | Agent-facing drawing tools that write immutable revisions and never write the catalog |
| Asset store and catalog | `visual_assets/store/`, `catalog/`; client in `frontend/src/visualAssets/` | Versioned asset sets the client adopts (ADR `docs/architecture/visual_asset_foundation_adr.md`, D1-D23) |

## Findings from this pass (advice)

The 2026-10-11 seed review is out of date on three points: Redis is now pinned to `8.10.2-alpine` by digest (its
finding 5), mypy is pinned `==2.4.0` (finding 1), and Promtail has been replaced by Alloy.

| # | finding | recommendation | owner |
|---|---|---|---|
| F1 | The two React apps no longer match. `frontend/` is on Vite 8, plugin-react 6 and Vitest 5; `dashboard-frontend/` is on Vite 7, plugin-react 5 and Vitest 4. The seed review's finding 4 ("versions match today") no longer holds. | Bring the dashboard up to the client's majors in one PR; the open Dependabot npm-major PR #811 covers only `frontend/`. Still no workspace. | lead (dashboard) |
| F2 | `pandas` is imported lazily in `src/observability/mining/dataset.py` but is declared nowhere in `pyproject.toml`. | Declare it in an extra, or replace it with DuckDB or PyArrow, which are already runtime dependencies. | rpg |
| F3 | Seed finding 2 still holds: `uv.lock` resolves torch's CUDA build while `.venv-knowledge` uses a hand-installed CPU wheel on Python 3.12. | Unchanged; tracked on #514. | agent-working |
| F4 | `hypothesis` and `httpx` are declared in `dev` but have no top-level import in `tests/`. | Check whether they are used through fixtures or lazy imports before removing either one. | testing |
