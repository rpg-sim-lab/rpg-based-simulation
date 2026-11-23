"""The two consequence lines of the body's needs, ONE source (the #996 rework, architecture review of the item 2 shape): the hunger line at which a body is starving and the sleep-debt line at which it is exhausted.

They live here, in the foundation layer, so the strategy layer (`experience_due`) and the systems layer (the consume step) can read them without importing `src.engine`. `src.engine.starvation` takes
`STARVING_LINE` as the default of `StarvationTable.starving_line`, and `src.engine.need_pull` re-exports both under the same names, so every existing importer is unchanged. Plain constants: no I/O, no state."""

STARVING_LINE = 95.0   # hunger at which health starts to go
SLEEP_LINE = 98.0      # sleep debt at which the sleep-deprivation damage starts
