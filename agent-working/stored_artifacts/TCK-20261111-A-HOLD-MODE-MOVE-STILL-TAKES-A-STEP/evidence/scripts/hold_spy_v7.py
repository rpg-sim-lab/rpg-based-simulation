"""HOLD-mode STAGE-2 spy v7 = approved v6 (hold_spy_v6.py 8891052e, file untouched) + three pure-read fields on EVERY per-episode trace row (the post-tick state of the held subject):
task_work_kind (the task's work kind), task_action (the payload's "action" or None; task_reason: the payload's "reason" or None), and action_live = (task work kind is ENTITY_ACT AND the payload is truthy AND neither its action
nor its reason is a typed-wait label: WATCH_HOSTILE / AVOID_NO_ROUTE / HOLD_CHOKEPOINT), i.e. the subject holds a live self-decided action task (ATTACK, SKILL, EAT, REST ...) under a stored HOLD mode. Nothing else changes; every v3-v6 key is unchanged.
v6 text follows.
HOLD-mode WAKE-TRACE spy v6 = approved v5 (hold_spy_v5.py f5a97861, file untouched) + ONE read-only wrap of DeterministicScheduler._critical_item (new top-level key "v6"; every v3/v4/v5 key unchanged).
For the subject entity (env V6_SUBJECT, default 32) on each tick in [V6_LO, V6_HI] (defaults 500 and 590) the wrap calls the original with its own arguments, returns ITS result unchanged, and records, from pure reads only:
tick; whether the item was scheduled and its work_kind; lifecycle.active; task work_kind / payload / payload_truthy / is_idle_act; movement_mode; readiness; navigation.step_ready_tick; hp, position, hunger, sleep_debt;
the decision-32 gates of _is_woken: the wake-tick gate ((tick + id) % ADJACENCY_WAKE_COOLDOWN == 0), action_holder (ENTITY_ACT with a truthy payload: "an action holder is not interrupted"), MovementCandidateSelector.unengaged_adjacent_hostile
(called with the scheduler's own wake_index), the engaged hostiles (LegalityServiceV2.get_engaged_hostiles) and the final _is_woken; _is_need_woken; is_brain (the scheduler's own formula); the scheduler's _throttled result; the readiness gate
(not is_brain and readiness < 100). Each row is then joined with the v5 per-tick decision records (tactical / strategic passes that ran for the subject that tick; [] = none). All pure helpers (a changed end hash would show a side effect).
Limits: the join only has decision records for ticks the subject was held (v5's rule); the wrap re-derives the gates with the scheduler's own formulas.
v5 text follows.
HOLD-mode STAGE-2 spy v5 = approved v4 (hold_spy_v4.py 6b3edf17, file untouched) + purely additive read-only DECISION WRAPS (new top-level key "v5"; every v3/v4 output key unchanged).
v5 additions: (a) TacticalDecisionSystem.evaluate_entity_intent and the strategic evaluate_strategic_intent are wrapped (the V3 trace spy's way: call the original with its own arguments, return its result
unchanged) and, for an entity that is in HOLD mode (or has an open HOLD episode) when called, append a decision record to a per-(tick, entity) store: tactical kind = wait (the result's
payload label is a typed wait: WATCH_HOSTILE / AVOID_NO_ROUTE / HOLD_CHOKEPOINT) | walk (the result sets a navigation target) | other | none (result None); with label, movement_mode_set, target_set, work_kind.
Strategic: walk (the update sets a navigation target) | other. (b) Every trace row (one per held tick, tick = the tick run) carries "tact" and "strat": the lists of that tick's decision records ([] = NO decision
that tick). (c) The narrowed stop (i) is computed per 50+ episode in VERDICT["V5"]: fresh_wait_ticks (held ticks with >=1 tactical wait record), no_fresh_wait ticks, beside-hostile ticks without a fresh wait and the LONGEST consecutive run of them,
walk_refused_ticks (a walk decision on a held tick that is not the episode's last row, i.e. the hold continued), no_decision_ticks (no tactical and no strategic record), the longest consecutive run of fresh waits and
the number of waits; STOP_i_candidate = no hit row in the hold AND a run of >= 50 consecutive held ticks beside a hostile with NO fresh wait decision (a stated reading; the raw per-tick rows are kept so any other reading can be
recomputed). (d) Compact stats for ALL episodes (not only 50+): class, label, length, hit rows, ticks beside a hostile, in doc["v5"]["episodes_all"]; the doc also carries the 1-tick collapse-lag list (collapse episodes with
outlived_task_by == 1), AVOID_NO_ROUTE episodes hit while holding, and the re-chosen-wait summary. v5_exceptions is a separate counter: a run counts only with exceptions {}, v4_exceptions {} AND v5_exceptions {}.
Limits (as v4): adjacency/hp read after each tick; a decision recorded for a held entity includes ticks where the scheduler did not select it only if the function ran; the decision store is keyed by the tick run.
v4 text follows.
HOLD-mode COMPLETION-CHECK spy v4 = approved v3 (hold_spy.py ffaa2295) + purely additive read-only recording (new top-level key "v4"; every v3 output key is unchanged).
v4 additions (all read-only; every wrapper still returns ITS original object): (a) resolve_multi_attack records EVERY call's defender, attackers, damage_taken and the OA flag
(whole-run counts labelled "multi/OA path only"; it misses ordinary adjacent swings, so the VERDICT does not use it). (b) Per tick, for each OPEN HOLD episode: post-tick position hp, the orthogonally adjacent hostiles
(LegalityServiceV2.get_engaged_hostiles, the same call v3 already makes), the tick's decision events (the v3 EntityUpdate heuristic: decisions / first target_set / movement_target
branch) and whether a walk (a target_set) was issued. At close, an episode of length >= 50 gets a verdict: ticks beside a hostile, hit by an adjacent hostile during the hold
(yes/no; a HIT TICK is a trace row whose combat.last_hit_tick == t, the attacker is combat.last_attacker_id, the damage is the hp drop on that row, never summed call damage), walk decision issued (yes/no), hp start/min/end; its compact per-tick trace is kept. (c) At the last tick, every entity in HOLD mode: episode class,
entry label, task, is_asleep, sleep_debt vs SLEEP_DEBT.wake_line, the tick its sleep ended (the episode's task_end_tick) and the walk decisions since. (d) Deaths: per death the
tick, kind, role, typed DeathRecord cause, last attacker, and whether the subject was in HOLD mode / an open episode at death; deaths by cause and by kind/role, alive per kind/role at
the end. Limits: adjacency and hp are read AFTER each tick_once; the decision-event heuristic is the v3 one (approximate); a hit in the tick an episode opens is attributed to the
tick window start_tick..end_tick inclusive. Usage and exit codes are v3's.
TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP. v3 text follows.
HOLD-mode step spy v3 (rpg-implementer, DRAFT for rpg-designer approval; NOT run before the smoke). v3 vs the approved v2: an EMPTIED task payload counts as ENDED
(a kill ends its task in the kill tick, so its HOLD has no live task; v2 matched the idle act's label None against the entry label None and called those steps live).
TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP. Read-only: every wrapper calls the original and returns ITS object unchanged; the tick loop only calls
kernel.tick_once(); the per-tick scan only reads kernel.state. Same build as the recruit spy (tools.test_architecture.rpg_gate_run.build_kernel, audit_mode /
no_frame_pacing checked, pinned governor, local sequential executor). A hook that raises inside the spy's own bookkeeping is counted in `exceptions` and swallowed;
an exception from an ORIGINAL call propagates unchanged. Run with cwd = the tree under test (PYTHONPATH = that tree); outputs and the kernel's data/runs go under /mnt/data2.
Usage: python hold_spy.py <world> <seed> <ticks> <out.json> [PLAIN | <expected final_hash>]. PLAIN = no wrapper, no scan (the plain twin; stores its hash).
A hash given = exit 3 on mismatch (the JSON is still written).
Hooks (class attributes, patched; each wrapper records, then returns the original result):
  MovementCandidateSelector.movement_target: the branch of the last call per entity (candidate_selector.py:166-175): decision (nav.target_set with an ENTITY_MOVE task
      update), target_set_no_move_task (nav.target_set otherwise), stored_or_live.
  MovementSystem.resolve_move: one row per call whose EFFECTIVE mode is HOLD (the `mode` argument): tick, entity, kind, branch, the STORED target and the site that last wrote
      it, target, from/to, stepped, legality-engaged hostiles before the call, hp, readiness, move_cost, the CURRENT task's work_kind and reason-or-action,
      hold_task_status = hold_task_live | hold_outlived_task | hold_entry_tick (the HOLD is written this very tick, so the entering task is live by definition) |
      hold_task_unknown (no writer seen: HOLD from before the spy could see it). live = the current task has the same work_kind and reason-or-action as the task of the
      update that entered the episode, the episode class, and the opportunity attacks it provoked. For WANDER calls with NO stored target: counts of calls and steps by branch.
  CombatResolutionSystem.resolve_multi_attack: while a HOLD resolve_move runs, a call with is_opportunity_attack=True appends {attackers, damage_taken, hp_delta, outcome_kind}.
  DeterministicScheduler._is_woken / _is_need_woken: whether an entity was woken (adjacency wake / need wake) this tick.
  EntityUpdate.__init__: the FIRST write of each movement_mode per (tick, entity); the FIRST target_set write per (tick, entity) (kept as the entity's last target writer);
      the FIRST task-bearing write per (tick, entity) from outside actions.py (a DECISION event, with its target_set). Each with the construction site (first frame outside
      dataclasses.py and core/updates.py).
  Per-tick scan of kernel.state after each tick_once (reads only): HOLD EPISODES per entity from the tick the stored movement_mode becomes HOLD until it becomes another mode,
      the entity dies, or the run ends. CLASS of an episode: typed_wait (entry label WATCH_HOSTILE / AVOID_NO_ROUTE / HOLD_CHOKEPOINT), kill (writer actions._hold_in_place),
      collapse (writer sleep_debt.collapse_update), other. Per episode: writer site, entry task, length, how it ended (mode, writer site, that tick's movement_target branch, or
      died / still HOLD), the first tick the entering task was no longer the current task and how many ticks the episode outlived it, HOLD steps with OA damage and deaths
      within 10 ticks, the stored target at entry, and (typed waits) the NEXT DECISION after entry: its tick, site, target_set, whether it re-issued the same target, and what
      woke the subject at that tick (adjacency_wake / need_wake / brain_or_idle_act), plus the gap steps (HOLD steps from entry to that decision) with branch, stored-target
      presence, target writer site, OA events, OA damage, deaths within 10 ticks.
Tick labels: tick = kernel.state.tick before the tick_once call (the tick being run). The decision-event heuristic (a task-bearing EntityUpdate from a site outside actions.py)
is approximate; its limits are visible in the rows (sites are recorded).
Output JSON: world, seed, ticks, final_hash, match, exceptions, counts (uncapped, also split by episode class and by entry label), length distribution per class, and capped
rows (400 each). HEADLINE: hold_steps_outlived_task (total, by class, by entry label) with OA events, damage, deaths within 10 ticks, distinct tick/subject counts."""
from __future__ import annotations

