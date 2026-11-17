#!/usr/bin/env python3
"""Record a hand close's Review after the planner's PR review comment exists
(TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS, follow-up to TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW).

A hand close is recorded before its PR exists, so Review is folded in as `skipped`/`no_hand_tool`. Once the review comment
exists, this appends one Review `ok` event to the ticket's hand-close run, with a fresh `seq` and `supersedes` set to the
folded skip's seq. Nothing already written is rewritten; readers drop the replaced row
(`run_dedup.drop_superseded_events`), so Review counts as ran exactly once. The row lands in the current week's shard.

    python3 tools/agent-monitoring/record_review.py --ticket-id <TCK-ID> --review-ref <PR#>#<comment id>

Refuses, writing nothing: a malformed ref, a ticket with no hand-close run, a tier with no Review step (hotfix), a run whose
Review is already `ok`, a review comment that does not exist or belongs to another PR. If `gh` or the network is
unavailable the comment check prints a WARNING and the row is still written: a monitoring write never fails on it.
Standard tier; run by the domain planner, or by the implementer on the planner's word.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))
import record_events  # noqa: E402
from monitoring_batch_identifier import resolve_write_target  # noqa: E402
from path_record import full_phases  # noqa: E402
from run_dedup import dedupe_to_latest_per_execution  # noqa: E402
from session_role import stamp as stamp_session_role  # noqa: E402
from tools.agent_working_paths import AGENT_MONITORING  # noqa: E402
from tools.delivery.repo_name import current_repo  # noqa: E402
from validate import load_data_glob  # noqa: E402
from writer import write_line  # noqa: E402

REVIEW_REF = re.compile(r"^[1-9][0-9]*#[1-9][0-9]*$")


class Refused(Exception):
    """The record is not written; the message says why."""


def check_comment(pr: str, comment: str, runner=subprocess.run) -> str | None:
    """None when the comment exists on PR `pr`; a WARNING text when it could not be checked; raises Refused when it is
    missing or on another PR."""
    repo = current_repo(lambda cmd: runner(cmd, capture_output=True, text=True, timeout=30))
    try:
        done = runner(["gh", "api", f"repos/{repo}/issues/comments/{comment}", "--jq", ".issue_url"],
                      capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return f"could not run gh to check comment {comment} ({e}); writing without the check"
    if done.returncode != 0:
        err = (done.stderr or "").strip()
        if "404" in err or "Not Found" in err:
            raise Refused(f"comment {comment} does not exist in {repo}")
        return f"could not check comment {comment} ({err[:120] or 'gh failed'}); writing without the check"
    url = (done.stdout or "").strip()
    if not url.endswith(f"/{pr}"):
        raise Refused(f"comment {comment} belongs to {url or 'no issue'}, not PR #{pr}")
    return None


def build_event(ticket_id: str, ref: str, agent: str, runs: list[dict], events: list[dict], now: str) -> dict:
    if not REVIEW_REF.match(ref or ""):
        raise Refused(f"--review-ref must look like <PR number>#<comment id>, got {ref!r}")
    pr, comment = ref.split("#")
    hand = [r for r in runs if r.get("ticket_id") == ticket_id and r.get("workflow") == "implement-ticket"
            and r.get("execution_mode") == "hand"]
    if not hand:
        raise Refused(f"no hand-close run recorded for {ticket_id}")
    run = dedupe_to_latest_per_execution(hand)
    run = max(run, key=lambda r: r.get("end_ts") or "")
    try:
        planned = "Review" in full_phases(run.get("tier") or "")
    except Exception as e:  # noqa: BLE001 - an unreadable plan cannot show a Review step
        raise Refused(f"the tier plan could not be read ({e})") from e
    if not planned:
        raise Refused(f"the {run.get('tier')} plan has no Review step to record")
    mine = [e for e in events if e.get("run_id") == run.get("run_id") and e.get("execution_id") == run.get("execution_id")]
    reviews = [e for e in mine if e.get("phase") == "Review"]
    if any(e.get("status") == "ok" for e in reviews):
        raise Refused(f"{ticket_id} already has a Review recorded as ok")
    seq = max([e["seq"] for e in mine if isinstance(e.get("seq"), int)] or [0]) + 1
    skipped = [e for e in reviews if e.get("status") == "skipped" and isinstance(e.get("seq"), int)]
    event = {
        "run_id": run["run_id"], "execution_id": run["execution_id"], "provider": run.get("provider"),
        "ticket_id": ticket_id, "seq": seq, "phase": "Review", "agent": agent, "status": "ok",
        "summary": f"Review ran as the domain planner's PR review of PR #{pr} (comment {comment}), recorded after the review "
                   f"existed (record_review.py --review-ref {ref}); it replaces the folded skipped Review.",
        "ts": now,
    }
    if skipped:
        event["supersedes"] = skipped[-1]["seq"]
    if event["provider"] is None:
        event.pop("provider")
    errors = record_events.validate_record(event)
    if errors:
        raise Refused("; ".join(errors))
    return event


def main(argv: list[str] | None = None, data_root: Path | None = None, events_file: Path | None = None,
         runner=subprocess.run) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--review-ref", required=True, help="<PR number>#<comment id> of the planner's PR review comment")
    parser.add_argument("--agent", default="claude")
    args = parser.parse_args(argv)
    root = data_root or AGENT_MONITORING / "data"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        event = build_event(args.ticket_id, args.review_ref, args.agent, load_data_glob(root, "runs"),
                            load_data_glob(root, "events"), now)
        warning = check_comment(*args.review_ref.split("#"), runner=runner)
    except Refused as e:
        print(f"ERROR: {e}; nothing was written.", file=sys.stderr)
        return 1
    if warning:
        print(f"WARNING: {warning}.", file=sys.stderr)
    target = events_file or resolve_write_target("events", iso_week=datetime.now(timezone.utc).strftime("%G-W%V"))
    target.parent.mkdir(parents=True, exist_ok=True)
    if not write_line(target, json.dumps(stamp_session_role(event), separators=(",", ":"))):
        print("WARNING: event-record append failed.", file=sys.stderr)
        return 0
    print(f"DONE: recorded Review:ok for {args.ticket_id} (seq {event['seq']}"
          + (f", supersedes {event['supersedes']}" if "supersedes" in event else "") + ").")
    return 0


if __name__ == "__main__":
    sys.exit(main())
