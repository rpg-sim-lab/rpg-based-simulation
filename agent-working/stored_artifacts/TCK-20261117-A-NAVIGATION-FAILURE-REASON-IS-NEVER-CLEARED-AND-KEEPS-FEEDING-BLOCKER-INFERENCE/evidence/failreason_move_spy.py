#!/usr/bin/env python3
"""Stale-failure-reason RERUN spy (DRAFT for designer approval; NOT run). READ-ONLY: every hook calls the original unchanged and returns its result untouched; the per-tick scan only reads kernel.state.
Same build/kit as the v1 spy (failreason_spy_8d711da2): tools.test_architecture.rpg_gate_run.build_kernel, audit_mode / no_frame_pacing checked, PINNED run manifest (exit 2 otherwise), root ERROR+ logging
count, kernel.shutdown in a finally. Usage: <world> <seed> <ticks> <out.json> [PLAIN | expected_final_hash] (PLAIN = no hook, the twin; a hash = the spy run must end on it, exit 3 otherwise).
cwd = the tree under test, PYTHONPATH = that tree. Exit 4 = a required hook target was not found (nothing ran).

Bars (rpg-designer, rpg-designer-stalereason-rerun-bars.md sha256 6771e32f..., fixed before data), per cell:
  L1  at the navigation patch apply (NavigationPatch.apply), per call (eid, tick): post last_failure_reason != (the merged update's code if any, else None if the clear is set, else the pre value) = 0.
  M1  a body whose position changed through the movement apply path (not lodge entry/exit) ends the tick with a non-None reason that has NO same-tick NON-movement writer of that code = 0.
  M2  a body that moved and ends the tick with a non-None reason that has NO same-tick writer of that code at all (movement or not) = 0. (M2 rows are a subset of M1 rows.)
  R2  a blocker filed by infer_blockers from PATH_NOT_FOUND / STUCK / OSCILLATING while the subject's latest applied outcome was a move = 0.
  Not vacuous: reasons_set >= 1 and reasons_cleared >= 1 per cell; moves of each kind (step, swap, yield) are REPORTED per cell (the >= 1 in at least one cell is read across cells).
REPORTED: action-code rows after a move per writer (the first writer in call order is the primary: the innermost call returns first), yields and swaps per cell, OCCUPANCY_CONFLICT rejections, moves with no
attributed kind, v1 R1 / R3 (the same definitions as the v1 spy, resolve_move-only, kept for comparison, NOT bars), the blocker counts v1 reported, and the hook coverage.
Writer categories: core_actions / action_router / combat / skill / aoe / lodging (module and class functions that RETURN an EntityUpdate or a dict of them), occupancy / actor_validity / trust (a phase whose
output update gained or changed a code), movement:* (resolve_move, the yield builder, the swap builder).
"""
from __future__ import annotations

import inspect
import json
import os
import sys
from collections import Counter, defaultdict

CAP = 400
ACCESS_CODES = ("PATH_NOT_FOUND", "STUCK", "OSCILLATING")
MOVEMENT_PREFIX = "movement:"