import json
import os
import shutil
import sys
from collections import Counter, defaultdict

CAP = 400
BUCKETS = ((1, 1), (2, 2), (3, 5), (6, 10), (11, 20), (21, 49), (50, 99), (100, 10 ** 9))
TYPED = {"WATCH_HOSTILE", "AVOID_NO_ROUTE", "HOLD_CHOKEPOINT"}


def bucket(n):
    for lo, hi in BUCKETS:
        if lo <= n <= hi:
            return f"{lo}-{hi if hi < 10 ** 9 else 'inf'}"
    return "0"


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    mode_arg = argv[4] if len(argv) > 4 else None
    plain = mode_arg == "PLAIN"
    want = None if plain else mode_arg
    from pathlib import Path

    from src.core.movement_modes import MovementMode
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    run_id = f"rpghold_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD")
        return 2
    HOLD = MovementMode.HOLD
    WANDER = MovementMode.WANDER
    cur = {"tick": 0}
    exc = Counter()
    branch_of = {}          # eid -> (tick, branch) of the last movement_target call
    first_mode = {}         # (tick, eid, mode value) -> {site, task_kind, label}
    first_target = {}       # (tick, eid) -> {site, target}
    decisions = {}          # (tick, eid) -> {site, task_kind, label, target_set}
    last_target_writer = {}  # eid -> {tick, site}
    woke = {}               # (tick, eid) -> "adjacency_wake" | "need_wake"
    hold_rows = []
    c = Counter()
    by = defaultdict(Counter)      # by["class:<cls>"|"label:<label>"] -> Counter
    sets = {"ticks": set(), "subjects": set(), "o_ticks": set(), "o_subjects": set()}
    wander_notarget = Counter()
    pending_death = []      # [tick, eid, row, outlived, cls, label]
    cur_row = {"row": None}
    episodes_open, episodes_done = {}, []
    prev_mode = {}
    v4_hits = defaultdict(list)     # defender id -> [(tick, [attacker ids], damage_taken, is_oa)] (damaging only)
    v4_all = Counter()              # whole-run: oa_calls, oa_damage, oa_damaging, hit_calls, hit_damage
    v4_deaths = []                  # per death
    v4_eps = []                     # verdicts for episodes of length >= 50
    v4_alive_prev = {}
    v4_exc = Counter()
    v5_exc = Counter()
    v5_dec = {}      # (tick, eid) -> {"tact": [...], "strat": [...]}
    v5_all = []      # compact stats for every closed episode
    v6_rows = []     # wake-gate rows for the v6 subject

    def val(x):
        return getattr(x, "value", str(x))

    def label_of(payload):
        if not payload:
            return None
        return payload.get("reason") or payload.get("action")

    def site():
        f = sys._getframe(2)
        while f is not None and (f.f_code.co_filename.endswith("dataclasses.py") or f.f_code.co_filename.endswith(os.path.join("core", "updates.py"))):
            f = f.f_back
        if f is None:
            return "unknown"
        return f"{os.path.basename(f.f_code.co_filename)}:{f.f_lineno}:{f.f_code.co_name}"

    def classify(w):
        if w is None:
            return "other", None
        label = w.get("label")
        s = w.get("site", "")
        if label in TYPED:
            return "typed_wait", label
        if "_hold_in_place" in s:
            return "kill", label or "AFTER_KILL"
        if "collapse_update" in s:
            return "collapse", label or "COLLAPSE"
        return "other", label

    if not plain:
        from src.core.updates import EntityUpdate
        from src.engine.candidate_selector import MovementCandidateSelector
        from src.engine.combat import CombatResolutionSystem
        from src.engine.legality import LegalityServiceV2
        from src.engine.movement import MovementSystem
        from src.engine.scheduler import DeterministicScheduler

        o_mt = MovementCandidateSelector.__dict__["movement_target"].__func__

        def mt_spy(*a, **kw):
            res = o_mt(*a, **kw)
            try:
                entity = a[0] if a else kw["entity"]
                ent_upd = a[1] if len(a) > 1 else kw.get("ent_upd")
                nav = ent_upd.navigation if ent_upd else None
                if nav is not None and nav.target_set is not None:
                    b = "decision" if (ent_upd.task is not None and ent_upd.task.work_kind_set == "ENTITY_MOVE") else "target_set_no_move_task"
                else:
                    b = "stored_or_live"
                branch_of[entity.id] = (cur["tick"], b)
            except Exception:
                exc["movement_target"] += 1
            return res

        MovementCandidateSelector.movement_target = staticmethod(mt_spy)

        o_w = DeterministicScheduler.__dict__["_is_woken"]
        o_w_fn = o_w.__func__ if isinstance(o_w, staticmethod) else o_w

        def woken_spy(*a, **kw):
            res = o_w_fn(*a, **kw)
            try:
                if res:
                    ent = a[-4] if len(a) >= 4 else kw.get("ent")
                    ent = ent if hasattr(ent, "id") else (a[1] if len(a) > 1 and hasattr(a[1], "id") else ent)
                    woke[(cur["tick"], ent.id)] = "adjacency_wake"
            except Exception:
                exc["is_woken"] += 1
            return res

        DeterministicScheduler._is_woken = staticmethod(woken_spy)

        o_nw = DeterministicScheduler.__dict__["_is_need_woken"]
        o_nw_fn = o_nw.__func__ if isinstance(o_nw, staticmethod) else o_nw

        def need_spy(*a, **kw):
            res = o_nw_fn(*a, **kw)
            try:
                if res:
                    ent = next((x for x in a if hasattr(x, "id") and hasattr(x, "task")), None)
                    if ent is not None:
                        woke.setdefault((cur["tick"], ent.id), "need_wake")
            except Exception:
                exc["is_need_woken"] += 1
            return res

        DeterministicScheduler._is_need_woken = staticmethod(need_spy)

        o_rm = MovementSystem.__dict__["resolve_move"].__func__

        def rm_spy(state, entity, target, *a, **kw):
            try:
                m = kw.get("mode", a[0] if a else WANDER)
                hold = (m == HOLD)
                wander_nt = (m == WANDER and entity.navigation.target is None)
            except Exception:
                exc["resolve_move_mode"] += 1
                hold, wander_nt = False, False
            row = None
            b = None
            try:
                bb = branch_of.get(entity.id)
                b = bb[1] if bb and bb[0] == cur["tick"] else None
            except Exception:
                exc["resolve_move_branch"] += 1
            if hold:
                try:
                    ep = episodes_open.get(entity.id)
                    entry = ep["entry_task"] if ep else None
                    cur_kind = entity.task.work_kind
                    cur_label = label_of(entity.task.payload)
                    ep_cls = ep["cls"] if ep else None
                    ep_lab = ep["entry_label"] if ep else None
                    if ep is None:
                        # no open episode: the HOLD may be written THIS tick (the step runs in the entry tick, before the per-tick scan opens the episode)
                        w0 = first_mode.get((cur["tick"], entity.id, "HOLD"))
                        if w0 is not None:
                            ep_cls, ep_lab = classify(w0)
                            status = "hold_entry_tick"   # the entering task is live in its own tick by definition; never counted as outlived
                        else:
                            status = "hold_task_unknown"  # HOLD held from before the spy could see it (e.g. the run's initial state)
                    elif entry is None:
                        status = "hold_task_unknown"
                    elif not entry["has_payload"] or not entity.task.payload:
                        status = "hold_outlived_task"  # the entering task was already emptied (a kill's: ended in the kill tick) or has been emptied since: ended, never matched as None == None
                    else:
                        status = "hold_task_live" if (cur_kind == entry["task_kind"] and cur_label == entry["label"]) else "hold_outlived_task"
                    tw = last_target_writer.get(entity.id)
                    row = {
                        "tick": cur["tick"], "entity": entity.id, "kind": entity.kind, "branch": b, "episode_class": ep_cls,
                        "entry_label": ep_lab,
                        "stored_target": list(entity.navigation.target) if entity.navigation.target is not None else None,
                        "stored_target_writer": tw["site"] if tw else None, "stored_target_write_tick": tw["tick"] if tw else None,
                        "target": list(target) if target is not None else None, "from": list(entity.navigation.position),
                        "engaged_hostiles": list(LegalityServiceV2.get_engaged_hostiles(entity, state)), "hp_before": entity.combat.hp,
                        "readiness": entity.combat.readiness, "move_cost": entity.combat.move_cost,
                        "current_task_kind": cur_kind, "current_task_label": cur_label, "hold_task_status": status, "oa": [],
                    }
                    cur_row["row"] = row
                except Exception:
                    exc["resolve_move_pre"] += 1
                    row = None
                    cur_row["row"] = None
            try:
                res = o_rm(state, entity, target, *a, **kw)
            finally:
                cur_row["row"] = None
            try:
                eu = res.get(entity.id) if isinstance(res, dict) else res
                new_pos = getattr(eu, "new_position", None) if eu is not None else None
                stepped = new_pos is not None
                if wander_nt:
                    wander_notarget[f"calls|{b}"] += 1
                    if stepped:
                        wander_notarget[f"steps|{b}"] += 1
                if row is not None:
                    row["stepped"] = stepped
                    row["to"] = list(new_pos) if new_pos is not None else None
                    row["died_within_10"] = None
                    cls, lab, status = row["episode_class"], row["entry_label"], row["hold_task_status"]
                    keys = [f"class:{cls}", f"label:{lab}"]
                    c["hold_calls"] += 1
                    c[f"hold_calls_{status}"] += 1
                    c[f"hold_calls_branch_{row['branch']}"] += 1
                    for k in keys:
                        by[k]["hold_calls"] += 1
                        by[k][f"hold_calls_{status}"] += 1
                    sets["ticks"].add(row["tick"])
                    sets["subjects"].add(row["entity"])
                    if stepped:
                        outlived = status == "hold_outlived_task"
                        n_oa = len(row["oa"])
                        dmg = sum((o.get("damage_taken") or 0) for o in row["oa"])
                        c["hold_steps"] += 1
                        c[f"hold_steps_{status}"] += 1
                        c[f"hold_steps_branch_{row['branch']}"] += 1
                        c["hold_steps_with_stored_target" if row["stored_target"] is not None else "hold_steps_without_stored_target"] += 1
                        if row["engaged_hostiles"]:
                            c["hold_steps_with_engaged_hostiles"] += 1
                        if n_oa:
                            c["hold_steps_with_oa"] += 1
                            c["hold_steps_oa_events"] += n_oa
                            c["hold_steps_oa_damage"] += dmg
                        for k in keys:
                            by[k]["hold_steps"] += 1
                            by[k][f"hold_steps_{status}"] += 1
                            by[k][f"hold_steps_branch_{row['branch']}"] += 1
                            by[k]["hold_steps_oa_events"] += n_oa
                            by[k]["hold_steps_oa_damage"] += dmg
                            if outlived:
                                by[k]["HEADLINE_outlived_steps"] += 1
                                by[k]["HEADLINE_outlived_oa_events"] += n_oa
                                by[k]["HEADLINE_outlived_oa_damage"] += dmg
                        if outlived:
                            c["HEADLINE_hold_steps_outlived_task"] += 1
                            c["HEADLINE_outlived_oa_events"] += n_oa
                            c["HEADLINE_outlived_oa_damage"] += dmg
                            sets["o_ticks"].add(row["tick"])
                            sets["o_subjects"].add(row["entity"])
                        pending_death.append([row["tick"], entity.id, row, outlived, cls, lab])
                        ep = episodes_open.get(entity.id)
                        if ep is not None:
                            ep["steps"] += 1
                            ep["oa_damage"] += dmg
                            ep["oa_events"] += n_oa
                            ep["step_rows"].append(row)
                    else:
                        c["hold_calls_no_step"] += 1
                    if len(hold_rows) < CAP:
                        hold_rows.append(row)
            except Exception:
                exc["resolve_move_post"] += 1
            return res

        MovementSystem.resolve_move = staticmethod(rm_spy)

        o_oa = CombatResolutionSystem.__dict__["resolve_multi_attack"].__func__

        def oa_spy(*a, **kw):
            res = o_oa(*a, **kw)
            try:
                dfd = a[1] if len(a) > 1 else kw.get("defender")
                atks = a[0] if a else kw.get("attackers")
                is_oa = bool(kw.get("is_opportunity_attack", a[3] if len(a) > 3 else False))
                dmg_t = getattr(res, "damage_taken", None) or 0
                v4_all["calls"] += 1
                if is_oa:
                    v4_all["oa_calls"] += 1
                if dmg_t > 0:
                    v4_all["damaging_calls"] += 1
                    v4_all["damage"] += dmg_t
                    if is_oa:
                        v4_all["oa_damaging_calls"] += 1
                        v4_all["oa_damage"] += dmg_t
                    v4_hits[getattr(dfd, "id", None)].append((cur["tick"], [getattr(x, "id", x) for x in (atks or [])], dmg_t, is_oa))
            except Exception:
                v4_exc["resolve_multi_attack_v4"] += 1
            try:
                row = cur_row["row"]
                if row is not None and kw.get("is_opportunity_attack"):
                    attackers = a[0] if a else kw.get("attackers")
                    row["oa"].append({
                        "attackers": [getattr(x, "id", x) for x in (attackers or [])],
                        "damage_taken": getattr(res, "damage_taken", None), "hp_delta": getattr(res, "hp_delta", None),
                        "outcome_kind": val(getattr(res, "outcome_kind", None)),
                    })
            except Exception:
                exc["resolve_multi_attack"] += 1
            return res

        CombatResolutionSystem.resolve_multi_attack = staticmethod(oa_spy)

        o_init = EntityUpdate.__init__

        def ent_init(self, *a, **kw):
            o_init(self, *a, **kw)
            try:
                nav = kw.get("navigation")
                task = kw.get("task")
                eid = kw.get("entity_id", a[0] if a else None)
                t = cur["tick"]
                ms = getattr(nav, "movement_mode_set", None) if nav is not None else None
                tg = getattr(nav, "target_set", None) if nav is not None else None
                wk = getattr(task, "work_kind_set", None) if task is not None else None
                if ms is not None or tg is not None or wk is not None:
                    s = site()
                    ps = (getattr(task, "payload_set", None) or {}) if task is not None else {}
                    if ms is not None and (t, eid, val(ms)) not in first_mode:
                        first_mode[(t, eid, val(ms))] = {"site": s, "task_kind": wk, "label": label_of(ps), "has_payload": bool(ps)}
                    if tg is not None and (t, eid) not in first_target:
                        first_target[(t, eid)] = {"site": s, "target": list(tg)}
                        last_target_writer[eid] = {"tick": t, "site": s}
                    if wk is not None and (t, eid) not in decisions and not s.startswith("actions.py"):
                        decisions[(t, eid)] = {"site": s, "task_kind": wk, "label": label_of(ps), "target_set": list(tg) if tg is not None else None}
            except Exception:
                exc["entity_update_init"] += 1

        EntityUpdate.__init__ = ent_init

        # --- v5: tactical and strategic decision wraps (read-only; the original's own result is returned unchanged)
        from src.engine.tactical import TacticalDecisionSystem
        import src.systems.strategic_systems.intelligence as intel_mod

        def v5_held(entity):
            return entity.navigation.movement_mode == HOLD or entity.id in episodes_open

        o_td = TacticalDecisionSystem.evaluate_entity_intent

        def td_spy(st, entity, *a, **kw):
            res = o_td(st, entity, *a, **kw)
            try:
                if v5_held(entity):
                    tk = getattr(res, "task", None)
                    pl = (getattr(tk, "payload_set", None) or {}) if tk is not None else {}
                    nav = getattr(res, "navigation", None)
                    tset = getattr(nav, "target_set", None) if nav is not None else None
                    mset = getattr(nav, "movement_mode_set", None) if nav is not None else None
                    lab = label_of(pl)
                    kind = "none" if res is None else ("walk" if tset is not None else ("wait" if lab in TYPED else "other"))
                    v5_dec.setdefault((cur["tick"], entity.id), {"tact": [], "strat": []})["tact"].append({
                        "kind": kind, "label": lab, "mode_set": val(mset) if mset is not None else None, "target_set": list(tset) if tset is not None else None,
                        "work_kind": (str(getattr(tk, "work_kind_set", None)) if tk is not None else None)})
            except Exception:
                v5_exc["tactical_wrap"] += 1
            return res

        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(td_spy)

        sis_cls = [c_ for c_ in vars(intel_mod).values() if isinstance(c_, type) and "evaluate_strategic_intent" in c_.__dict__][0]
        so_fn = sis_cls.__dict__["evaluate_strategic_intent"].__func__

        def ss_spy(state_, entity, *a, **kw):
            res = so_fn(state_, entity, *a, **kw)
            try:
                if v5_held(entity):
                    nav = getattr(res, "navigation", None)
                    tset = getattr(nav, "target_set", None) if nav is not None else None
                    mset = getattr(nav, "movement_mode_set", None) if nav is not None else None
                    v5_dec.setdefault((cur["tick"], entity.id), {"tact": [], "strat": []})["strat"].append({
                        "kind": "walk" if tset is not None else "other", "mode_set": val(mset) if mset is not None else None, "target_set": list(tset) if tset is not None else None})
            except Exception:
                v5_exc["strategic_wrap"] += 1
            return res

        sis_cls.evaluate_strategic_intent = staticmethod(ss_spy)

        # --- v6: wake-gate trace for one subject in a tick window (read-only)
        from src.engine.scheduler import ADJACENCY_WAKE_COOLDOWN
        v6_subj = int(os.environ.get("V6_SUBJECT", "32"))
        v6_lo = int(os.environ.get("V6_LO", "500"))
        v6_hi = int(os.environ.get("V6_HI", "590"))
        o_ci = DeterministicScheduler.__dict__["_critical_item"]

        def ci_spy(self, ent, state_, policy, focus_points, wake_index):
            res = o_ci(self, ent, state_, policy, focus_points, wake_index)
            try:
                if ent.id == v6_subj and v6_lo <= state_.tick <= v6_hi:
                    wk = ent.task.work_kind
                    if wk not in ("ENTITY_ACT", "ENTITY_MOVE"):
                        wk = "ENTITY_BRAIN"
                    payload = dict(ent.task.payload or {})
                    is_idle_act = (wk == "ENTITY_ACT" and not ent.task.payload)
                    woken_ = DeterministicScheduler._is_woken(ent, state_, wk, wake_index)
                    need_ = DeterministicScheduler._is_need_woken(ent, state_, wk)
                    woken = woken_ or need_
                    is_brain = woken or wk == "ENTITY_BRAIN" or is_idle_act
                    v6_rows.append({
                        "tick": state_.tick, "scheduled": res is not None, "item_work_kind": (res.work_kind if res is not None else None), "active": ent.lifecycle.active,
                        "task_work_kind": ent.task.work_kind, "task_payload": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in payload.items()},
                        "payload_truthy": bool(ent.task.payload), "is_idle_act": is_idle_act, "movement_mode": val(ent.navigation.movement_mode),
                        "readiness": ent.combat.readiness, "step_ready_tick": ent.navigation.step_ready_tick, "hp": ent.combat.hp, "pos": list(ent.navigation.position),
                        "hunger": ent.biological.hunger, "sleep_debt": ent.biological.sleep_debt,
                        "wake_tick_gate": (state_.tick + ent.id) % ADJACENCY_WAKE_COOLDOWN == 0, "action_holder": (wk == "ENTITY_ACT" and bool(ent.task.payload)),
                        "unengaged_adjacent_hostile": bool(MovementCandidateSelector.unengaged_adjacent_hostile(ent, state_.entities, wake_index)),
                        "engaged_hostiles": list(LegalityServiceV2.get_engaged_hostiles(ent, state_)),
                        "is_woken": bool(woken_), "is_need_woken": bool(need_), "is_brain": bool(is_brain),
                        "throttled": bool(self._throttled(ent, state_, policy, focus_points, is_brain)),
                        "readiness_gate_blocks": bool((not is_brain) and ent.combat.readiness < 100.0),
                    })
            except Exception:
                v5_exc["v6_wrap"] += 1
            return res

        DeterministicScheduler._critical_item = ci_spy

    def close_episode(ep, end_tick, how, end_mode=None, end_site=None, end_branch=None):
        ep["end_tick"] = end_tick
        ep["length"] = end_tick - ep["start_tick"]
        ep["ended"] = how
        ep["end_mode"] = end_mode
        ep["end_site"] = end_site
        ep["end_branch"] = end_branch
        if ep["task_end_tick"] is not None:
            ep["outlived_task_by"] = max(0, end_tick - ep["task_end_tick"])
        try:
            tr = ep.pop("trace", None) or []
            try:
                _pl, _hits, _beside = None, 0, 0
                for _i, _r in enumerate(tr):
                    _beside += 1 if _r["adj"] else 0
                    _h = (_r["last_hit_tick"] is not None and _r["last_hit_tick"] >= ep["start_tick"]) if _i == 0 else (_r["last_hit_tick"] is not None and _r["last_hit_tick"] != _pl)
                    _hits += 1 if _h else 0
                    _pl = _r["last_hit_tick"]
                v5_all.append({"entity": ep["entity"], "kind": ep["kind"], "cls": ep["cls"], "entry_label": ep["entry_label"], "start_tick": ep["start_tick"], "end_tick": end_tick,
                               "length": ep["length"], "ended": how, "hit_rows": _hits, "ticks_beside_hostile": _beside, "outlived_task_by": ep.get("outlived_task_by"), "task_end_tick": ep["task_end_tick"]})
            except Exception:
                v5_exc["all_episode_stats"] += 1
            if ep["length"] >= 50:
                s0, s1 = ep["start_tick"], end_tick
                hits = [h for h in v4_hits.get(ep["entity"], []) if s0 <= h[0] <= s1]   # multi/OA path ONLY (resolve_multi_attack); not used for the verdict
                adj_union = set()
                for r in tr:
                    adj_union.update(r["adj"])
                # HIT ROWS from typed state: a trace row is a hit row when combat.last_hit_tick is not None and differs from the previous row's (first row: >= start_tick); damage = the hp drop on that row
                # (never summed call damage: resolve_attack runs twice per tick). hit_by_adjacent = last_attacker_id in this tick's or the previous tick's adjacent set.
                hit_ticks, prev_hp, prev_adj, off, prev_lht, first = [], None, set(), Counter(), None, True
                for r in tr:
                    if r["last_hit_tick"] is not None:
                        off[r["last_hit_tick"] - r["t"]] += 1
                    # a HIT ROW (no tick-convention assumed): last_hit_tick is not None and differs from the previous trace row's; on the first row: last_hit_tick >= start_tick
                    is_hit = (r["last_hit_tick"] is not None and r["last_hit_tick"] >= s0) if first else (r["last_hit_tick"] is not None and r["last_hit_tick"] != prev_lht)
                    first = False
                    prev_lht = r["last_hit_tick"]
                    if is_hit:
                        hit_ticks.append({"t": r["t"], "attacker": r["last_attacker_id"], "hp": r["hp"], "hp_drop": (max(0, prev_hp - r["hp"]) if prev_hp is not None else None),
                                          "attacker_adjacent_now_or_prev": (r["last_attacker_id"] in set(r["adj"]) or r["last_attacker_id"] in prev_adj)})
                    prev_hp, prev_adj = r["hp"], set(r["adj"])
                walks = [r["t"] for r in tr if (r["decision"] and r["decision"]["target_set"] is not None) or (r["target_write"] is not None and not r["target_write"]["site"].startswith("actions.py")) or r["branch"] in ("decision", "target_set_no_move_task")]
                hp = [r["hp"] for r in tr]
                v5 = {}
                try:
                    nrow = len(tr)
                    wait_t, nowait_beside, nodec, refused, walk_t = [], [], [], [], []
                    run_nw = best_nw = run_w = best_w = 0
                    for i, r in enumerate(tr):
                        kinds = [x["kind"] for x in r.get("tact", [])]
                        has_wait = "wait" in kinds
                        has_walk = ("walk" in kinds) or any(x["kind"] == "walk" for x in r.get("strat", []))
                        if has_wait:
                            wait_t.append(r["t"])
                        if has_walk:
                            walk_t.append(r["t"])
                            if i < nrow - 1:
                                refused.append(r["t"])
                        if not r.get("tact") and not r.get("strat"):
                            nodec.append(r["t"])
                        if r["adj"] and not has_wait:
                            nowait_beside.append(r["t"])
                            run_nw += 1
                            best_nw = max(best_nw, run_nw)
                        else:
                            run_nw = 0
                        if has_wait:
                            run_w += 1
                            best_w = max(best_w, run_w)
                        else:
                            run_w = 0
                    any_hit_row = any_hit_v5 = bool(hit_ticks)
                    v5 = {
                        "held_ticks": nrow, "fresh_wait_ticks": len(wait_t), "fresh_wait_tick_list": wait_t[:60], "longest_run_of_consecutive_fresh_waits": best_w,
                        "beside_hostile_ticks_without_fresh_wait": len(nowait_beside), "longest_run_beside_hostile_without_fresh_wait": best_nw,
                        "no_decision_ticks": len(nodec), "walk_decision_ticks": walk_t[:60], "walk_refused_ticks": refused[:60], "walk_refused_count": len(refused),
                        "any_hit_row": any_hit_v5,
                        "STOP_i_candidate": (not any_hit_v5) and best_nw >= 50,
                        "STOP_i_basis": "no hit row in the hold AND >=50 consecutive held ticks beside a hostile with no fresh wait decision (implementer's stated reading; raw per-tick rows kept in trace)",
                    }
                except Exception:
                    v5_exc["verdict_v5"] += 1
                v4_eps.append({
                    "entity": ep["entity"], "kind": ep["kind"], "cls": ep["cls"], "entry_label": ep["entry_label"], "start_tick": s0, "end_tick": s1, "length": ep["length"],
                    "ended": how, "end_mode": end_mode, "end_site": end_site, "task_end_tick": ep["task_end_tick"], "steps": ep["steps"],
                    "VERDICT": {
                        "ticks_beside_hostile": sum(1 for r in tr if r["adj"]),
                        "hit_by_adjacent_hostile_during_hold": any(h["attacker_adjacent_now_or_prev"] for h in hit_ticks),
                        "any_hit_during_hold": bool(hit_ticks), "hit_ticks": len(hit_ticks), "hp_drop_total_on_hit_ticks": sum((h["hp_drop"] or 0) for h in hit_ticks),
                        "hit_tick_offsets_last_hit_tick_minus_t": dict(off),
                        "multi_or_oa_path_only": {"hits": len(hits), "damage_total_summed_calls": sum(h[2] for h in hits), "oa_hits": sum(1 for h in hits if h[3])},
                        "walk_decision_issued": bool(walks), "walk_decision_ticks": walks[:40], "walk_decision_count": len(walks),
                        "V5": v5, "hp_start": hp[0] if hp else None, "hp_min": min(hp) if hp else None, "hp_end": hp[-1] if hp else None,
                    },
                    "hit_tick_rows": hit_ticks[:400], "multi_or_oa_path_hits": [{"t": h[0], "attackers": h[1], "damage": h[2], "oa": h[3]} for h in hits][:200],
                    "trace_rows": len(tr), "trace": tr,
                })
        except Exception:
            v4_exc["close_verdict"] += 1
        episodes_done.append(ep)

    try:
        for _ in range(ticks):
            cur["tick"] = kernel.state.tick
            kernel.tick_once()
            if plain:
                continue
            t = cur["tick"]
            state = kernel.state
            for eid, e in state.entities.items():
                m = e.navigation.movement_mode
                prev = prev_mode.get(eid)
                ep = episodes_open.get(eid)
                if m == HOLD and prev != HOLD and ep is None:
                    w = first_mode.get((t, eid, "HOLD"))
                    cls, lab = classify(w)
                    episodes_open[eid] = {
                        "entity": eid, "kind": e.kind, "start_tick": t, "writer_site": w["site"] if w else "UNATTRIBUTED", "cls": cls, "entry_label": lab,
                        "entry_task": ({"task_kind": w["task_kind"], "label": w["label"], "has_payload": w.get("has_payload", True)} if w else None),
                        "stored_target_at_entry": list(e.navigation.target) if e.navigation.target is not None else None,
                        "task_end_tick": None, "steps": 0, "oa_damage": 0, "oa_events": 0, "step_rows": [], "deaths_within_10": 0, "next_decision": None,
                    }
                    ep = episodes_open[eid]
                if ep is not None:
                    if ep["task_end_tick"] is None and ep["entry_task"] is not None:
                        if (not ep["entry_task"]["has_payload"] or not e.task.payload
                                or not (e.task.work_kind == ep["entry_task"]["task_kind"] and label_of(e.task.payload) == ep["entry_task"]["label"])):
                            ep["task_end_tick"] = t
                    if ep["next_decision"] is None and t > ep["start_tick"]:
                        d = decisions.get((t, eid))
                        if d is not None:
                            same = None
                            if d["target_set"] is not None and ep["stored_target_at_entry"] is not None:
                                same = (d["target_set"] == ep["stored_target_at_entry"])
                            ep["next_decision"] = {"tick": t, "site": d["site"], "label": d["label"], "target_set": d["target_set"], "same_target_as_at_entry": same,
                                                   "woken_by": woke.get((t, eid), "brain_or_idle_act")}
                    try:
                        adj = list(LegalityServiceV2.get_engaged_hostiles(e, state)) if e.combat.alive else []
                        dd = decisions.get((t, eid))
                        ft = first_target.get((t, eid))
                        bb = branch_of.get(eid)
                        ep.setdefault("trace", []).append({
                            "t": t, "hp": e.combat.hp, "alive": e.combat.alive, "last_hit_tick": e.combat.last_hit_tick, "last_attacker_id": e.combat.last_attacker_id, "pos": list(e.navigation.position), "adj": adj,
                            "decision": ({"site": dd["site"], "label": dd["label"], "target_set": dd["target_set"]} if dd else None),
                            "target_write": ({"site": ft["site"], "target": ft["target"]} if ft else None),
                            "branch": (bb[1] if bb and bb[0] == t else None), "woke": woke.get((t, eid)),
                            "tact": (v5_dec.get((t, eid)) or {}).get("tact", []), "strat": (v5_dec.get((t, eid)) or {}).get("strat", []),
                            "task_work_kind": e.task.work_kind, "task_action": (dict(e.task.payload or {}).get("action")), "task_reason": (dict(e.task.payload or {}).get("reason")),
                            "action_live": bool(e.task.work_kind == "ENTITY_ACT" and e.task.payload and dict(e.task.payload).get("action") not in TYPED and dict(e.task.payload).get("reason") not in TYPED),
                        })
                    except Exception:
                        v4_exc["trace"] += 1
                    if not e.combat.alive:
                        close_episode(episodes_open.pop(eid), t, "died")
                    elif m != HOLD:
                        w = first_mode.get((t, eid, val(m)))
                        b = branch_of.get(eid)
                        close_episode(episodes_open.pop(eid), t, "mode_changed", val(m), w["site"] if w else "UNATTRIBUTED", b[1] if b and b[0] == t else None)
                prev_mode[eid] = m
                try:
                    was = v4_alive_prev.get(eid, True)
                    if was and not e.combat.alive:
                        dr = e.lifecycle.death_record
                        v4_deaths.append({"tick": t, "entity": eid, "kind": e.kind, "role": int(e.identity.role), "death_record": (dr.to_dict() if dr is not None else None),
                                          "mode_at_death": val(m), "in_open_hold_episode": eid in episodes_open or (ep is not None)})
                    v4_alive_prev[eid] = e.combat.alive
                except Exception:
                    v4_exc["death_scan"] += 1
            for entry in list(pending_death):
                pt, peid, prow, poutlived, pcls, plab = entry
                ent = state.entities.get(peid)
                dead = ent is not None and not ent.combat.alive
                if dead and t - pt <= 10:
                    prow["died_within_10"] = True
                    c["hold_steps_died_within_10"] += 1
                    by[f"class:{pcls}"]["hold_steps_died_within_10"] += 1
                    by[f"label:{plab}"]["hold_steps_died_within_10"] += 1
                    if poutlived:
                        c["HEADLINE_outlived_died_within_10"] += 1
                        by[f"class:{pcls}"]["HEADLINE_outlived_died_within_10"] += 1
                        by[f"label:{plab}"]["HEADLINE_outlived_died_within_10"] += 1
                    pending_death.remove(entry)
                elif t - pt > 10:
                    prow["died_within_10"] = False
                    pending_death.remove(entry)
    finally:
        state = kernel.state
        kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    t_end = state.tick
    v4_last = []
    try:
        from src.engine.sleep_debt import SLEEP_DEBT, is_asleep
        for eid, e in state.entities.items():
            if e.combat.alive and e.navigation.movement_mode == HOLD:
                ep = episodes_open.get(eid)
                te = ep["task_end_tick"] if ep else None
                dec_since = sorted(tt for (tt, ee), d in decisions.items() if ee == eid and te is not None and tt >= te and d["target_set"] is not None)
                tgt_since = sorted(tt for (tt, ee), d in first_target.items() if ee == eid and te is not None and tt >= te and not d["site"].startswith("actions.py"))
                v4_last.append({
                    "entity": eid, "kind": e.kind, "role": int(e.identity.role), "episode_class": ep["cls"] if ep else None, "entry_label": ep["entry_label"] if ep else None,
                    "episode_start": ep["start_tick"] if ep else None, "episode_length_so_far": (t_end - ep["start_tick"]) if ep else None,
                    "task_kind": e.task.work_kind, "task_label": label_of(e.task.payload), "task_payload": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in dict(e.task.payload or {}).items()},
                    "is_asleep": bool(is_asleep(e)), "sleep_debt": e.biological.sleep_debt, "wake_line": SLEEP_DEBT.wake_line,
                    "debt_below_wake_line": e.biological.sleep_debt < SLEEP_DEBT.wake_line, "task_end_tick": te, "sleep_ended": te is not None,
                    "walk_decision_ticks_since_task_end": dec_since[:40], "walk_decisions_since_task_end": len(dec_since), "target_writes_outside_actions_since_task_end": len(tgt_since),
                    "hp": e.combat.hp, "stored_target": list(e.navigation.target) if e.navigation.target is not None else None,
                })
    except Exception:
        v4_exc["last_tick"] += 1
    v4_end = {"alive_by_kind": Counter(), "total_by_kind": Counter(), "alive_by_role": Counter(), "total_by_role": Counter(), "dead_by_cause": Counter(), "dead_by_kind": Counter(), "dead_by_cause_and_kind": Counter()}
    try:
        for eid, e in state.entities.items():
            rl = str(int(e.identity.role))
            v4_end["total_by_kind"][e.kind] += 1
            v4_end["total_by_role"][rl] += 1
            if e.combat.alive:
                v4_end["alive_by_kind"][e.kind] += 1
                v4_end["alive_by_role"][rl] += 1
            else:
                dr = e.lifecycle.death_record
                cause = dr.cause.value if dr is not None else "NO_RECORD"
                v4_end["dead_by_cause"][cause] += 1
                v4_end["dead_by_kind"][e.kind] += 1
                v4_end["dead_by_cause_and_kind"][f"{cause}|{e.kind}"] += 1
    except Exception:
        v4_exc["end_census"] += 1
    for eid, ep in list(episodes_open.items()):
        close_episode(ep, t_end, "still_hold_at_end")

    def gap_rows(ep):
        """Typed-wait gap steps: HOLD steps from entry up to (excluding) the next decision tick."""
        nd = ep["next_decision"]
        lim = nd["tick"] if nd else None
        rows = [r for r in ep["step_rows"] if lim is None or r["tick"] < lim]
        return [{"tick": r["tick"], "branch": r["branch"], "stored_target_present": r["stored_target"] is not None, "stored_target_writer": r["stored_target_writer"],
                 "oa_events": len(r["oa"]), "oa_damage": sum((o.get("damage_taken") or 0) for o in r["oa"]), "died_within_10": r["died_within_10"], "hold_task_status": r["hold_task_status"]}
                for r in rows]

    ep_rows = []
    for ep in episodes_done:
        e2 = {k: v for k, v in ep.items() if k != "step_rows"}
        if ep["cls"] == "typed_wait":
            g = gap_rows(ep)
            e2["gap_steps"] = g
            e2["gap_step_count"] = len(g)
            e2["gap_oa_events"] = sum(x["oa_events"] for x in g)
            e2["gap_oa_damage"] = sum(x["oa_damage"] for x in g)
            e2["gap_steps_with_stored_target"] = sum(1 for x in g if x["stored_target_present"])
            e2["gap_deaths_within_10"] = sum(1 for x in g if x["died_within_10"])
        ep_rows.append(e2)
    ep_by_cls = defaultdict(list)
    for e2 in ep_rows:
        ep_by_cls[e2["cls"]].append(e2)
    dist = {cls: dict(Counter(bucket(e2["length"]) for e2 in rows)) for cls, rows in ep_by_cls.items()}
    tw = ep_by_cls.get("typed_wait", [])
    tw_summary = {
        "episodes": len(tw), "with_next_decision": sum(1 for e2 in tw if e2["next_decision"]),
        "next_decision_same_target": sum(1 for e2 in tw if e2["next_decision"] and e2["next_decision"]["same_target_as_at_entry"] is True),
        "next_decision_different_target": sum(1 for e2 in tw if e2["next_decision"] and e2["next_decision"]["same_target_as_at_entry"] is False),
        "next_decision_no_target_or_no_stored": sum(1 for e2 in tw if e2["next_decision"] and e2["next_decision"]["same_target_as_at_entry"] is None),
        "ended_by": dict(Counter((e2["next_decision"] or {}).get("woken_by", "none_seen") for e2 in tw)),
        "gap_steps": sum(e2["gap_step_count"] for e2 in tw), "gap_steps_with_stored_target": sum(e2["gap_steps_with_stored_target"] for e2 in tw),
        "gap_oa_events": sum(e2["gap_oa_events"] for e2 in tw), "gap_oa_damage": sum(e2["gap_oa_damage"] for e2 in tw), "gap_deaths_within_10": sum(e2["gap_deaths_within_10"] for e2 in tw),
        "gap_steps_by_branch": dict(Counter(x["branch"] for e2 in tw for x in e2["gap_steps"])),
        "gap_steps_by_target_writer": dict(Counter(x["stored_target_writer"] for e2 in tw for x in e2["gap_steps"] if x["stored_target_present"])),
        "episodes_with_stored_target_at_entry": sum(1 for e2 in tw if e2["stored_target_at_entry"] is not None),
    }
    c["episodes"] = len(ep_rows)
    for cls, rows in ep_by_cls.items():
        c[f"episodes_class_{cls}"] = len(rows)
        c[f"episodes_class_{cls}_with_steps"] = sum(1 for e2 in rows if e2["steps"] > 0)
        c[f"episodes_class_{cls}_outlived_task"] = sum(1 for e2 in rows if e2.get("outlived_task_by", 0) > 0)
        c[f"episodes_class_{cls}_50plus"] = sum(1 for e2 in rows if e2["length"] >= 50)
    c["episodes_still_hold_at_end"] = sum(1 for e2 in ep_rows if e2["ended"] == "still_hold_at_end")
    c["episodes_unattributed_writer"] = sum(1 for e2 in ep_rows if e2["writer_site"] == "UNATTRIBUTED")
    outlived_by_label = defaultdict(lambda: {"episodes": 0, "outlived_ticks": 0})
    for e2 in ep_rows:
        if e2.get("outlived_task_by", 0) > 0:
            o = outlived_by_label[str(e2["entry_label"])]
            o["episodes"] += 1
            o["outlived_ticks"] += e2["outlived_task_by"]
    doc = {
        "world": world, "seed": seed, "ticks": ticks, "hashseed": os.environ.get("PYTHONHASHSEED"), "plain": plain, "final_hash": final_hash,
        "match": (None if (plain or want is None) else final_hash == want), "exceptions": dict(exc), "counts": dict(c),
        "counts_by_class_and_label": {k: dict(v) for k, v in by.items()},
        "distinct_hold_call_ticks": len(sets["ticks"]), "distinct_hold_call_subjects": len(sets["subjects"]),
        "distinct_outlived_step_ticks": len(sets["o_ticks"]), "distinct_outlived_step_subjects": len(sets["o_subjects"]),
        "wander_no_stored_target": dict(wander_notarget), "episode_length_distribution_by_class": dist,
        "episodes_outlived_task_by_entry_label": {k: dict(v) for k, v in outlived_by_label.items()},
        "typed_wait_summary": tw_summary, "episodes_by_writer_site": dict(Counter(e2["writer_site"] for e2 in ep_rows)),
        "episodes_by_end": dict(Counter(f"{e2['cls']}:{e2['ended']}:{e2['end_mode']}:{e2['end_site']}" for e2 in ep_rows)),
        "rows_cap": CAP, "hold_rows": hold_rows[:CAP],
        "episodes_50plus": [e2 for e2 in ep_rows if e2["length"] >= 50][:CAP],
        "episodes_with_steps": [{k: v for k, v in e2.items() if k != "gap_steps"} for e2 in ep_rows if e2["steps"] > 0][:CAP],
        "episodes_outlived_task": [{k: v for k, v in e2.items() if k != "gap_steps"} for e2 in ep_rows if e2.get("outlived_task_by", 0) > 0][:CAP],
        "typed_wait_episodes": tw[:CAP],
        "v6": {"spy": "hold_spy_v7", "subject": int(os.environ.get("V6_SUBJECT", "32")), "lo": int(os.environ.get("V6_LO", "500")), "hi": int(os.environ.get("V6_HI", "590")),
               "rows": [dict(r_, tact=(v5_dec.get((r_["tick"], int(os.environ.get("V6_SUBJECT", "32")))) or {}).get("tact"), strat=(v5_dec.get((r_["tick"], int(os.environ.get("V6_SUBJECT", "32")))) or {}).get("strat")) for r_ in v6_rows]},
        "v5": {
            "spy": "hold_spy_v5", "v5_exceptions": dict(v5_exc),
            "episodes_all": v5_all,
            "collapse_lag_1tick": [e_ for e_ in v5_all if e_["cls"] == "collapse" and e_.get("outlived_task_by") == 1],
            "collapse_lag_1tick_count": sum(1 for e_ in v5_all if e_["cls"] == "collapse" and e_.get("outlived_task_by") == 1),
            "avoid_no_route_episodes": sum(1 for e_ in v5_all if e_["entry_label"] == "AVOID_NO_ROUTE"),
            "avoid_no_route_episodes_hit_while_holding": sum(1 for e_ in v5_all if e_["entry_label"] == "AVOID_NO_ROUTE" and e_["hit_rows"] > 0),
            "rechosen_wait_summary_50plus": {
                "episodes_with_fresh_waits": sum(1 for e_ in v4_eps if (e_.get("VERDICT", {}).get("V5") or {}).get("fresh_wait_ticks", 0) > 0),
                "fresh_wait_ticks_total": sum((e_.get("VERDICT", {}).get("V5") or {}).get("fresh_wait_ticks", 0) for e_ in v4_eps),
                "longest_run": max([(e_.get("VERDICT", {}).get("V5") or {}).get("longest_run_of_consecutive_fresh_waits", 0) for e_ in v4_eps] or [0]),
                "stop_i_candidates": [e_["entity"] for e_ in v4_eps if (e_.get("VERDICT", {}).get("V5") or {}).get("STOP_i_candidate")],
            },
        },
        "v4": {
            "spy": "hold_spy_v4", "v4_exceptions": dict(v4_exc),
            "whole_run_combat_multi_or_oa_path_only": dict(v4_all),
            "episodes_50plus_verdicts": v4_eps,
            "last_tick_hold_entities": v4_last,
            "deaths": v4_deaths, "deaths_total": len(v4_deaths),
            "end_census": {k: dict(v) for k, v in v4_end.items()},
        },
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True, default=str), encoding="utf-8")
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
    print(json.dumps({"final_hash": final_hash, "match": doc["match"], "exceptions": dict(exc), "hold_calls": c["hold_calls"], "hold_steps": c["hold_steps"],
                      "episodes": c["episodes"]}))
    if want is not None and final_hash != want:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
