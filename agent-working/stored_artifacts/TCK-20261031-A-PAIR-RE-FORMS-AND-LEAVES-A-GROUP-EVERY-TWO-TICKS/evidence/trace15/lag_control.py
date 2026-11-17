"""Positive control for the FULFILLED-vs-expiry lag measure: a contract made to run late must show a non-zero lag. Two parts, both through the real code.
(a) m15_sum.summ on a synthetic dissolution row whose tick is 3 after the contract's expiry -> lag histogram {3: 1}; a row on the expiry tick -> {0: 1}.
(b) the real GroupSystem.update_groups with a StateUpdate whose dirty set does NOT contain the bound group, at a tick past the contract's expiry: the group is not dissolved that
    tick (a late end is possible and observable), and with the group in the dirty set it dissolves on the tick (FULFILLED)."""
import sys, os
sys.path.insert(0, "."); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, "tests/unit/social")
import m15_sum
base = dict(forms=[], mbt=[], lag=[], overdue_ticks=0, overdue_not_relevant=0, ended_seen=0, full_scan_ticks=0, deaths=[], active_pairs={}, dis_other=[])
late = dict(base, dis=[[53, 10000, [1, 2], "r1", "BINDING_CONTRACT_NOT_ACTIVE", "FULFILLED", 1, 1, 50]])
ontime = dict(base, dis=[[50, 10000, [1, 2], "r1", "BINDING_CONTRACT_NOT_ACTIVE", "FULFILLED", 1, 1, 50]])
a = m15_sum.summ(late, True)["fulfilled_lag_hist_tick_minus_expiry"]; b = m15_sum.summ(ontime, True)["fulfilled_lag_hist_tick_minus_expiry"]
print("CONTROL_A late row lag hist", a, "on-time row lag hist", b); assert a == {3: 1} and b == {0: 1}
import test_group_contract_binding as T
from dataclasses import replace
from src.core.updates import StateUpdate
from src.core.dirty import DirtySet
from src.systems.world_systems.groups import GroupSystem
state = T._state(53, contract=T._contract(expiry=50), group=T._bound_group(last_leadership_check_tick=53))
not_dirty = StateUpdate(dirty_set=DirtySet())
r1 = GroupSystem.update_groups(state, not_dirty)
dirty = StateUpdate(dirty_set=DirtySet(group_ids={10000}))
r2 = GroupSystem.update_groups(state, dirty)
print("CONTROL_B group outside the dirty set dissolved:", any(g.dissolution_tick == 53 for g in r1.groups_add_or_update), "| inside:", [(g.dissolution_tick, g.dissolution_reason.value, g.dissolution_contract_status.value) for g in r2.groups_add_or_update])
assert not any(g.dissolution_tick == 53 for g in r1.groups_add_or_update) and any(g.dissolution_tick == 53 for g in r2.groups_add_or_update)
print("LAG_CONTROL_OK")
