"""Read-only counts for the lifecycle pin question: ACTIVE contracts per tick, contracts created per tick, and (after tree only) why MEMBERS_BELOW_TWO happened.
Usage: CNT_OUT=<json> python cnt_run.py <world> <seed> <ticks>  (cwd = tree, PYTHONPATH = tree). Wraps ApplyPath.apply_generation and GroupSystem.update_groups only."""
import json, os, sys, collections
sys.path.insert(0, ".")
from src.engine.apply import ApplyPath
from src.systems.world_systems.groups import GroupSystem
series = []; mbt = collections.Counter(); mbt_rows = []
oa = ApplyPath.apply_generation
def ag(prior, update, *a, **k):
    new = oa(prior, update, *a, **k)
    seen = {}
    for e in new.entities.values():
        for cid, c in e.strategic.contracts.items(): seen[cid] = c
    st = collections.Counter(str(getattr(c.status, "value", c.status)) for c in seen.values())
    created = sum(1 for c in seen.values() if getattr(c, "created_tick", None) == prior.tick)
    pairs = collections.Counter((min(c.source_id, c.target_id), max(c.source_id, c.target_id)) for c in seen.values() if str(getattr(c.status, "value", c.status)) == "ACTIVE")
    series.append([new.tick, st.get("ACTIVE", 0), st.get("OFFERED", 0), created, max(pairs.values()) if pairs else 0])
    return new
ApplyPath.apply_generation = staticmethod(ag)
ou = GroupSystem.update_groups
def ug(state, *a, **k):
    r = ou(state, *a, **k)
    for row in r.groups_add_or_update:
        if row.dissolution_tick == state.tick and getattr(row, "dissolution_reason", None) is not None and row.dissolution_reason.value == "MEMBERS_BELOW_TWO":
            old = state.groups[row.id]; cu = a[0] if a else k.get("current_update")
            dropped = {}
            for m in old.member_ids:
                if m == old.leader_id: continue
                e = state.entities.get(m)
                upd = cu.entity_updates.get(m) if cu else None
                dead = e is None or not e.combat.alive or not e.lifecycle.active or (upd is not None and upd.combat is not None and upd.combat.alive_set is False)
                dx = (e.navigation.position[0] - old.anchor[0]) if e else 0; dy = (e.navigation.position[1] - old.anchor[1]) if e else 0
                far = (dx * dx + dy * dy) > (old.cohesion_radius * 2) ** 2
                dropped[m] = "dead_or_inactive" if dead else ("distance" if far else "other")
            holder_dropped = old.contract_holder_id in dropped
            key = "holder_dropped" if holder_dropped else "other_member_dropped"
            for cause in set(dropped.values()): mbt[key + ":" + cause] += 1
            mbt_rows.append([state.tick, row.id, old.leader_id, old.contract_holder_id, dropped])
    return r
GroupSystem.update_groups = staticmethod(ug)
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
_run_engine(world, seed, ticks, extra_flags=_load_profile_feature_flags(_resolve_profile(world)), audit_mode=True)
act = [r[1] for r in series]; created = [r[3] for r in series]; maxpair = [r[4] for r in series]
out = dict(world=world, seed=seed, ticks=ticks, sum_active_per_tick=sum(act), mean_active=sum(act)/max(len(act),1), max_active=max(act) if act else 0, contracts_created_total=sum(created), max_active_per_pair_max=max(maxpair) if maxpair else 0,
           active_at=dict((str(r[0]), r[1]) for r in series if r[0] in (50, 100, 150, 200)), members_below_two=dict(mbt), mbt_rows=mbt_rows[:20], series_sample=series[::20])
open(os.environ["CNT_OUT"], "w").write(json.dumps(out, indent=1)); print("CNT_OK")
