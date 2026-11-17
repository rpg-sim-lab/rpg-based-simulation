"""Merge of the group fields of StateUpdate.merge_many (kept out of updates.py)."""
from __future__ import annotations

from typing import Any, Dict, Iterable


def merge_group_fields(first: Any, others: Iterable[Any]) -> Dict[str, Any]:
    """Merge groups_add_or_update, groups_add, next_group_id_set and groups_remove of `first` and `others`, in order.

    New records (groups_add) are concatenated, never merged by id, so a duplicate id reaches apply and is rejected there. The counter takes the
    larger value. Removals are a set, listed the way StateUpdate.merge_many always listed them.
    """
    add_or_update = list(first.groups_add_or_update)
    add = list(first.groups_add)
    counter = first.next_group_id_set
    remove = set(first.groups_remove)
    for other in others:
        add_or_update.extend(other.groups_add_or_update)
        add.extend(other.groups_add)
        if other.next_group_id_set is not None:
            counter = other.next_group_id_set if counter is None else max(counter, other.next_group_id_set)
        remove.update(other.groups_remove)
    return {"groups_add_or_update": add_or_update, "groups_add": add, "next_group_id_set": counter, "groups_remove": list(remove)}
