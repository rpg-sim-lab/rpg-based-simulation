---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS

Read on origin/main 5e58ae857.

## How a row is matched today
- `Row.key` and `Finding.key` are `(file, symbol, tool, rule)` (`codebase/health/registry.py` `Row.key`; `findings.py` `Key`).
- `ratchet.compare` matches findings to rows by exact key only:
  - a finding with no row → `new` (fails `blocking_failed` unless the tool is report-only);
  - a row with no finding → `gone` (never fails).
- So a definition moved to another file is one `new` and one `gone` with the same `(symbol, tool, rule)`.
- The `findings.py` module docstring records this as accepted: "A function renamed, or moved to another file, surfaces as new ... the old row then shows as 'gone' and can be deleted."

## What a symbol looks like, per tool
- ruff, complexipy and line_count function and class rows use `Class.method` or a function name. File-level ruff rules (D100, I001, ...) and line_count `module-length` use `None`.
- ast_grep uses the innermost def or class, or `<module>`.
- jscpd uses `"dup:" + higher_path` with the lower path as `file`. It names a file pair, not a definition, so a "same symbol" match is meaningless.

## Pairing rule
Pair only non-`None` symbols, skip `<module>` and jscpd, require a different file, and require `value <= row.ceiling`. A file-level row moving is not a definition move; it stays new plus gone. Ambiguity is real: `__init__`, `run` and `apply` recur across files. That's why pairing is a label only, and `move` acts only on files the caller names.

## Existing commands to mirror
- `delete` (`_cmd_delete`, `registry.delete_row`) is the shape for a targeted row edit: load with `check_files=False`, edit, `write_rows`.
- `tighten` takes `--from DIR` and never skips a tool (`_findings` with no skippable set). `move` should do the same, so a "not measured" tool cannot look movable.
- `write_rows` sorts rows (`_sort_key`), so a re-keyed row lands in its new file's place and the diff is one line removed, one line added.

## Where the report goes
- `format_report` is the plain-text `check` output.
- `format_summary` is the Markdown job summary that CI's `code-health` job appends (`--summary-out`), so the label has to appear in both.

## Risks
- **Loosening:** none, as long as the exit code and the new/worse sets are untouched and `move` refuses over-ceiling values.
- **Baseline edits:** `move` writes the real registry only when someone runs it. The tests must use the `seeded` tmp fixture in `tests/codebase/test_code_health_ratchet_registry.py`, never the repo file.
