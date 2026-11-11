"""Near-death hardening counts (rpg-implementer-3, DRAFT for rpg-planner review; not run, not smoked). TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT.
Read-only. Same build (tools.test_architecture.rpg_gate_run.build_kernel, audit_mode / no_frame_pacing checked) and tick loop as arm_child / hit_gap2; run with the arm's tree as cwd and PYTHONPATH.
Spy 1: NearDeathHardeningPhase.apply (src/engine/pipeline_phases/hardening.py) is wrapped by an append-only function: it calls the original, returns ITS object unchanged, and only reads
(state, input update, output update). A GRANT = an entity whose OUTPUT combat trace holds NEAR_DEATH_HARDENING and whose INPUT combat trace did not. Row per grant: tick (state.tick at the call),
entity id, kind, hp / max_hp before, projected hp, and the INPUT CombatUpdate's fields: hp_delta, damage_taken, hazard_damage, attacker_id, hit_tick_set, outcome_kind, max_hp_delta, permanent_max_hp_bonus_delta
(the +5 is added by the phase itself), the entity's last_hit_tick before, its position tile and whether the tile is in state.town_tiles.
Source class (derived after the run from those fields, ambiguity kept): hp_delta < 0 -> 'neg:hit' (damage_taken > 0 or attacker_id set), 'neg:hazard' (hazard_damage > 0, no hit fields), 'neg:other'.
hp_delta >= 0 -> 'heal:town' (hp_delta == 1 and the tile is a town tile: town_resolution.py Part A, PASSIVE_HEAL_AMT), 'heal:lodging' (hp_delta == 5: lodging.py:158), 'heal:levelup' (hp_delta a positive multiple
of 20: evolution.py:131), 'heal:consume' (input max_hp_delta > 0 with hp_delta == max_hp_delta: core_actions.py:398), 'heal:other' (rest). hp_delta == 0 is 'zero'. A merged update that fits two classes is
recorded under the first matching class and flagged in 'ambiguous' (the raw fields stay in the row so the split can be redone).
Spy 2 (per tick, after tick_once, reads only): for every entity that has a grant so far or is a person, counts panic ticks = task payload reason == 'PANIC_RETREAT' (the reason the SURV-07 reading uses) and
ticks with emotion.panic >= 0.5; also the first/last tick alive and max_hp at start and end. Person = not hostility.is_wild_creature.
Output JSON: grants rows, per-run counts split (hit / non-hit) by class, per-subject summary {kind, n_hit_grants, n_nonhit_grants, max_hp_start/end, nonhit_hp_gained (5 per non-hit grant), panic_ticks,
emotion_panic_ticks, alive_at_end, cause (arm_child._cause)}, group comparison (subjects with any non-hit grant vs hit-only: n, panic ticks sum/mean, deaths, deaths by cause), final_hash.
Usage: python hard_count.py <world> <seed> <ticks> <out.json> [<expected final_hash>]. Exit 3 on a hash mismatch (when given) -- then the run does not count."""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path

