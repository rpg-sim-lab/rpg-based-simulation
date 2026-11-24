"""The blocker lifecycle of the strategic pass: infer, resolve, merge on re-inference (divergence 2.214) and remove after a quiet spell; `StrategicIntelligenceSystem` delegates here."""
from __future__ import annotations

import ast
from dataclasses import replace
from typing import Any, Dict, Optional, Tuple

from src.content.blocker_settings import access_giveup_limit
from src.content.navigation_experience_settings import navigation_experience_settings
from src.core.giveup_records import HeldTargetAtAnchorCounts, near_anchor
from src.core.navigation_experience import NavigationExperienceUpdate
from src.core.inventory import InventoryService
from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import (
    CONGESTION_BLOCKER_ID,
    BlockerRemoval,
    BlockerState,
    ObjectiveStatus,
    ProjectEnd,
    ProjectState,
    ProjectStatus,
    end_record,
    merge_inferred_blocker,
    quiet_blockers,
)
from src.core.updates import (
    EntityUpdate,
    IdentityUpdate,
    NavigationUpdate,
    StateUpdate,
    StrategicUpdate,
)
from src.systems.strategic_systems.navigation_experience_step import (
    navigation_experience_update,
)


def reinferred_blockers_update(entity: EntityState, staged: StrategicUpdate, inferred: StrategicUpdate, tick: int) -> StrategicUpdate:
    """``staged`` with this pass's blocker inference folded in (divergence 2.214): a re-inferred blocker MERGES into the stored one (keeps its suppression and failure count, refreshes what is
    observed; `merge_inferred_blocker`), never replaces it; then the quiet-spell removals (`quiet_spell_update`) are merged on top."""
    additions = list(staged.blockers_add_or_update)
    for b in inferred.blockers_add_or_update:
        if b.id not in [x.id for x in additions]:
            additions.append(merge_inferred_blocker(entity.strategic.blockers.get(b.id), b, tick))
    staged = replace(staged, blockers_add_or_update=additions)
    quiet = quiet_spell_update(entity, staged, tick)
    return staged if quiet is None else staged.merge(quiet)


def quiet_spell_update(entity: EntityState, staged: StrategicUpdate, tick: int) -> Optional[StrategicUpdate]:
    """Divergence 2.214: a congestion blocker with `BLOCKER_QUIET_SPELL_TICKS` of observable quiet (`quiet_blockers`: no live resolve_blocker project names it, and the spell counts from its
    last sighting, the end of its suppression and the end of the last project that named it) is removed (``blockers_remove``, reason QUIET_SPELL on ``blockers_removed_for``). No project ends
    with it: none naming it is live. A congestion blocker with no last-seen tick (an old checkpoint) is stamped ``tick`` on first sight. A blocker inferred this pass (in
    ``staged.blockers_add_or_update``) is not removed. Reads only; None when nothing is to be written."""
    staged_ids = {b.id for b in staged.blockers_add_or_update}
    stored = entity.strategic.blockers
    gone = [i for i in quiet_blockers(stored, entity.strategic.projects, tick) if i not in staged_ids and i not in staged.blockers_remove]
    stamps = [replace(b, last_seen_tick=tick) for b in stored.values() if b.id == CONGESTION_BLOCKER_ID and b.last_seen_tick is None and b.id not in staged_ids]
    if not gone and not stamps:
        return None
    return StrategicUpdate(blockers_add_or_update=stamps, blockers_remove=gone, blockers_removed_for={i: BlockerRemoval.QUIET_SPELL for i in gone})


