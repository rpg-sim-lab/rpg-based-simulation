"""Recruitment-path spy (rpg-implementer, DRAFT for rpg-designer approval; NOT run, NOT smoked).
TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD. Read-only: every wrapper calls the original and returns ITS object unchanged; the tick loop only calls kernel.tick_once();
the per-tick scan only reads kernel.state. Same build as rejcount_spy (tools.test_architecture.rpg_gate_run.build_kernel, audit_mode / no_frame_pacing checked). Run with the tree as cwd and PYTHONPATH.
Usage: python recruit_spy.py <world> <seed> <ticks> <out.json> [PLAIN | <expected final_hash>]. PLAIN = no wrapper, no scan (the plain twin; prints and stores its hash). A hash given = exit 3 on mismatch.
Hooks (class attributes, patched and restored; each wrapper appends a row, then returns the original result):
  (a) creation: ContractService.create_recruitment_contract (cooperation site, services.py ~:284 and any other caller; row: tick, id, source, target, daily_pay, caller file:line);
      CoreActions.execute_recruit (the RECRUIT action; row per call: tick, actor, target_id, payout, created = the ids of ContractState values in the returned updates, with their status).
      Any RECRUITMENT contract the scan first sees whose id was named by neither wrapper is listed as `unattributed_creations` (id, tick, source, target) = a creation site not named in the ticket.
  (b)/(d) appraisal: SocialAppraisalSystem.appraise_contract, rows for kind == RECRUITMENT only (tick, entity = appraiser, source, contract id, status, reason, origin = 'action' when id == 'temp_eval' else 'other');
      a row whose reason is TOTAL_DISTRUST or BETRAYAL_HISTORY was stopped before the kind dispatch at appraisal.py:83. SocialAppraisalSystem._appraise_recruitment: one row per call (tick, entity, source, status, reason) = the P1 hook, to cross-check zero.
  (c) acceptance: CooperationDecisionService.accept_pending_offer (the JOIN_PARTY selection; row: tick, entity, offerer, contract id), ContractService.accept_contract (row: tick, offerer, contract id, kind, caller),
      SocialContractSystem.transition_contract (RECRUITMENT contracts only; row: tick, contract id, from, to, caller). Per-tick scan of kernel.state (reads only): every contract of kind RECRUITMENT (first seen tick, source, target, status changes
      [(tick, status)], last seen tick, the tick it left its holder's dict, holder alive at that tick) and every group (first seen tick, id, contract_id, holder, members, contract kind, and its path:
      'cooperation_accept' if the contract id was passed to accept_contract or to a JOIN_PARTY selection before the group's first-seen tick, 'execute_recruit' if it was created ACTIVE by execute_recruit, else 'other').
  SHADOW (allowed because appraise_contract is pure on main: appraisal.py:29-115 and _appraise_recruitment :118-185 read entity/contract/state and return a tuple; no RNG, no state write, no cache; ClanLifecycleService.find_clan_id_for_entity is a
      read-only sorted scan): at each JOIN_PARTY selection the unwrapped appraise_contract(entity, the offered contract, state) is called with the `state` of the calling frame (CooperationPhase.execute) and its
      (status, reason) stored as `shadow` with the inputs it reads (trust inputs: bond sentiment or trust_history, offerer public_reputation, betrayal_count, rejection_count, pay, risk, hp_pct, gold). Inputs and verdicts only; no class. While it runs, the
      _appraise_recruitment wrapper marks its row origin 'shadow' and (d) excludes it. The hash must still equal the plain twin's: that is the backing for purity.
Output JSON: world, seed, ticks, final_hash, counts (a)-(d) summaries, and all rows. Counts are derived after the run from the rows."""
from __future__ import annotations
import json, os, sys
from collections import Counter


