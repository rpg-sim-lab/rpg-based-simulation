"""A count of priced services that named no payee (EXCH-02, TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN). OBSERVABILITY ONLY, never durable state.

The resolver debits nothing for a priced service or fee whose source is not a building and which names no treasury (`conservation.is_no_payee`), so the service goes ahead without
a charge. That is a modelling gap worth seeing, and the applied update no longer carries the resolved intents, so the engine counts each one at the point it commits it:

* written ONLY by `src.engine.economy.ResourceTransactionSystem._note_effects` (`note`);
* read and reset ONLY by `src.observability.run_ledger.RunLedger` (`counts`, `reset`), which carries it in the run ledger's closing tally;
* nothing in the simulation reads it, so the final state hash cannot depend on it (a test pins both the call sites and the hash).

It lives in `core` because both the engine and observability may import it (the layer contract allows engine -> core and observability -> core, not engine -> observability).
"""
from __future__ import annotations

from typing import Dict


class PayeeMissingCounts:
    """Class-level, non-durable counts keyed ``"<source_kind>|<transfer_kind>"``; reset at run start by the run ledger."""

    _counts: Dict[str, int] = {}

    @classmethod
    def note(cls, source_kind: str, transfer_kind: str) -> None:
        """Count one committed priced service that named no payee."""
        key = f"{source_kind}|{transfer_kind}"
        cls._counts[key] = cls._counts.get(key, 0) + 1

    @classmethod
    def counts(cls) -> Dict[str, int]:
        """A copy of the counts, keys sorted."""
        return dict(sorted(cls._counts.items()))

    @classmethod
    def reset(cls) -> None:
        """Clear the counts (run start, and test teardown)."""
        cls._counts = {}
