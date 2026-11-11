# Deterministic Concurrent RPG Engine

A 2D fantasy world simulation in Python with a React client. Autonomous simulated entities (adventurers, townsfolk, monsters, factions) eat, sleep, work, trade, craft, fight, form groups and pursue long-term goals. The world around them changes too: resources deplete and regrow, regions carry the trauma of past events, and calamities strike.

The engine is built so that a run can be examined after the fact. Every change to the world goes through one authoritative path, so each change has a typed record and a single place where it was applied. The same seed and starting state replay to the same state hash, within a stated scope. That makes emergent behaviour (a starvation, a faction war, an economic collapse) something you can reproduce, trace and compare across code changes, rather than a one-off.

The simulated entities are not the coding agents described under [AI-first engineering workflow](#ai-first-engineering-workflow). The first are part of the simulated world; the second are the development process that builds it.

---

## Core capabilities

| Capability | What exists today | Spec |
|---|---|---|
| Entity behaviour | Biological needs, a goal hierarchy with interruption resistance, bounded knowledge and perception, social and political ties | [Mechanics Bible](docs/mechanics/) ch. 01, 04, 07 |
| Combat | A deterministic damage formula, tactical modifiers and durability decay | ch. 02 |
| Economy | Harvesting, trade and crafting under atomic conservation (items and gold are moved, never created or lost) | ch. 03 |
| World evolution | Tick-to-day time, regional trauma, ecology, calamities | ch. 05 |
| Authoritative updates | AI decisions can run concurrently on workers; every proposed change is validated and applied in one synchronous phase | [Kernel](docs/engine/kernel.md), [Authoritative Pipeline](docs/engine/authoritative_pipeline.md) |
| Reproducible runs | A seeded, order-independent RNG and a SHA-256 proof digest of the whole state, guaranteed only in the scope below | [Deterministic Execution Contract](docs/engine/deterministic_execution.md) |
| Load governance | A governor moves the tick between NORMAL, CONSTRAINED, DEGRADED and SURVIVAL modes under load and sheds optional work | [Resource governor contract](docs/engine/contracts/resource_governor_contract.md) |
| Observability and evaluation | Simulation events, Prometheus metrics, hard-law invariant checks every tick, and Simulation Quality scoring of runs against anchors | [docs/observability/](docs/observability/) |

---

## Quick Start

```bash
make install    # Install all dependencies (Python + Node)
make serve      # Build frontend + start server at :8000
make cli        # Run a headless simulation (200 ticks)
```

**Requirements:** Python ≥ 3.12, Node.js ≥ 18, Docker (optional, for the telemetry stack). On Windows, run `make` under WSL or Git Bash (there is no `make.bat`).

---

## Running the Engine

### Server mode: visual client at `http://127.0.0.1:8000`
```bash
python3 -m src serve --seed 42 --workers 4
make dev        # backend + frontend dev server with hot reload
```

### Headless CLI mode
```bash
python3 -m src cli --seed 42 --ticks 1000
SIM_OBS_MODE=DEBUG python3 -m src cli --ticks 100 --seed 42   # full observability
```

See [docs/guides/simulation.md](docs/guides/simulation.md) for world authoring, CLI flags, and artifact paths. Full CLI reference: [docs/observability/how_to_run_simulation.md](docs/observability/how_to_run_simulation.md).

---

## Architecture

Each tick runs a fixed sequence of phases in the `Kernel` (`src/engine/kernel.py`). The two that matter most:

- **Propose.** In the Collection phase, entity AI runs on a read-only frozen view of the state, possibly on several workers at once, and returns proposals. It changes nothing.
- **Refine and apply.** In the Resolution phase, every proposal is sorted into a fixed order and goes through the `AuthoritativeApplyPipeline`, which validates it against the current state and applies the accepted ones as typed updates. This is the only place durable state changes, so the result does not depend on which worker finished first.

| Principle | Summary |
|---|---|
| **Determinism** | Stateless seeded RNG: `DeterministicRNG` seeds a fresh `random.Random` per draw from the run seed, domain, tick and entity. A SHA-256 canonical state hash is the proof. |
| **Immutable state** | `AuthoritativeState` and each entity's typed components are frozen dataclasses; a tick produces a new state instead of editing the old one ([docs/core/](docs/core/)) |
| **Read projection for the API** | The API never reads the engine's working state. After each tick, the engine thread publishes the new state and an updated read-model cache under a lock; REST and WebSocket handlers read that published copy through the cache and presenters. It runs in the same process, so a slow read can briefly delay the next publish. |
| **Content pipeline** | World modules, compositions and archetypes are resolved through a typed content pipeline before runtime |

Core laws: [Simulation Kernel](docs/engine/kernel.md) · [Authoritative Pipeline](docs/engine/authoritative_pipeline.md) · [Project Lawbook](docs/engine/project_lawbook_m10.md)

---

## Verification and reproducibility

The guarantee is narrower than "every run is deterministic". It is guaranteed for the same build, Python minor version, OS and CPU architecture, using the sequential executor under the Canonical signal contract (tier DET-PORT-0). Concurrent executors and other platforms are claimed only where a parity test covers them. The default Live contract reads the wall clock and host load, so two Live runs can differ. The [Deterministic Execution Contract](docs/engine/deterministic_execution.md) gives the full scope and its known gaps.

- [`make replay-check`](docs/guides/reviewer_replay_check.md) runs one seed twice under the Canonical contract and compares the final state hashes. It is a short-run demonstration, not a proof.
- Limits and known defects: [docs/engine/known_limitations.md](docs/engine/known_limitations.md).

---

## Documentation Site

`website/` holds a Docusaurus 3 wiki for someone watching the simulation run, with three spaces: **World Knowledge** (generated at build time from the world rules, the mechanism registry and the content catalog), **Technical** and **Control Guide** (both filled later). It does not render `docs/`. It is built locally and is not published at the moment: the GitHub Pages deploy runs only by hand and Pages is not enabled (`TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`). Details: [docs/README.md](docs/README.md).

```bash
make docs-serve      # Start site at http://localhost:3000
make docs-build      # Build static site (website/build/)
make docs-registry   # Regenerate docs/REGISTRY.yaml after adding new docs
```

**How docs are classified:** every `.md` file carries a YAML frontmatter block (`status`, `layer`, `authority`, `audience`). The schema is defined in [`docs/guidelines/frontmatter_schema.md`](docs/guidelines/frontmatter_schema.md). Run `python3 tools/validate_frontmatter.py <path>` to check any file or directory.

**Machine-readable index:** [`docs/REGISTRY.yaml`](docs/REGISTRY.yaml) is a generated flat list of all tagged docs and closed tickets. Agents and scripts query it instead of scanning the tree.

---

## Documentation Reference

| Area | Location |
|---|---|
| **Developer guides** (how-to, quickstarts) | [`docs/guides/`](docs/guides/) |
| Mechanics Bible (simulation laws and formulas) | [`docs/mechanics/`](docs/mechanics/) |
| Engine contracts and kernel spec | [`docs/engine/`](docs/engine/) |
| Core state, entities, attributes | [`docs/core/`](docs/core/) |
| Architecture decisions (ADRs) | [`docs/architecture/`](docs/architecture/) |
| Observability and how to run | [`docs/observability/`](docs/observability/) |
| Compliance, parity ledger, divergences | [`docs/parity_ledger/`](docs/parity_ledger/) · [`docs/guidelines/`](docs/guidelines/) |
| Design patterns and coding conventions | [`docs/guidelines/design_patterns.md`](docs/guidelines/design_patterns.md) |
| AI-first engineering workflow | [`docs/ai/`](docs/ai/) |

Full doc index: [docs/README.md](docs/README.md)

---

## Testing

```bash
pytest tests/unit/            # unit tests (fast)
pytest tests/ -m "not slow"   # exclude long integration runs
```

Resource budgets (for memory/timeout control in constrained environments):
```bash
pytest tests/ --resource-budget=small    # 1 GB RAM, 15s timeout
pytest tests/ --resource-budget=medium   # 4 GB RAM, 60s timeout (default)
pytest tests/ --resource-budget=large    # 8 GB RAM, for long calibration tests
pytest tests/ --resource-budget=off      # no limits
```

Never run `pytest tests/` without scoping — scope to the domain under change. See [testing taxonomy](docs/testing/test_taxonomy.md).

---

## AI-first engineering workflow

The project is developed with an AI-first workflow: development agents work in defined roles (planning, implementation, review) under rules kept in the repository. Its purpose is:

- **Coordination:** work is split into tickets with scope and acceptance criteria, and each role owns a defined set of files.
- **Gates:** a ticket passes scoping, investigation, planning, review, tests and a definition-of-done check before it closes. A failing gate is reported, not worked around.
- **Traceability:** every ticket, plan, investigation and run is recorded under `agent-working/`, and every commit names its ticket.
- **Knowledge search:** a semantic index over docs and tickets, and a code graph, are queried before any change.

None of this replaces tests or review; it is how the work is organised. See [docs/ai/](docs/ai/) for roles, workflows and gates.

---

## Infrastructure (Optional)

Docker Compose (`compose.yaml` at the root; Dockerfiles and ops configs in `docker/`) runs two profiles. The only broker is
Redis Streams; there is no Kafka or RabbitMQ (`docs/architecture/devops_baseline_adr.md`).

```bash
docker compose up -d                                  # backend, redis, ai_worker, frontend
docker compose --profile observability up -d          # adds Prometheus, Grafana, Loki, Alloy (log shipping), Tempo, ntfy and the exporters
# Grafana: http://localhost:3000 (set GRAFANA_PORT if the docs site uses 3000; user admin; the password is the gitignored secret file docker/secrets/grafana_admin_password)
```

Tempo runs in that profile, but the simulation code does not emit trace spans yet. The observability profile needs its secret files first (Grafana password, ntfy topic and token): the steps are in the header of
`compose.yaml`. Alerts, drills and first checks are in [`docs/runbooks/`](docs/runbooks/README.md).

---

## License and contributing

The code is public but not open source: [LICENSE](LICENSE) is All Rights Reserved, with provisions for versions previously released under MIT. See [CONTRIBUTING.md](CONTRIBUTING.md) for engineering rules. Tickets live in [`agent-working/tickets/`](agent-working/tickets/).