def infer_blockers(
    entity: EntityState,
    last_task: str,
    last_payload: Dict[str, Any],
    navigation_failure: Optional[str] = None,
    current_project: Optional[ProjectState] = None
) -> StrategicUpdate:
    """
    Infer blockers based on recent failures.
    Logic ID: STRAT-191 (Blockers have kind)
    Logic ID: STRAT-192 (Blockers have subject/reference)
    Logic ID: STRAT-193 (Blockers have severity)
    Logic ID: STRAT-194 (Blockers have origin/spawned-from reference where useful)
    VERIFIED v2: strategic_blocker_inference
    """
    blockers = []

    # 1. Navigation Failure (ACCESS blocker)
    if navigation_failure in ("PATH_NOT_FOUND", "STUCK", "OSCILLATING"):
        target_pos = last_payload.get("target_position")
        if target_pos:
            subject = f"{target_pos}"
            kind = "access"
            blockers.append(BlockerState(
                id=f"blocker_access_{int(target_pos[0])}_{int(target_pos[1])}",
                kind=kind,
                subject=subject,
                severity=0.8
            ))

    # Phase 4: Congestion Blocker
    if entity.navigation.wait_count >= 5 or entity.navigation.oscillation_count >= 3:
         blockers.append(BlockerState(
             id=CONGESTION_BLOCKER_ID,
             kind="access",
             subject="congestion",
             severity=0.5
         ))

    # 2. Material/Resource Failure (Interactions)
    if last_task == "ENTITY_ACT" and last_payload.get("action") == "INTERACT":
        target_id = last_payload.get("target_id")
        if target_id and current_project and current_project.kind == "harvesting":
            # Check for capacity failure in latest intent results
            capacity_fail = any(r.reason == "INSUFFICIENT_CAPACITY" or r.reason == "INVENTORY_FULL" for r in entity.identity.latest_intent_results)
            if capacity_fail:
                blockers.append(BlockerState(
                    id="blocker_inventory_full",
                    kind="inventory",
                    subject="capacity",
                    severity=1.0
                ))
            else:
                blockers.append(BlockerState(
                    id=f"blocker_node_{target_id}",
                    kind="material",
                    subject="resource", 
                    severity=1.0
                ))

    # 3. Transaction Failures (Generic)
    for result in entity.identity.latest_intent_results:
        if not result.accepted:
            if result.reason in ("INSUFFICIENT_CAPACITY", "INVENTORY_FULL"):
                 blockers.append(BlockerState(
                    id="blocker_inventory_full",
                    kind="inventory",
                    subject="capacity",
                    severity=1.0
                ))
            elif result.reason == "OUT_OF_STOCK":
                blockers.append(BlockerState(
                    id=f"blocker_out_of_stock_{result.source_id}",
                    kind="material",
                    subject="out_of_stock",
                    severity=1.0
                ))
            elif result.reason == "LIQUIDITY_EXHAUSTED":
                blockers.append(BlockerState(
                    id=f"blocker_liquidity_{result.source_id}",
                    kind="material",
                    subject="liquidity",
                    severity=1.0
                ))

    if not blockers:
        return StrategicUpdate()

    # Deduplicate by ID
    unique_blockers = {}
    for b in blockers:
        unique_blockers[b.id] = b

    return StrategicUpdate(blockers_add_or_update=list(unique_blockers.values()))


def generate_crafting_blockers(
    entity: EntityState,
    recipe_mats: Dict[str, int],
    gold_cost: int
) -> StrategicUpdate:
    """
    Produce a StrategicUpdate containing blockers for missing requirements.
    """
    blockers = []
    inv = entity.inventory

    for mat_id, needed in recipe_mats.items():
        have = sum((s.quantity if hasattr(s, "quantity") else 1) for s in inv.items if (s.item_id if hasattr(s, "item_id") else s) == mat_id)
        if have < needed:
            blockers.append(BlockerState(
                id=f"blocker_mat_{mat_id}",
                kind="material",
                subject=mat_id,
                severity=min(1.0, (needed - have) / needed),
                target_quantity=needed
            ))

    if inv.gold < gold_cost:
        blockers.append(BlockerState(
            id="blocker_gold",
            kind="material",
            subject="gold",
            severity=min(1.0, (gold_cost - inv.gold) / gold_cost),
            target_quantity=gold_cost
        ))

    return StrategicUpdate(blockers_add_or_update=blockers)