def val(x):
    return getattr(x, "value", x)


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    mode_arg = argv[4] if len(argv) > 4 else None
    plain = mode_arg == "PLAIN"
    want = None if plain else mode_arg
    from pathlib import Path

    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    run_id = f"rpgmovesp_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD")
        return 2
    import importlib.util
    import logging

    cur = {"tick": 0}
    pp_path = Path("tools") / "test_architecture" / "pinned_runner.py"
    spec = importlib.util.spec_from_file_location("_movesp_pinned_runner", pp_path)
    pinned_runner = importlib.util.module_from_spec(spec)
    sys.modules["_movesp_pinned_runner"] = pinned_runner
    spec.loader.exec_module(pinned_runner)
    manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
    evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {}
    verdict = pinned_runner.classify_manifest(evidence)
    if not verdict.pinned:
        print("NOT_PINNED " + "; ".join(verdict.differences))
        return 2
    log_rows, log_count = [], [0]

    class _Err(logging.Handler):
        def emit(self, record):
            log_count[0] += 1
            if len(log_rows) < CAP:
                log_rows.append({"logger": record.name, "level": record.levelname, "message": record.getMessage()[:300], "tick": cur["tick"]})

    logging.getLogger().addHandler(_Err(level=logging.ERROR))
    exc = Counter()
    exc_rows = defaultdict(list)

    def note(hook):
        exc[hook] += 1
        if len(exc_rows[hook]) < 20:
            et, ev, tb = sys.exc_info()
            while tb is not None and tb.tb_next is not None:
                tb = tb.tb_next
            fr = f"{os.path.basename(tb.tb_frame.f_code.co_filename)}:{tb.tb_lineno}:{tb.tb_frame.f_code.co_name}" if tb is not None else "unknown"
            exc_rows[hook].append({"type": et.__name__ if et else None, "message": str(ev)[:300], "frame": fr, "tick": cur["tick"]})

    c = Counter()
    l1, m1, m2, r1, r2, r3, unkinded = [], [], [], [], [], [], []
    writers = defaultdict(list)       # eid -> [(writer name, code str)] written this tick (cleared each tick)
    moves = defaultdict(set)          # eid -> move kinds proposed this tick: step / swap / yield
    tick_last = {}                    # eid -> outcome of the LAST resolve_move call this tick (v1 definition)
    applied_latest = {}               # eid -> "move" | "stay": the latest applied movement outcome
    after_move_by_writer = Counter()  # reported: action codes left after a move, by primary writer
    after_move_by_code = Counter()
    filed = Counter()
    prev_reason, prev_pos, prev_lod = {}, {}, {}
    blocker_ids = defaultdict(set)
    removed_tick = {}
    refiled = []
    coverage = {"wrapped": [], "missing": []}

    if not plain:
        import functools

        from src.engine.movement import MovementSystem
        from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

        def items_of(res):
            if isinstance(res, dict):
                return [(k, v) for k, v in res.items() if isinstance(k, int)]
            if hasattr(res, "entity_id") and hasattr(res, "navigation"):
                return [(res.entity_id, res)]
            return []

        def record(name, res):
            for eid, u in items_of(res):
                nav = getattr(u, "navigation", None)
                fr = getattr(nav, "failure_reason", None) if nav is not None else None
                if fr is not None:
                    writers[eid].append((name, str(val(fr))))

        def make_returns_wrapper(name, orig):
            @functools.wraps(orig)
            def w(*a, **kw):
                res = orig(*a, **kw)
                try:
                    record(name, res)
                except Exception:
                    note("writer:" + name)
                return res
            return w

        def make_diff_wrapper(name, orig, update_arg_index):
            @functools.wraps(orig)
            def w(*a, **kw):
                res = orig(*a, **kw)
                try:
                    before = (a[update_arg_index] if len(a) > update_arg_index else kw.get("update")).entity_updates
                    for eid, u in res.entity_updates.items():
                        nav = getattr(u, "navigation", None)
                        fr = getattr(nav, "failure_reason", None) if nav is not None else None
                        if fr is None:
                            continue
                        bu = before.get(eid)
                        bnav = getattr(bu, "navigation", None) if bu is not None else None
                        bfr = getattr(bnav, "failure_reason", None) if bnav is not None else None
                        if bfr != fr:
                            writers[eid].append((name, str(val(fr))))
                            if str(val(fr)) == "OCCUPANCY_CONFLICT":
                                c["occupancy_conflict_rejections"] += 1
                except Exception:
                    note("phase:" + name)
                return res
            return w

        def rebind_everywhere(orig, new):
            n = 0
            for modname, mod in list(sys.modules.items()):
                if mod is None or not modname.startswith("src."):
                    continue
                try:
                    for attr, obj in list(vars(mod).items()):
                        if obj is orig:
                            setattr(mod, attr, new)
                            n += 1
                except Exception:
                    note("rebind")
            return n

        def wrap_class_statics(cls, category):
            for attr, raw in list(vars(cls).items()):
                if isinstance(raw, staticmethod) and callable(raw.__func__):
                    setattr(cls, attr, staticmethod(make_returns_wrapper(f"{category}.{attr}", raw.__func__)))
                    coverage["wrapped"].append(f"{cls.__name__}.{attr}")

        def wrap_module_funcs(mod, category):
            for attr, obj in list(vars(mod).items()):
                if inspect.isfunction(obj) and obj.__module__ == mod.__name__:
                    new = make_returns_wrapper(f"{category}.{attr}", obj)
                    setattr(mod, attr, new)
                    rebind_everywhere(obj, new)
                    coverage["wrapped"].append(f"{mod.__name__}.{attr}")

        required = []

        # --- movement writers: the step (v1 wrapper, same outcome definition), the yield builder, the swap builder
        o_rm = MovementSystem.__dict__["resolve_move"].__func__

        def rm_spy(state, entity, target, *a, **kw):
            res = o_rm(state, entity, target, *a, **kw)
            try:
                u = res.get(entity.id) if isinstance(res, dict) else None
                nav = u.navigation if u is not None else None
                fr = getattr(nav, "failure_reason", None) if nav is not None else None
                clr = bool(getattr(nav, "failure_reason_clear", False)) if nav is not None else False
                if fr is not None:
                    out_ = f"code:{val(fr)}"
                    writers[entity.id].append((MOVEMENT_PREFIX + "resolve_move", str(val(fr))))
                elif clr:
                    out_ = "success"
                else:
                    out_ = "other"
                c[f"step_{out_.split(':')[0]}"] += 1
                tick_last[entity.id] = out_
                if u is not None and getattr(u, "new_position", None) is not None:
                    moves[entity.id].add("step")
                # EVERY update in res (not only the mover's): record codes of any other body's entry
                for eid, ou in res.items() if isinstance(res, dict) else ():
                    if eid != entity.id:
                        onav = getattr(ou, "navigation", None)
                        ofr = getattr(onav, "failure_reason", None) if onav is not None else None
                        if ofr is not None:
                            writers[eid].append((MOVEMENT_PREFIX + "resolve_move.other", str(val(ofr))))
            except Exception:
                note("resolve_move")
            return res

        MovementSystem.resolve_move = staticmethod(rm_spy)
        coverage["wrapped"].append("MovementSystem.resolve_move")

        o_yield = MovementSystem.__dict__["_yield_update"].__func__ if "_yield_update" in vars(MovementSystem) else None
        if o_yield is None:
            coverage["missing"].append("MovementSystem._yield_update")
            required.append("MovementSystem._yield_update")
        else:
            def yield_spy(*a, **kw):
                res = o_yield(*a, **kw)
                try:
                    if res is not None and getattr(res, "new_position", None) is not None:
                        moves[res.entity_id].add("yield")
                        c["yields_proposed"] += 1
                    record(MOVEMENT_PREFIX + "yield", res)
                except Exception:
                    note("yield")
                return res

            MovementSystem._yield_update = staticmethod(yield_spy)
            coverage["wrapped"].append("MovementSystem._yield_update")

        from src.engine.pipeline_phases.movement import MovementPhase

        if "_build_position_swap_entity_update" not in vars(MovementPhase):
            coverage["missing"].append("MovementPhase._build_position_swap_entity_update")
            required.append("MovementPhase._build_position_swap_entity_update")
        else:
            o_swap = MovementPhase.__dict__["_build_position_swap_entity_update"].__func__

            def swap_spy(*a, **kw):
                res = o_swap(*a, **kw)
                try:
                    if res is not None and getattr(res, "new_position", None) is not None:
                        moves[res.entity_id].add("swap")
                        c["swaps_proposed"] += 1
                    record(MOVEMENT_PREFIX + "swap", res)
                except Exception:
                    note("swap")
                return res

            MovementPhase._build_position_swap_entity_update = staticmethod(swap_spy)
            coverage["wrapped"].append("MovementPhase._build_position_swap_entity_update")

        # --- non-movement writers
        import src.engine.combat as combat_mod
        import src.engine.domain.action_router as router_mod
        import src.engine.domain.core_actions as core_mod
        import src.engine.lodging as lodging_mod
        from src.engine.domain.action_router import ActionRouter
        from src.engine.domain.aoe_actions import AoeActions
        from src.engine.domain.combat_actions import CombatActions
        from src.engine.domain.core_actions import CoreActions
        from src.engine.domain.skill_actions import SkillActions

        for cls, cat in ((CoreActions, "core_actions"), (ActionRouter, "action_router"), (CombatActions, "combat"), (SkillActions, "skill"), (AoeActions, "aoe")):
            wrap_class_statics(cls, cat)
        for mod, cat in ((core_mod, "core_actions"), (router_mod, "action_router"), (lodging_mod, "lodging"), (combat_mod, "combat")):
            wrap_module_funcs(mod, cat)

        # --- refiner phases (diff of the output update against the input update)
        from src.engine.pipeline_phases.actor_validity import ActorValidityPhase
        from src.engine.pipeline_phases.occupancy import OccupancyPhase
        from src.engine.pipeline_phases.trust import TrustBoundaryPhase

        for cls, attr, cat, idx in ((OccupancyPhase, "resolve", "occupancy", 1), (ActorValidityPhase, "resolve", "actor_validity", 1), (TrustBoundaryPhase, "strip", "trust", 0)):
            raw = vars(cls).get(attr)
            if not isinstance(raw, staticmethod):
                coverage["missing"].append(f"{cls.__name__}.{attr}")
                required.append(f"{cls.__name__}.{attr}")
                continue
            setattr(cls, attr, staticmethod(make_diff_wrapper(cat, raw.__func__, idx)))
            coverage["wrapped"].append(f"{cls.__name__}.{attr}")

        # --- L1: the law at the navigation patch apply
        from src.engine.patches import NavigationPatch

        o_apply = NavigationPatch.apply

        def apply_spy(self, entity, changes):
            pre = None
            expected = None
            have = False
            try:
                pre_nav = changes.get("navigation", entity.navigation)
                pre = pre_nav.last_failure_reason
                un = self.navigation
                if un is None:
                    expected = pre
                elif un.failure_reason is not None:
                    expected = un.failure_reason
                elif un.failure_reason_clear:
                    expected = None
                else:
                    expected = pre
                have = True
            except Exception:
                note("apply_pre")
            o_apply(self, entity, changes)
            if have:
                try:
                    post = changes.get("navigation", entity.navigation).last_failure_reason
                    c["l1_calls"] += 1
                    e_v = None if expected is None else str(val(expected))
                    p_v = None if post is None else str(val(post))
                    if p_v != e_v:
                        c["l1_violations"] += 1
                        if len(l1) < CAP:
                            l1.append({"tick": cur["tick"], "eid": getattr(self, "entity_id", None), "pre": None if pre is None else str(val(pre)), "expected": e_v, "post": p_v})
                except Exception:
                    note("apply_post")

        NavigationPatch.apply = apply_spy
        coverage["wrapped"].append("NavigationPatch.apply")

        if required:
            print("MISSING_HOOK_TARGETS " + ", ".join(required))
            return 4

        # --- R2 hook (infer_blockers), v1 shape; the subject's latest applied outcome is "move"
        o_ib = StrategicIntelligenceSystem.__dict__["infer_blockers"].__func__

        def ib_spy(entity, last_task, last_payload, navigation_failure=None, current_project=None):
            res = o_ib(entity, last_task, last_payload, navigation_failure, current_project)
            try:
                nf = val(navigation_failure) if navigation_failure is not None else None
                for b in getattr(res, "blockers_add_or_update", ()) or ():
                    if b.kind == "access" and nf in ACCESS_CODES and b.id.startswith("blocker_access_"):
                        filed[f"access_from_{nf}"] += 1
                        if applied_latest.get(entity.id) == "move":
                            c["r2_violations"] += 1
                            if len(r2) < CAP:
                                r2.append({"tick": cur["tick"], "eid": entity.id, "blocker": b.id, "navigation_failure": nf})
                    elif b.id == "blocker_congestion":
                        filed["congestion"] += 1
                    elif b.kind == "access":
                        filed["access_other"] += 1
            except Exception:
                note("infer_blockers")
            return res

        StrategicIntelligenceSystem.infer_blockers = staticmethod(ib_spy)

    try:
        for eid0, e0 in kernel.state.entities.items():
            prev_pos[eid0] = tuple(e0.navigation.position)
            prev_lod[eid0] = getattr(e0.navigation, "lodged_in", None)
        for _ in range(ticks):
            cur["tick"] = kernel.state.tick
            tick_last.clear()
            writers.clear()
            moves.clear()
            kernel.tick_once()
            if plain:
                continue
            t = cur["tick"]
            for eid, e in kernel.state.entities.items():
                try:
                    nav = e.navigation
                    now = nav.last_failure_reason
                    nowv = None if now is None else str(val(now))
                    pv = prev_reason.get(eid)
                    if eid in prev_reason:
                        if pv is None and nowv is not None:
                            c["reasons_set"] += 1
                        elif pv is not None and nowv is None:
                            c["reasons_cleared"] += 1
                    prev_reason[eid] = nowv
                    pos = tuple(nav.position)
                    lod = getattr(nav, "lodged_in", None)
                    ppos = prev_pos.get(eid)
                    moved = False
                    if ppos is not None and pos != ppos:
                        if lod is None and prev_lod.get(eid) is None:
                            moved = True
                        else:
                            c["position_changes_lodging_excluded"] += 1
                    prev_pos[eid] = pos
                    prev_lod[eid] = lod
                    kinds = moves.get(eid, set())
                    ws = writers.get(eid, [])
                    if moved:
                        c["moves"] += 1
                        for k in kinds:
                            c[f"move_{k}"] += 1
                        if not kinds:
                            c["moves_without_kind"] += 1
                            if len(unkinded) < CAP:
                                unkinded.append({"tick": t, "eid": eid})
                        if nowv is not None:
                            non_mv = [w for w in ws if w[1] == nowv and not w[0].startswith(MOVEMENT_PREFIX)]
                            any_w = [w for w in ws if w[1] == nowv]
                            if non_mv:
                                after_move_by_writer[non_mv[0][0]] += 1
                                after_move_by_code[nowv] += 1
                            else:
                                c["m1_violations"] += 1
                                if len(m1) < CAP:
                                    m1.append({"tick": t, "eid": eid, "last_failure_reason": nowv, "kinds": sorted(kinds), "writers_of_that_code": [w[0] for w in any_w]})
                            if not any_w:
                                c["m2_violations"] += 1
                                if len(m2) < CAP:
                                    m2.append({"tick": t, "eid": eid, "last_failure_reason": nowv, "kinds": sorted(kinds), "all_writers_this_tick": [list(w) for w in ws]})
                        applied_latest[eid] = "move"
                    elif eid in tick_last:
                        applied_latest[eid] = "stay"
                    # v1 R1 / R3 (REPORTED, comparable with the first own-job; resolve_move-only)
                    out_ = tick_last.get(eid)
                    if out_ == "success":
                        c["success_steps_scanned"] += 1
                        if nowv is not None:
                            c["r1_violations"] += 1
                            if len(r1) < CAP:
                                r1.append({"tick": t, "eid": eid, "last_failure_reason": nowv, "writers_of_that_code": [w[0] for w in ws if w[1] == nowv]})
                    elif out_ is not None and out_.startswith("code:"):
                        c["failed_steps_scanned"] += 1
                        if nowv != out_[5:]:
                            c["r3_violations"] += 1
                            if len(r3) < CAP:
                                r3.append({"tick": t, "eid": eid, "step_code": out_[5:], "last_failure_reason": nowv, "writers_of_that_code": [w[0] for w in ws if w[1] == nowv]})
                    ids = set(e.strategic.blockers.keys())
                    before = blocker_ids[eid]
                    for bid in before - ids:
                        removed_tick[(eid, bid)] = t
                        c["blockers_removed"] += 1
                    for bid in ids - before:
                        rt = removed_tick.pop((eid, bid), None)
                        c["blockers_seen_new"] += 1
                        if rt is not None and t - rt <= 200:
                            c["blockers_refiled_within_200"] += 1
                            if len(refiled) < CAP:
                                refiled.append({"eid": eid, "blocker": bid, "removed_tick": rt, "refiled_tick": t})
                    blocker_ids[eid] = ids
                except Exception:
                    note("scan")
    finally:
        state = kernel.state
        kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    doc = {
        "world": world, "seed": seed, "ticks": ticks, "hashseed": os.environ.get("PYTHONHASHSEED"), "plain": plain, "final_hash": final_hash,
        "match": (None if (plain or want is None) else final_hash == want), "exceptions": dict(exc), "exception_rows": {k: v for k, v in exc_rows.items()},
        "logging_errors": log_count[0], "logging_error_rows": log_rows, "run_dir": str(Path("data").resolve() / "runs" / run_id), "pinned": "PINNED", "rows_cap": CAP,
        "bars": {"L1_post_ne_expected": c["l1_violations"], "M1_moved_with_unattributed_code": c["m1_violations"], "M2_moved_with_code_no_writer": c["m2_violations"],
                 "R2_blocker_filed_after_move": c["r2_violations"], "reasons_set": c["reasons_set"], "reasons_cleared": c["reasons_cleared"],
                 "moves": {"all": c["moves"], "step": c["move_step"], "swap": c["move_swap"], "yield": c["move_yield"]},
                 "l1_rows": l1, "m1_rows": m1, "m2_rows": m2, "r2_rows": r2},
        "reported": {"counts": dict(c), "action_codes_after_a_move_by_primary_writer": dict(after_move_by_writer), "action_codes_after_a_move_by_code": dict(after_move_by_code),
                     "moves_without_kind_rows": unkinded, "v1_r1_rows": r1, "v1_r3_rows": r3, "blockers_filed_by_infer_blockers": dict(filed), "refiled_within_200_rows": refiled,
                     "hook_coverage": coverage},
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"final_hash": final_hash, "match": doc["match"], "exceptions": dict(exc), "logging_errors": log_count[0], "l1": c["l1_violations"], "m1": c["m1_violations"],
                      "m2": c["m2_violations"], "r2": c["r2_violations"]}))
    if want is not None and final_hash != want:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
