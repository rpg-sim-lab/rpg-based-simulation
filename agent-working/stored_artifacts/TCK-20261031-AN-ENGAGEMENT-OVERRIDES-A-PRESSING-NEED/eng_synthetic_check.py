"""Synthetic substitute for the s44 known case (rpg-planner ruling): a subject past need onset in an ATTACK task against a hostile that is neither adjacent nor acting
on it is tagged ENG; flip the hostile to acting (its task attacks the subject) and it is NOT tagged; make it adjacent and it is NOT tagged; with no pressing need NOT tagged."""
import copy, dataclasses
from tools.test_architecture.rpg_gate_run import build_kernel
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("eng_classifier", os.path.join(os.path.dirname(os.path.abspath(__file__)), "eng_classifier.py"))
ec = importlib.util.module_from_spec(spec); spec.loader.exec_module(ec)

k = build_kernel("urban_political", 42, "eng_synth_%d" % os.getpid())
st = k.state
ents = [e for e in st.entities.values() if e.combat.alive]
A, B = ents[0], ents[1]


def setattr_deep(obj, **kw):
    for n, v in kw.items():
        object.__setattr__(obj, n, v)


def put(e, pos=None, payload=None, hunger=None):
    if pos is not None: object.__setattr__(e.navigation, "position", pos)
    if payload is not None: object.__setattr__(e.task, "payload", payload); object.__setattr__(e.task, "work_kind", "ENTITY_ACT")
    if hunger is not None: object.__setattr__(e.biological, "hunger", hunger)


ax, ay = A.navigation.position
perceived = lambda e, s: [B] if e.id == A.id else []
results = []
def case(name, expect, **kw):
    put(A, hunger=kw.get("hunger", 80.0), payload={"action": "ATTACK", "target_id": B.id}, pos=(ax, ay))
    put(B, pos=kw.get("bpos", (ax + 5, ay)), payload=kw.get("bpayload", {"action": "HOLD"}))
    got = bool(ec.is_eng(A, st, perceived=perceived))
    results.append((name, expect, got)); print(("PASS" if got == expect else "FAIL"), name, "expected", expect, "got", got)

case("pressing, hostile 5 away, not acting -> ENG", True)
case("hostile acting (attacks the subject) -> not ENG", False, bpayload={"action": "ATTACK", "target_id": A.id})
case("hostile adjacent, not acting -> not ENG", False, bpos=(ax + 1, ay))
case("no pressing need (hunger 10) -> not ENG", False, hunger=10.0)
k.shutdown()
import shutil; shutil.rmtree(os.path.join("data", "runs", "eng_synth_%d" % os.getpid()), ignore_errors=True)
sys.exit(0 if all(e == g for _, e, g in results) else 1)
