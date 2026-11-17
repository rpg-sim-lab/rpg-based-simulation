"""The ENGAGEMENT_OVERRIDES classifier exactly as eng_probe.py evaluates it inline (same expression), as a function so it can be checked on a synthetic state."""
from src.ai.goals import present_threat as _pt
from src.ai.goals.scorers_support import perceived_hostiles as _ph
from src.engine.need_pull import need_is_pressing


def man1(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def threat_split(e, st, perceived=None):
    hs = (perceived or _ph)(e, st)
    adj = any(man1(h.navigation.position, e.navigation.position) <= 1 for h in hs)
    return adj, any(_pt.hostile_acts_on(h, e, st.tick) for h in hs)


def is_eng(e, st, skip_site=False, perceived=None):
    pl = e.task.payload or {}
    act = pl.get("action")
    cpj = e.strategic.projects.get(e.strategic.current_project_id) if e.strategic.current_project_id else None
    pk = str(getattr(cpj.kind, "value", cpj.kind)).lower() if cpj is not None else None
    pr = need_is_pressing(e.biological.hunger, e.biological.sleep_debt)
    adj, acting = threat_split(e, st, perceived)
    return pr and not (adj or acting) and (act == "ATTACK" or pk == "combat_engage" or skip_site)
