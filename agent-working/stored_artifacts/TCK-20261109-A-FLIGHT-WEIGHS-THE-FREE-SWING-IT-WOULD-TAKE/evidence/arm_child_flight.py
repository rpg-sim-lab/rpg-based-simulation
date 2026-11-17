"""One run of one arm (flight guard measurement, TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE): build the pinned kernel (audit_mode, no frame pacing), run it, and write a small JSON of typed facts (never a raw event dump).

Executed by ``paired.py`` with the ARM'S source tree as the working directory and on PYTHONPATH, so it must import only what every arm tree has
(``tools.test_architecture.rpg_gate_run.build_kernel``, the engine, ``keeps_coin``). Counters that an older arm tree does not record are written as null,
never as zero.

Usage: python arm_child.py <world> <seed> <ticks> <out.json>
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

LEDGER_TALLY = "rpg_gate_ledger_tally"
STARVATION_EVENTS = ("starvation_channel_live", "starvation_death_record", "starvation_channel_tally")


def _cause(entity) -> str | None:
    """The typed cause recorded at death (``death_record``), else the older passive cause or reason string (``legacy:``), else None while alive."""
    if entity.combat.alive:
        return None
    record = getattr(entity.lifecycle, "death_record", None)
    if record is not None:
        return str(getattr(record.cause, "value", record.cause))
    legacy = getattr(entity.lifecycle.passive_death_cause, "value", None) or entity.lifecycle.death_reason or "unknown"
    return f"legacy:{legacy}"


def _roster(state, keeps_coin) -> list:
    return [[e.id, e.kind, int(bool(keeps_coin(e))), int(e.combat.alive)] for e in sorted(state.entities.values(), key=lambda x: x.id)]


def _tally(run_dir: Path) -> dict | None:
    path = run_dir / "simulation_events.jsonl"
    if not path.exists():
        return None
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if LEDGER_TALLY in line:
            found = json.loads(line).get("payload")
    return found


def _starvation(run_dir: Path) -> list:
    path = run_dir / "simulation_events.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if any(name in line for name in STARVATION_EVENTS):
            ev = json.loads(line)
            if ev.get("event_type") in STARVATION_EVENTS:
                out.append({"event_type": ev["event_type"], "tick": ev.get("tick"), "entity_id": ev.get("entity_id"), "payload": ev.get("payload")})
    return out


def _install_counters() -> dict:
    """Spies only: they call the real functions and return their results unchanged.

    ``flight_weighs_free_swing`` (fix tree only): every (site, fired) pair, the response of each fire (ATTACK / HOLD_BETWEEN_BLOWS / HOLD_TILE), the first two fire rows per
    site and a compact list of every fire (tick, subject, site, response) for the alive-at-t+20 read. ``MovementPhase._swap_updates``: swaps, and swaps in which a side was
    engaged with a hostile and landed on a tile no longer adjacent to any of those hostiles."""
    from src.engine import tactical
    from src.engine.pipeline_phases.movement import MovementPhase
    from src.engine.legality import LegalityServiceV2

    counts = {"has_guard": hasattr(tactical, "flight_weighs_free_swing"), "calls": {}, "fires": {}, "responses": {}, "rows": {}, "fire_list": [],
              "swaps": 0, "swap_engaged_side": 0, "swap_engaged_leaving": 0}
    if counts["has_guard"]:
        real = tactical.flight_weighs_free_swing

        def spy(state, entity, update, site):
            out = real(state, entity, update, site)
            name = getattr(site, "name", str(site))
            counts["calls"][name] = counts["calls"].get(name, 0) + 1
            if update is not None and out is not update:
                payload = (out.task.payload_set or {}) if out.task else {}
                response = "ATTACK" if payload.get("action") == "ATTACK" and payload.get("reason") != "HOLD_BETWEEN_BLOWS" else ("HOLD_BETWEEN_BLOWS" if payload.get("reason") == "HOLD_BETWEEN_BLOWS" else "HOLD_TILE")
                counts["fires"][name] = counts["fires"].get(name, 0) + 1
                counts["responses"][response] = counts["responses"].get(response, 0) + 1
                row = {"tick": state.tick, "subject": entity.id, "felt_blow": entity.combat.last_hit_damage, "hp": entity.combat.hp, "attacker": entity.combat.last_attacker_id, "response": response}
                rows = counts["rows"].setdefault(name, [])
                if len(rows) < 2:
                    rows.append(row)
                if len(counts["fire_list"]) < 20000:
                    counts["fire_list"].append([state.tick, entity.id, name, response])
            return out
        tactical.flight_weighs_free_swing = spy

    real_swap = MovementPhase._swap_updates

    def spy_swap(state, a, b, a_existing, b_existing):
        counts["swaps"] += 1
        for who, other in ((a, b), (b, a)):
            engaged = LegalityServiceV2.get_engaged_hostiles(who, state)
            if engaged:
                counts["swap_engaged_side"] += 1
                px, py = other.navigation.position
                near = any(abs(state.entities[e].navigation.position[0] - px) + abs(state.entities[e].navigation.position[1] - py) == 1 for e in engaged if e in state.entities and e != other.id)
                counts["swap_engaged_leaving"] += int(not near)
        return real_swap(state, a, b, a_existing, b_existing)
    MovementPhase._swap_updates = staticmethod(spy_swap)
    return counts


def _stripped_hash(state) -> str:
    """The end digest with ``last_hit_damage`` dropped from every CombatComponent canonical dict. (The scheme label is not part of the hashed JSON; the label is normalised by
    not reading it: only this value is compared.) On a tree without the field this equals the plain hash."""
    import hashlib
    from src.engine.checkpoint import CanonicalStateHasher
    data = CanonicalStateHasher.to_canonical_data(state)
    for entity in data["entities"].values():
        entity["combat"].pop("last_hit_damage", None)
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.serves import keeps_coin
    from tools.test_architecture.rpg_gate_run import build_kernel

    counts = _install_counters()
    run_id = f"rpgm_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this arm's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    start = _roster(kernel.state, keeps_coin)
    start_hash = CanonicalStateHasher.get_hash(kernel.state)
    alive_t20: dict = {}
    due: dict = {}
    seen = 0
    for _ in range(ticks):
        kernel.tick_once()
        cur = kernel.state
        for fire_tick, subject, _site, _resp in counts["fire_list"][seen:]:
            due.setdefault(fire_tick + 20, []).append((fire_tick, subject))
        seen = len(counts["fire_list"])
        for fire_tick, subject in due.pop(cur.tick, []):
            ent = cur.entities.get(subject)
            alive_t20[(fire_tick, subject)] = int(bool(ent is not None and ent.combat.alive))
    state = kernel.state
    kernel.shutdown()
    run_dir = Path("data") / "runs" / run_id
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8")) if (run_dir / "run_manifest.json").exists() else {}
    tally = _tally(run_dir)
    final = {str(e.id): [int(e.combat.alive), _cause(e), e.kind] for e in state.entities.values()}
    doc = {
        "world": world, "seed": seed, "ticks": ticks, "hashseed": os.environ.get("PYTHONHASHSEED"),
        "start_hash": start_hash, "final_hash": CanonicalStateHasher.get_hash(state),
        "forced_flags": forced, "audit_mode": manifest.get("audit_mode"), "signals_zeroed": manifest.get("signals_zeroed"),
        "start": start, "final": final,
        "counters": (tally or {}).get("behaviour") if tally and "behaviour" in tally else None,
        "perception_samples": (tally or {}).get("perception_samples"),
        "adds": (tally or {}).get("adds"),
        "starvation_events": _starvation(run_dir),
        "flight_counts": counts, "alive_t20": [[k[0], k[1], v] for k, v in sorted(alive_t20.items())], "stripped_final_hash": _stripped_hash(state),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    shutil.rmtree(run_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
