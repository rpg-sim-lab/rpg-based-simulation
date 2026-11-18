"""Lint a PR body for an attribution trailer (TCK-20261006-PR-BODY-ATTRIBUTION-TRAILER-NOT-CHECKED) and for the
required durable-state line in `## Verification` (TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES).

Repo law (`docs/guides/delivery_process.md`, "PR Lifecycle" step 3): no attribution trailer in a PR body.
That means no "Generated with [Claude Code]" line, no `claude.ai/code/session_...` link and no
`Co-Authored-By:` line. Commit-message trailers are unaffected.

This is the one pattern list. `pr_render.check_against_live` imports `find_attribution` and the CI job
`.github/workflows/pr-body-lint.yml` runs this file as a script on `github.event.pull_request.body`.

The patterns are anchored on the real trailer shapes, so prose that only mentions the rule
("no Generated with line") is not a hit.

stdlib only: the CI job runs it without installing the project.
"""
import os
import re
import sys
from typing import List, Optional

# TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES: a template-shaped PR body
# (one with a `## Tickets` heading) must carry this line in its `## Verification` section, with a non-empty answer on the
# line itself (pr_render writes one such line per ticket). `pr_render.py` renders it (`N/A: no src change` when the diff touches no
# `src/`), so a PR rendered from the template never fails. Bodies without `## Tickets` (Dependabot, hand-written
# one-offs) are not template-shaped and are not checked.
LIFECYCLE_LINE = "- Durable state, lifecycle and clocks:"
_H2_RE = re.compile(r"^##\s", re.MULTILINE)
_TICKETS_H2_RE = re.compile(r"^## Tickets\s*$", re.MULTILINE)
_VERIFICATION_H2_RE = re.compile(r"^## Verification\s*$", re.MULTILINE)


def _verification_section(body: str) -> Optional[str]:
    start = _VERIFICATION_H2_RE.search(body)
    if start is None:
        return None
    rest = body[start.end():]
    nxt = _H2_RE.search(rest)
    return rest if nxt is None else rest[: nxt.start()]


def find_missing_lifecycle(body: Optional[str]) -> Optional[str]:
    """Return a reason when a template-shaped PR body lacks a non-empty lifecycle line in `## Verification`, else None."""
    text = body or ""
    if _TICKETS_H2_RE.search(text) is None:
        return None
    section = _verification_section(text)
    if section is None:
        return "no ## Verification section"
    found = [line for line in section.splitlines() if line.startswith(LIFECYCLE_LINE)]
    if not found:
        return f"no `{LIFECYCLE_LINE}` line"
    # The template placeholder (an HTML comment) is not an answer.
    if any(line[len(LIFECYCLE_LINE):].strip() and not line[len(LIFECYCLE_LINE):].strip().startswith("<!--") for line in found):
        return None
    return f"the `{LIFECYCLE_LINE}` line is empty"

# A trailer is its own line: the robot emoji and markdown punctuation may precede "Generated with", but prose that
# quotes the phrase mid-sentence is not one. The session link needs a real id character after `session_`
# (a literal `session_...` in prose does not match).
ATTRIBUTION_PATTERNS = (
    re.compile(r"^[\W_]*Generated with \[?Claude Code", re.IGNORECASE),
    re.compile(r"claude\.ai/code/session_[A-Za-z0-9]", re.IGNORECASE),
    re.compile(r"^\s*Co-Authored-By:", re.IGNORECASE),
    re.compile("^[\\W_]*\U0001F916\\s*Generated", re.IGNORECASE),
)


def find_attribution(body: Optional[str]) -> List[str]:
    """Return each body line (stripped) that matches an attribution pattern, in order, once each."""
    hits: List[str] = []
    for line in (body or "").splitlines():
        if any(pattern.search(line) for pattern in ATTRIBUTION_PATTERNS):
            hits.append(line.strip())
    return hits


def main(argv=None, environ=None) -> int:
    """Read the body from the `PR_BODY` environment variable (no shell interpolation of untrusted text)."""
    env = os.environ if environ is None else environ
    body = env.get("PR_BODY")
    hits = find_attribution(body)
    missing = find_missing_lifecycle(body)
    if not hits:
        print("PR body has no attribution trailer.")
    for line in hits:
        print(f"::error::attribution trailer in PR body: {line}")
    if hits:
        print("Remove it and PATCH the body again (docs/guides/delivery_process.md, PR Lifecycle step 3).")
    if missing:
        print(f"::error::PR body Verification section: {missing}. Re-render with tools/delivery/pr_render.py "
              "(it writes `N/A: no src change` when the diff touches no src/).")
    else:
        print("PR body Verification carries the durable-state line (or the body is not template-shaped).")
    return 1 if hits or missing else 0


if __name__ == "__main__":
    sys.exit(main())
