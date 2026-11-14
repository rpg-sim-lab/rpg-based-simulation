---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT
artifact_type: test_plan
tags: [ai, documentation, governance]
---

# Test Plan: TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT

## Tests (temp-repo git fixtures; `tests/tools/test_doc_drift.py`)
- Unverified, clean, changed, deleted, renamed (to a new directory), doc text edited, `verified_at`-only edit ignored, `evidence_paths` edit counts, uncommitted evidence, squash-merged history keeps its baseline, `git mv` keeps it through `--follow`, removing the line makes the doc unverified, shallow clone gives `baseline-unavailable`, the name-status diff has no pathspec, CLI prints the pin and exits 0, a bad ref prints a MARKER error and exits 0.
- `tests/tools/test_validate_frontmatter_evidence_fields.py`: shapes accepted and rejected, a missing file is valid, real frontmatter text parses.
- `tests/tools/test_week_close.py`: the summary never raises, names the pin, a failing report leaves the exit status alone, `--data-dir` prints no report.
- `tests/tools/test_finalize_doc_drift_wiring.py`: the Finalize block's place, `|| true`, log-only, paired backticks.
- Full `tests/tools/` and `tests/docs` in a lead slot before the push; paths-guard before any push.