def resolve_blockers(
    state: AuthoritativeState,
    update: StateUpdate,
    cadence: Any = None  # kept for the delegate's signature; the default is resolved in StrategicIntelligenceSystem.resolve_blockers (import contract)
) -> StateUpdate:
    """
    Resolve strategic blockers that are satisfied by the current or pending
    authoritative inventory state.
    """
    refined_entity_updates = dict(update.entity_updates)

    def has_item(inventory, item_id: str, quantity: int = 1) -> bool:
        if item_id == "gold":
            return inventory.gold >= quantity
        return any(
            stack.item_id == item_id and stack.quantity >= quantity
            for stack in inventory.items
        )

    candidate_ids = list(state.entities.keys())
    for e_id in sorted(candidate_ids):
        entity = state.entities[e_id]
        ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))

        pending_inventory = entity.inventory
        if ent_upd.inventory:
            pending_inventory = InventoryService.apply_update(
                entity.inventory,
                ent_upd.inventory,
            )

        strat_up = ent_upd.strategic or StrategicUpdate()
        removals = set(strat_up.blockers_remove)
        resolved_ids = set()
        # 1. Passive resolution from existing state
        # We ONLY check blockers from previous ticks. New blockers added this tick (in strat_up)
        # are trusted to be accurate results of current-tick enforcement (e.g. Blacksmith).
        for b_id, b in entity.strategic.blockers.items():
            if b_id in removals or b.resolved: continue

            # 1. Material Resolution
            if b.kind == "material" and has_item(pending_inventory, b.subject, b.target_quantity):
                resolved_ids.add(b_id)

            # 2. Access Resolution (RPG-STRAT-011)
            elif b.kind == "access" and b.subject.startswith("("):
                try:
                    coords = ast.literal_eval(b.subject)
                    if isinstance(coords, tuple) and len(coords) == 2:
                        dx = entity.navigation.position[0] - coords[0]
                        dy = entity.navigation.position[1] - coords[1]
                        dist = (dx*dx + dy*dy)**0.5
                        if dist < 0.5:
                            resolved_ids.add(b_id)
                except:
                    pass

            # 3. Inventory Resolution
            elif b.kind == "inventory" and b.subject == "capacity":
                if len(pending_inventory.items) < pending_inventory.max_slots:
                    resolved_ids.add(b_id)

        # 2. Check for newly resolved blockers (explicitly marked as resolved)
        for blocker in strat_up.blockers_add_or_update:
            if blocker.resolved:
                resolved_ids.add(blocker.id)

        # 3. Objective Resolution (RPG-STRAT-009 Fix)
        # If a blocker was resolved, check if the active objective is also resolved
        current_proj_id = strat_up.current_project_id_set if strat_up.current_project_id_set is not None else entity.strategic.current_project_id
        project_upd = None
        if current_proj_id:
            project = entity.strategic.projects.get(current_proj_id)
            if project and project.status == ProjectStatus.ACTIVE:
                obj_id = strat_up.current_objective_id_set if strat_up.current_objective_id_set is not None else project.active_objective_id
                active_obj = next((o for o in project.objectives if o.id == obj_id), None)
                if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:
                    # Check if all blockers for this objective are resolved
                    all_blockers_resolved = True
                    for b_id in active_obj.blocker_ids:
                        if b_id not in entity.strategic.blockers and b_id not in [b.id for b in strat_up.blockers_add_or_update]:
                             # This blocker was never there or already removed?
                             continue

                        is_now_resolved = (b_id in resolved_ids)
                        if not is_now_resolved:
                             b_obj = entity.strategic.blockers.get(b_id)
                             if b_obj and not b_obj.resolved:
                                  all_blockers_resolved = False
                                  break

                    # Special case: Crafting/Collecting objectives (Material-based)
                    is_material_obj = active_obj.kind in ("craft", "collect")
                    if is_material_obj:
                         if has_item(pending_inventory, active_obj.target, 1):
                              all_blockers_resolved = True

                    if all_blockers_resolved:
                        # Resolve Objective and Complete Project
                        new_obj = replace(active_obj, status=ObjectiveStatus.RESOLVED)
                        new_project = replace(project, objectives=[new_obj if o.id == new_obj.id else o for o in project.objectives], status=ProjectStatus.COMPLETED)
                        project_upd = new_project

        if not resolved_ids and not project_upd:
            continue

        # RPG-STRAT-011: Mark resolved blockers in the update for test observability
        new_additions = list(strat_up.blockers_add_or_update)
        for b_id in resolved_ids:
            # 1. Update if already in additions
            found_in_upd = False
            for i, b in enumerate(new_additions):
                if b.id == b_id:
                    new_additions[i] = replace(b, resolved=True)
                    found_in_upd = True
                    break

            # 2. Add if it was only in state
            if not found_in_upd:
                b_obj = entity.strategic.blockers.get(b_id)
                if b_obj:
                    new_additions.append(replace(b_obj, resolved=True))

        new_removals = list(
            set(strat_up.blockers_remove) | resolved_ids
        )

        new_projects = list(strat_up.projects_add_or_update)
        if project_upd:
            new_projects.append(project_upd)

        final_identity_upd = ent_upd.identity
        if project_upd and project_upd.status == ProjectStatus.COMPLETED:
            # Milestone 3 Law: Complete means stop trying [INTEG-FIX]
            final_identity_upd = (final_identity_upd or IdentityUpdate()).merge(IdentityUpdate(craft_target=""))

        refined_entity_updates[e_id] = replace(
            ent_upd,
            identity=final_identity_upd,
            strategic=replace(
                strat_up,
                blockers_add_or_update=new_additions,
                blockers_remove=new_removals,
                projects_add_or_update=new_projects,
                current_project_id_set="" if project_upd else strat_up.current_project_id_set,
                current_objective_id_set="" if project_upd else strat_up.current_objective_id_set
            ),
        )

    metric_counters = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
    metric_counters["strategic_candidates"] = len(candidate_ids)
    return replace(update, entity_updates=refined_entity_updates, metric_counters=metric_counters)