def main(argv):
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    mode = argv[4] if len(argv) > 4 else None
    plain = mode == "PLAIN"
    want = None if plain else mode
    from src.core.strategic import ContractKind, ContractStatus, ContractState
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel
    run_id = f"rpgrec_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    if getattr(kernel, "_audit_mode", None) is not True or getattr(kernel, "_no_frame_pacing", None) is not True:
        print("BAD_BUILD")
        return 2
    cur = {"tick": None, "shadow": False}
    rows = {k: [] for k in ("create_coop", "execute_recruit", "appraise", "appraise_recruitment", "join_party", "accept_contract", "transition")}
    named_ids, active_from_action, coop_accepted = set(), set(), set()
    contracts, groups, unattributed = {}, {}, []
    patches = []

    def caller(depth=2):
        f = sys._getframe(depth)
        return f"{os.path.basename(f.f_code.co_filename)}:{f.f_lineno}:{f.f_code.co_name}"

    def val(x):
        return getattr(x, "value", str(x))

    if not plain:
        from src.domains.cooperation.services import CooperationDecisionService
        from src.engine.domain.core_actions import CoreActions
        from src.systems.social_systems.appraisal import SocialAppraisalSystem
        from src.systems.social_systems.contracts import ContractService, SocialContractSystem

        o_create = ContractService.create_recruitment_contract
        o_exec = CoreActions.execute_recruit
        o_appr = SocialAppraisalSystem.appraise_contract
        o_apprr = SocialAppraisalSystem._appraise_recruitment
        o_join = CooperationDecisionService.accept_pending_offer
        o_acc = ContractService.accept_contract
        o_trans = SocialContractSystem.transition_contract

        def s_create(contract_id, source_id, target_id, daily_pay=10, duration_ticks=100, risk_level=None, tick=0):
            kw = dict(daily_pay=daily_pay, duration_ticks=duration_ticks, tick=tick)
            if risk_level is not None:
                kw["risk_level"] = risk_level
            res = o_create(contract_id, source_id, target_id, **kw)
            named_ids.add(contract_id)
            rows["create_coop"].append({"tick": cur["tick"], "id": contract_id, "source": source_id, "target": target_id, "daily_pay": daily_pay, "caller": caller()})
            return res

        def s_exec(entity, payload, current_tick, neighbor_view, context):
            res = o_exec(entity, payload, current_tick, neighbor_view, context)
            made = []
            for upd in (res or {}).values():
                strat = getattr(upd, "strategic", None)
                for c in (getattr(strat, "contracts_add_or_update", None) or []):
                    if c.kind == ContractKind.RECRUITMENT:
                        made.append({"id": c.id, "status": val(c.status)})
                        named_ids.add(c.id)
                        if c.status == ContractStatus.ACTIVE:
                            active_from_action.add(c.id)
            rows["execute_recruit"].append({"tick": cur["tick"], "actor": entity.id, "target_id": (payload or {}).get("target_id"), "payout": (payload or {}).get("payout", 100), "created": made})
            return res

        def s_appr(entity, contract, state):
            res = o_appr(entity, contract, state)
            if contract.kind == ContractKind.RECRUITMENT and not cur["shadow"]:
                rows["appraise"].append({"tick": cur["tick"], "entity": entity.id, "source": contract.source_id, "contract": contract.id,
                                         "origin": "action" if contract.id == "temp_eval" else "other", "status": val(res[0]), "reason": val(res[1])})
            return res

        def s_apprr(entity, contract, trust_score):
            res = o_apprr(entity, contract, trust_score)
            rows["appraise_recruitment"].append({"tick": cur["tick"], "entity": entity.id, "source": contract.source_id, "contract": contract.id,
                                                 "origin": "shadow" if cur["shadow"] else ("action" if contract.id == "temp_eval" else "other"),
                                                 "status": val(res[0]), "reason": val(res[1])})
            return res

        def s_join(entity, pending_offer):
            res = o_join(entity, pending_offer)
            offerer_id, contract_id = pending_offer
            coop_accepted.add(contract_id)
            row = {"tick": cur["tick"], "entity": entity.id, "offerer": offerer_id, "contract": contract_id, "shadow": None}
            f = sys._getframe(1)
            state = f.f_locals.get("state")
            offerer = state.entities.get(offerer_id) if state is not None else None
            contract = offerer.strategic.contracts.get(contract_id) if offerer is not None else None
            if contract is not None:
                bond = entity.social.bonds.get(offerer_id)
                inputs = {"bond_sentiment": None if bond is None else bond.sentiment, "trust_history": entity.social.trust_history.get(offerer_id),
                          "offerer_public_reputation": offerer.social.public_reputation, "betrayal_count": entity.social.betrayal_count,
                          "rejection_count": entity.social.rejection_count.get(offerer_id, 0), "daily_pay": contract.terms.get("daily_pay"),
                          "risk": str(contract.terms.get("risk_level")), "hp_pct": entity.combat.hp / entity.combat.max_hp, "gold": entity.inventory.gold}
                cur["shadow"] = True
                try:
                    sres = o_appr(entity, contract, state)
                finally:
                    cur["shadow"] = False
                row["shadow"] = {"status": val(sres[0]), "reason": val(sres[1]), "inputs": inputs}
            rows["join_party"].append(row)
            return res

        def s_acc(entity, contract_id, tick):
            res = o_acc(entity, contract_id, tick)
            c = entity.strategic.contracts.get(contract_id)
            if c is not None and c.kind == ContractKind.RECRUITMENT:
                coop_accepted.add(contract_id)
            rows["accept_contract"].append({"tick": cur["tick"], "offerer": entity.id, "contract": contract_id, "kind": None if c is None else val(c.kind), "caller": caller()})
            return res

        def s_trans(entity, contract_id, new_status, tick):
            res = o_trans(entity, contract_id, new_status, tick)
            c = entity.strategic.contracts.get(contract_id)
            if c is not None and c.kind == ContractKind.RECRUITMENT:
                rows["transition"].append({"tick": cur["tick"], "contract": contract_id, "from": val(c.status), "to": val(new_status),
                                           "applied": bool(res[0].contracts_add_or_update), "caller": caller()})
            return res

        for owner, name, orig, spy in (
            (ContractService, "create_recruitment_contract", o_create, s_create), (CoreActions, "execute_recruit", o_exec, s_exec),
            (SocialAppraisalSystem, "appraise_contract", o_appr, s_appr), (SocialAppraisalSystem, "_appraise_recruitment", o_apprr, s_apprr),
            (CooperationDecisionService, "accept_pending_offer", o_join, s_join), (ContractService, "accept_contract", o_acc, s_acc),
            (SocialContractSystem, "transition_contract", o_trans, s_trans),
        ):
            patches.append((owner, name, orig))
            setattr(owner, name, staticmethod(spy))

    def scan(state, tick):
        held = set()
        for eid in sorted(state.entities):
            e = state.entities[eid]
            for cid, c in e.strategic.contracts.items():
                if c.kind != ContractKind.RECRUITMENT:
                    continue
                held.add(cid)
                r = contracts.get(cid)
                if r is None:
                    contracts[cid] = {"id": cid, "holder": eid, "source": c.source_id, "target": c.target_id, "first_seen": tick, "status_changes": [[tick, val(c.status)]], "left_tick": None, "holder_alive_at_left": None}
                    if cid not in named_ids:
                        unattributed.append({"id": cid, "tick": tick, "source": c.source_id, "target": c.target_id, "status": val(c.status)})
                elif r["status_changes"][-1][1] != val(c.status):
                    r["status_changes"].append([tick, val(c.status)])
        for cid, r in contracts.items():
            if r["left_tick"] is None and cid not in held:
                r["left_tick"] = tick
                h = state.entities.get(r["holder"])
                r["holder_alive_at_left"] = bool(h is not None and h.combat.alive)
        for gid, g in state.groups.items():
            if gid in groups:
                continue
            kind = None
            holder = state.entities.get(g.contract_holder_id) if g.contract_holder_id is not None else None
            c = holder.strategic.contracts.get(g.contract_id) if holder is not None and g.contract_id else None
            if c is not None:
                kind = val(c.kind)
            elif g.contract_id in contracts:
                kind = "RECRUITMENT"
            if g.contract_id is None:
                path = "no_contract"
            elif g.contract_id in coop_accepted:
                path = "cooperation_accept"
            elif g.contract_id in active_from_action:
                path = "execute_recruit"
            else:
                path = "other"
            groups[gid] = {"id": gid, "first_seen": tick, "contract": g.contract_id, "holder": g.contract_holder_id, "members": sorted(g.member_ids), "contract_kind": kind, "path": path}

    try:
        for _ in range(ticks):
            cur["tick"] = kernel.state.tick
            kernel.tick_once()
            if not plain:
                scan(kernel.state, kernel.state.tick)
        state = kernel.state
    finally:
        for owner, name, orig in patches:
            setattr(owner, name, staticmethod(orig))
    kernel.shutdown()
    final_hash = CanonicalStateHasher.get_hash(state)
    if plain:
        doc = {"world": world, "seed": seed, "ticks": ticks, "final_hash": final_hash, "plain": True}
        json.dump(doc, open(out, "w", encoding="utf-8"), sort_keys=True)
        print(f"PLAIN hash={final_hash[:12]}")
        return 0
    appr_rec = [r for r in rows["appraise_recruitment"] if r["origin"] != "shadow"]
    counts = {
        "a_created_coop": len(rows["create_coop"]),
        "a_execute_recruit_calls": len(rows["execute_recruit"]),
        "a_execute_recruit_created": sum(len(r["created"]) for r in rows["execute_recruit"]),
        "a_recruit_contracts_seen": len(contracts),
        "a_unattributed": len(unattributed),
        "b_appraise_contract_recruitment": len(rows["appraise"]),
        "b_stopped_before_dispatch": sum(1 for r in rows["appraise"] if r["reason"] in ("TOTAL_DISTRUST", "BETRAYAL_HISTORY")),
        "c_join_party_selections": len(rows["join_party"]),
        "c_accept_contract_calls": len(rows["accept_contract"]),
        "c_transitions_to": dict(sorted(Counter(r["to"] for r in rows["transition"] if r["applied"]).items())),
        "c_final_contract_status": dict(sorted(Counter(r["status_changes"][-1][1] for r in contracts.values()).items())),
        "c_left_dict": sum(1 for r in contracts.values() if r["left_tick"] is not None),
        "c_groups_formed": len(groups),
        "c_groups_by_path": dict(sorted(Counter(g["path"] for g in groups.values()).items())),
        "c_groups_by_contract_kind": dict(sorted(Counter(str(g["contract_kind"]) for g in groups.values()).items())),
        "d_appraisals_reached_recruitment_branch": len(appr_rec),
        "d_by_origin": dict(sorted(Counter(r["origin"] for r in appr_rec).items())),
        "shadow_verdicts": dict(sorted(Counter(f'{(r["shadow"] or {}).get("status")}|{(r["shadow"] or {}).get("reason")}' for r in rows["join_party"]).items())),
    }
    doc = {"world": world, "seed": seed, "ticks": ticks, "final_hash": final_hash, "counts": counts, "rows": rows,
           "contracts": [contracts[k] for k in sorted(contracts)], "groups": [groups[k] for k in sorted(groups)], "unattributed_creations": unattributed}
    json.dump(doc, open(out, "w", encoding="utf-8"), sort_keys=True, default=str)
    print(" ".join(f"{k}={v}" for k, v in counts.items() if not isinstance(v, dict)) + f" hash={final_hash[:12]}")
    if want is not None and final_hash != want:
        print(f"HASH_MISMATCH want={want[:12]} got={final_hash[:12]}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
