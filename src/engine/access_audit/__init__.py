"""Stage 1 of the next-generation engine plan: an observe-only access audit of the Resolution steps (TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT).

Off by default (flag ``ENABLE_ACCESS_AUDIT``). When off, nothing in this package runs. When on, a recorder the caller supplies observes each step the pipeline dispatches
and writes nothing into state or the update."""