def giveup_project_end_update(entity: EntityState, staged: StrategicUpdate, experience: NavigationExperienceUpdate, tick: int, limit: int) -> Optional[StrategicUpdate]:
    """The project end of the give-up consume step (design section 8; divergence 2.220): when an experience the pass files has ``project_giveups`` at ``limit`` (``access_giveup_limit``), the number of give-ups of one
    place for one purpose within the project CURRENT at this pass, that project ends, typed `DESTINATION_GIVEN_UP`, with its current project and objective cleared in the same update. Nothing ends when the subject has no
    current project, or when its project already ended. Files NO ACCESS blocker: the memory of the place is the experience. Reads only; None when nothing ends."""
    project_id = staged.current_project_id_set if staged.current_project_id_set is not None else entity.strategic.current_project_id
    if not project_id or not any(r.project_giveups >= limit for r in experience.upserts):
        return None
    project = next((p for p in reversed(staged.projects_add_or_update) if p.id == project_id), None) or entity.strategic.projects.get(project_id)
    if project is None or project.ended_by is not None:
        return None
    return StrategicUpdate(
        projects_add_or_update=[end_record(project, ProjectStatus.ABANDONED, ProjectEnd.DESTINATION_GIVEN_UP, tick)],
        current_project_id_set="",
        current_objective_id_set="",
    )


def consume_giveup_records(entity: EntityState, staged: StrategicUpdate, ent_upd: Optional[EntityUpdate], tick: int) -> Tuple[StrategicUpdate, EntityUpdate]:
    """The give-up consume step of one strategic pass (F2, divergence 2.220): ``staged`` with the typed project end of `giveup_project_end_update` folded in, and ``ent_upd`` carrying the
    typed clear of the records, so none outlives a pass (also when no project is current). A subject holding no record is returned unchanged; the limit is read from the catalog only then.
    The #996 rework: the same step also computes the subject's navigation experience update (`navigation_experience_update`: reviews of due records, an upsert per pending give-up, evictions at the cap) and
    stages it on ``ent_upd``; it runs whenever the subject holds a pending record or an experience, so a due record is reviewed on any pass that serves the subject. It files NO ACCESS blocker: ``staged`` gets only
    the typed project end (`giveup_project_end_update`)."""
    cur = ent_upd if ent_upd is not None else EntityUpdate(entity_id=entity.id)
    nx = NavigationExperienceUpdate()
    if entity.navigation.giveup_records or entity.cognition.memory.navigation.records:
        project_id = (staged.current_project_id_set if staged.current_project_id_set is not None else entity.strategic.current_project_id) or ""
        nx = navigation_experience_update(entity, tick, project_id, navigation_experience_settings())
        if not nx.is_noop():
            cur = replace(cur, navigation_experience=cur.navigation_experience.merge(nx) if cur.navigation_experience is not None else nx)
    if not entity.navigation.giveup_records:
        return staged, cur
    held = entity.navigation.target
    if held is not None and any(near_anchor(held, r.anchor) for r in entity.navigation.giveup_records):
        HeldTargetAtAnchorCounts.note()  # v2.1c: report only, never cleared here: only a writer that skips `destination_suppressed` can hold a target at the anchor
    filed = giveup_project_end_update(entity, staged, nx, tick, access_giveup_limit())
    clear = NavigationUpdate(giveup_records_clear=True)
    return (staged if filed is None else staged.merge(filed)), replace(cur, navigation=(cur.navigation or NavigationUpdate()).merge(clear))