def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    want = argv[4] if len(argv) > 4 else None
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.hostility import is_wild_creature
    from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase
    from tools.rpg_measure.arm_child import _cause
    from tools.test_architecture.rpg_gate_run import build_kernel
    run_id = f"rpghard_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD"); return 2
    grants = []
    orig = NearDeathHardeningPhase.apply
    def spy(state, update):
        res = orig(state, update)
        for eid, eu in res.entity_updates.items():
            c = eu.combat
            if c is None or "NEAR_DEATH_HARDENING" not in c.trace:
                continue
            cin = update.entity_updates[eid].combat if eid in update.entity_updates else None
            if cin is not None and "NEAR_DEATH_HARDENING" in cin.trace:
                continue
            e = state.entities[eid]
            pos = e.navigation.position
            tile = (int(pos[0]), int(pos[1]))
            grants.append({"tick": state.tick, "e": eid, "kind": e.kind, "hp": e.combat.hp, "max_hp": e.combat.max_hp, "proj": c.trace.get("NEAR_DEATH_PROJECTED_HP"),
                           "hp_delta": cin.hp_delta, "damage_taken": cin.damage_taken, "hazard_damage": cin.hazard_damage, "attacker_id": cin.attacker_id, "hit_tick_set": cin.hit_tick_set,
                           "outcome": cin.outcome_kind, "max_hp_delta_in": cin.max_hp_delta, "perm_in": cin.permanent_max_hp_bonus_delta, "last_hit_tick": e.combat.last_hit_tick,
                           "tile": list(tile), "town_tile": tile in state.town_tiles, "wild": bool(is_wild_creature(e))})
        return res
    NearDeathHardeningPhase.apply = staticmethod(spy)
    panic_t, emo_t, start_max = {}, {}, {}
    state = kernel.state
    try:
        for _ in range(ticks):
            kernel.tick_once()
            st = kernel.state
            for e in st.entities.values():
                if not e.combat.alive:
                    continue
                start_max.setdefault(e.id, e.combat.max_hp)
                p = e.task.payload or {}
                if p.get("reason") == "PANIC_RETREAT":
                    panic_t[e.id] = panic_t.get(e.id, 0) + 1
                try:
                    if e.cognition.subjective.emotion.panic >= 0.5:
                        emo_t[e.id] = emo_t.get(e.id, 0) + 1
                except Exception:
                    pass
        state = kernel.state
    finally:
        NearDeathHardeningPhase.apply = orig
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    def klass(g):
        d = g["hp_delta"]; amb = []
        if d < 0:
            c = "neg:hit" if (g["damage_taken"] > 0 or g["attacker_id"] is not None) else ("neg:hazard" if g["hazard_damage"] > 0 else "neg:other")
            return c, amb
        cands = []
        if d == 1 and g["town_tile"]: cands.append("heal:town")
        if d == 5: cands.append("heal:lodging")
        if d > 0 and d % 20 == 0: cands.append("heal:levelup")
        if g["max_hp_delta_in"] > 0 and d == g["max_hp_delta_in"]: cands.append("heal:consume")
        if d == 0: cands.append("zero")
        if not cands: cands.append("heal:other")
        return cands[0], cands[1:]
    cnt = {}
    for g in grants:
        g["cls"], g["ambiguous"] = klass(g)
        g["hit"] = g["hp_delta"] < 0
        cnt[g["cls"]] = cnt.get(g["cls"], 0) + 1
    subj = {}
    for g in grants:
        s = subj.setdefault(g["e"], {"kind": g["kind"], "wild": g["wild"], "n_hit": 0, "n_nonhit": 0})
        s["n_hit" if g["hit"] else "n_nonhit"] += 1
    for eid, s in subj.items():
        e = state.entities.get(eid)
        s.update(max_hp_start=start_max.get(eid), max_hp_end=None if e is None else e.combat.max_hp, nonhit_hp_gained=5 * s["n_nonhit"],
                 panic_ticks=panic_t.get(eid, 0), emotion_panic_ticks=emo_t.get(eid, 0), alive_at_end=None if e is None else bool(e.combat.alive), cause=None if e is None else _cause(e))
    def grp(sel):
        ids = [i for i, s in subj.items() if sel(s) and not s["wild"]]
        dead = [i for i in ids if not subj[i]["alive_at_end"]]
        causes = {}
        for i in dead: causes[subj[i]["cause"]] = causes.get(subj[i]["cause"], 0) + 1
        pt = [subj[i]["panic_ticks"] for i in ids]; et = [subj[i]["emotion_panic_ticks"] for i in ids]
        return {"n": len(ids), "deaths": len(dead), "deaths_by_cause": causes, "panic_ticks_sum": sum(pt), "panic_ticks_mean": (sum(pt) / len(pt)) if pt else None,
                "emotion_panic_ticks_sum": sum(et), "emotion_panic_ticks_mean": (sum(et) / len(et)) if et else None}
    nonhit_gain = sorted(((s["nonhit_hp_gained"], i) for i, s in subj.items() if s["n_nonhit"]), reverse=True)
    res = {"world": world, "seed": seed, "ticks": ticks, "final_hash": final_hash, "grants_total": len(grants), "grants_hit": sum(1 for g in grants if g["hit"]),
           "grants_nonhit": sum(1 for g in grants if not g["hit"]), "by_class": cnt,
           "groups": {"any_nonhit": grp(lambda s: s["n_nonhit"] > 0), "hit_only": grp(lambda s: s["n_nonhit"] == 0 and s["n_hit"] > 0)},
           "nonhit_hp_gain": {"largest": nonhit_gain[0] if nonhit_gain else None, "total": sum(x for x, _ in nonhit_gain), "subjects": len(nonhit_gain)},
           "subjects": {str(i): s for i, s in subj.items()}, "grants": grants}
    Path(out).write_text(json.dumps(res, sort_keys=True), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    ok = want is None or final_hash == want
    print(("MATCH " if ok else "MISMATCH ") + final_hash[:12] + f" grants={len(grants)} nonhit={res['grants_nonhit']} classes={json.dumps(cnt)}")
    return 0 if ok else 3

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
