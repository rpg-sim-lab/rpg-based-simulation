"""The one sum rule for the per-offerer rejection counts (apply and merge share it)."""
from __future__ import annotations

from typing import Dict, Mapping


def add_rejection_counts(base: Mapping[int, int], increment: Mapping[int, int]) -> Dict[int, int]:
    """Keep every count in `base` and add each `increment` entry to its key; `base` is not mutated.

    Logic ID: SOC-280 (TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME).
    """
    counts = dict(base)
    for key, value in increment.items():
        counts[key] = counts.get(key, 0) + value
    return counts
