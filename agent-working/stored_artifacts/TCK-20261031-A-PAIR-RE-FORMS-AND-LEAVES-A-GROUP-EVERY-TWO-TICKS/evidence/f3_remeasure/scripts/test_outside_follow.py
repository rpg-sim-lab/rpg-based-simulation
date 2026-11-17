"""Planted-state test: the instrument fires on each condition and counts nothing on a quiet state."""
import sys; sys.path.insert(0, "/data/vboxuser/Work/groups_base")
from types import SimpleNamespace as N
import outside_follow as of
OFFS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
def ent(pos, target=None, payload=None, lodged=None, alive=True):
    return N(navigation=N(position=pos, target=target, lodged_in=lodged), task=N(payload=payload or {}), combat=N(alive=alive))
def state(member):
    return N(tick=7, entities={1: ent((10.0, 10.0), lodged=5), 2: member}, groups={9: N(id=9, leader_id=1, member_ids={1, 2}, dissolution_tick=None)})
lodged = lambda e: e.navigation.lodged_in
def run(member):
    acc = of.new_acc(); of.count(state(member), lodged, OFFS, 3, acc); return acc
a = run(ent((20.0, 20.0)));                                               assert a["denominator"] == 1 and a["any"] == 0, a   # quiet outside member: counted in the denominator only
a = run(ent((20.0, 20.0), target=(10.0, 10.0)));                         assert a["c_building_tile"] == 1 and a["any"] == 1, a
a = run(ent((20.0, 20.0), payload={"target_position": (10.0, 11.0)}));   assert a["c_reach_orth"] == 1 and a["c_building_tile"] == 0, a
a = run(ent((20.0, 20.0), target=(12.0, 11.0)));                         assert a["c_ring"] == 1 and a["c_reach_orth"] == 0, a
a = run(ent((20.0, 20.0), payload={"target_id": 1}));                    assert a["c_target_id"] == 1, a
a = run(ent((20.0, 20.0), payload={"reason": "REGROUP"}));               assert a["c_reason"] == 1 and a["reasons"]["REGROUP"] == 1, a
a = run(ent((20.0, 20.0), lodged=5));                                    assert a["denominator"] == 0, a   # a lodged member is not an outside member
a = run(ent((20.0, 20.0), alive=False));                                 assert a["denominator"] == 0, a
print("OUTSIDE_FOLLOW_INSTRUMENT_OK")
