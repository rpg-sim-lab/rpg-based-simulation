---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS

1. **`codebase/health/ratchet.py`**
   - Add a frozen `LikelyMove(row: Row, finding: Finding, ambiguous: bool)`.
   - Add a pure `likely_moves(result: RatchetResult) -> tuple[LikelyMove, ...]` using the pairing rule in investigation.md. Make it a separate function, not a `compare` field, so `compare`'s result and callers stay unchanged.
   - Sort the output deterministically, by old file, then symbol, then new file.
2. **Report**
   - `format_report(result, limit, moves=())` gains a "likely move (still a failure; run the command to re-key)" section. One line per pair:
     `  old → new symbol [tool rule] value=V ceiling=C  →  python3 -m codebase.health move OLD NEW --symbol S`
     Add an `(ambiguous)` tag where it applies.
   - `format_summary` gets the same block.
   - `_cmd_check` computes the moves and passes them in. The exit code logic is untouched.
3. **`codebase/health/registry.py`**
   - Add a pure `move_rows(rows, findings, old_file, new_file, symbol=None) -> tuple[list[Row], list[str]]`. It returns the new rows and a change list, and raises `MoveRefused(reason)` for each refusal in the ticket's Scope 3.
   - It uses `dataclasses.replace(row, file=new_file)` only.
4. **`codebase/health/__main__.py`**
   - Add a `move` subparser: `old_file`, `new_file`, `--symbol`, `--from`.
   - `_cmd_move` loads rows with `check_files=False` and gets findings with no skippable tools (like `tighten`). On `MoveRefused`, print to stderr and exit 2, writing nothing. Otherwise write the rows and print the changes and the count.
   - Update the usage docstring.
5. **Docs**
   - In the `findings.py` docstring, replace the move sentence: a move is still new plus gone; `check` names the pair; `move` re-keys it.
   - Add one sentence to roadmap §6.3.
6. **Gates last, on the committed tree:**
   - `tests/codebase/`;
   - `make code-health`;
   - ruff, mypy and pyrefly over `codebase/health/` (no new finding);
   - the baseline must be byte-identical to the base.

Scope guard: no `src/` change, no baseline row change, and no change to `compare`, `blocking_failed` or the exit codes.

## AC map
| AC | Step |
|---|---|
| fixture move fails, then passes after `move` | 1, 2, 4 |
| refusals write nothing | 3, 4 |
| no `None`, `<module>` or jscpd pair; ambiguous lists all | 1 |
| summary shows pairs | 2 |
| gates, baseline untouched | 6 |
