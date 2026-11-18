"""The blocker lifecycle of the strategic pass (divergence 2.214): a re-inference merges into the stored blocker, and a congestion blocker that stays quiet is removed."""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from src.core.state import EntityState
from src.core.strategic import (
    CONGESTION_BLOCKER_ID,
    BlockerRemoval,
    merge_inferred_blocker,
    quiet_blockers,
)
from src.core.updates import StrategicUpdate


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
