"""The outcome record of one resource transfer intent, moved verbatim out of src/core/state.py (which re-exports it) for the module-length ceiling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class IntentResult:
    """The outcome of a specific resource transfer intent."""
    transaction_id: str | None
    accepted: bool
    reason: Any
    source_kind: str
    source_id: str | int
