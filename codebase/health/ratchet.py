"""The ratchet: fail only on a violation that is new, or worse than its baseline row.

`compare` matches each current `Finding` to a registry `Row` by `(file, symbol, tool, rule)`
(never a line number; see `codebase/health/findings.py` for the key each tool produces):

- no row                         -> NEW      (fails)
- value above the row's ceiling  -> WORSE    (fails)
- value below the row's ceiling  -> IMPROVED (reported, never fails)
- row with no current finding    -> GONE     (reported, never fails)
- otherwise                      -> unchanged

The two non-failing outcomes are how paid-off debt shows up: `tighten` (or `delete`) in
`codebase.health.registry` then lowers or removes the row. Frozen historical debt and a live
regression are different lists in the report, which is what an earlier single-number ratchet in
this repo (TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION) could not say.

Blocking in CI (the `code-health` job in test.yml runs it on every PR; roadmap M4 flip,
TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING). Two sets below are the policy, in code rather than in flags:
`REPORT_ONLY_TOOLS` findings are listed but never fail `check`; `SKIPPABLE_TOOLS` may fail to run without failing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Iterable, Sequence

from codebase.health.findings import Finding
from codebase.health.registry import Row, movable_symbol

DEFAULT_REPORT_LIMIT = 25

# Tools whose new or worse findings are listed and labelled "report-only" but do not fail `check`
# (decision 8.16: jscpd stays report-only; ast-grep joined the blocking tools in
# TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING).
REPORT_ONLY_TOOLS = frozenset({"jscpd"})
# Tools that may fail to run without failing `check`: jscpd needs npx and the npm registry. A skipped tool is
# "not measured", never "gone". Deliberately its own set, never derived from REPORT_ONLY_TOOLS, so that a blocking
# tool can never become skippable by accident (ast_grep is a local binary and keeps exit 2). Must stay a subset of
# REPORT_ONLY_TOOLS.
SKIPPABLE_TOOLS = frozenset({"jscpd"})
REPORT_ONLY_LABEL = "(report-only)"


@dataclass(frozen=True)
class RatchetResult:
    """The outcome of comparing one scan with the registry."""

    new: tuple[Finding, ...] = ()
    worse: tuple[tuple[Finding, Row], ...] = ()
    improved: tuple[tuple[Finding, Row], ...] = ()
    gone: tuple[Row, ...] = ()
    unchanged: int = 0

    @property
    def failed(self) -> bool:
        """True if any violation is new or above its ceiling."""
        return bool(self.new or self.worse)

    @property
    def blocking_failed(self) -> bool:
        """True if a new or worse finding belongs to a tool that is not report-only; this is `check`'s exit 1."""
        return any(f.tool not in REPORT_ONLY_TOOLS for f in self.new) or any(
            f.tool not in REPORT_ONLY_TOOLS for f, _ in self.worse
        )

    @property
    def report_only(self) -> tuple[tuple[Finding, str], ...]:
        """The new or worse findings of report-only tools, each with what changed."""
        entries = [(f, f"NEW value={f.value}") for f in self.new if f.tool in REPORT_ONLY_TOOLS]
        entries += [(f, f"WORSE {f.value} > ceiling {row.ceiling}") for f, row in self.worse if f.tool in REPORT_ONLY_TOOLS]
        return tuple(entries)


@dataclass(frozen=True)
class LikelyMove:
    """A gone row and a new finding that look like one definition moved to another file.

    A label only: the pair never changes `RatchetResult`, so `check` still fails the new finding. `ambiguous` is true
    when the row has more than one candidate finding, or the finding more than one candidate row.
    """

    row: Row
    finding: Finding
    ambiguous: bool

    @property
    def command(self) -> str:
        """The `move` command that re-keys this row, naming the symbol so nothing else of the file moves."""
        return f"python3 -m codebase.health move {self.row.file} {self.finding.file} --symbol {self.row.symbol}"


def likely_moves(result: RatchetResult) -> tuple[LikelyMove, ...]:
    """Pair each gone row with each new finding of the same (symbol, tool, rule) in another file, at or under its ceiling.

    Only a named definition can have moved: a file-level row (symbol `None`), ast-grep's `<module>` and a jscpd file pair
    are never paired, and a finding above the row's ceiling is not a move. Sorted by old file, symbol, then new file.
    """
    by_identity: dict[tuple, list[Finding]] = {}
    for finding in result.new:
        if movable_symbol(finding.symbol, finding.tool):
            by_identity.setdefault((finding.symbol, finding.tool, finding.rule), []).append(finding)
    pairs = [
        (row, finding)
        for row in result.gone
        if movable_symbol(row.symbol, row.tool)
        for finding in by_identity.get((row.symbol, row.tool, row.rule), ())
        if finding.file != row.file and finding.value <= row.ceiling
    ]
    rows_per_finding = {pair[1].key: 0 for pair in pairs}
    findings_per_row = {pair[0].key: 0 for pair in pairs}
    for row, finding in pairs:
        rows_per_finding[finding.key] += 1
        findings_per_row[row.key] += 1
    moves = [
        LikelyMove(row, finding, findings_per_row[row.key] > 1 or rows_per_finding[finding.key] > 1)
        for row, finding in pairs
    ]
    return tuple(sorted(moves, key=lambda m: (m.row.file, m.row.symbol or "", m.finding.file)))


def compare(findings: Iterable[Finding], rows: Sequence[Row]) -> RatchetResult:
    """Compare a scan with the registry. Both are matched by key, so line moves never matter."""
    baseline = {row.key: row for row in rows}
    seen: set[tuple] = set()
    new: list[Finding] = []
    worse: list[tuple[Finding, Row]] = []
    improved: list[tuple[Finding, Row]] = []
    unchanged = 0
    for finding in findings:
        seen.add(finding.key)
        row = baseline.get(finding.key)
        if row is None:
            new.append(finding)
        elif finding.value > row.ceiling:
            worse.append((finding, row))
        elif finding.value < row.ceiling:
            improved.append((finding, row))
        else:
            unchanged += 1
    gone = [row for row in rows if row.key not in seen]
    return RatchetResult(tuple(new), tuple(worse), tuple(improved), tuple(gone), unchanged)


def _tag(finding: Finding) -> str:
    return f" {REPORT_ONLY_LABEL}" if finding.tool in REPORT_ONLY_TOOLS else ""


def _where(finding: Finding) -> str:
    place = f"{finding.file}:{finding.line}" if finding.line else finding.file
    return f"{place} {finding.symbol}" if finding.symbol else place


def _section(title: str, lines: list[str], limit: int) -> list[str]:
    if not lines:
        return []
    shown = lines[:limit]
    more = [f"  ... and {len(lines) - limit} more"] if len(lines) > limit else []
    return [f"{title} ({len(lines)}):", *shown, *more]


def _move_line(move: LikelyMove) -> str:
    tag = " (ambiguous: other candidates listed)" if move.ambiguous else ""
    return (
        f"  {move.row.file} -> {move.finding.file} {move.row.symbol} [{move.row.tool} {move.row.rule}] "
        f"value={move.finding.value} ceiling={move.row.ceiling}{tag}\n    {move.command}"
    )


MOVE_TITLE = "likely move (still a failure above; if the code moved unchanged, the command re-keys the row)"


def format_report(result: RatchetResult, limit: int = DEFAULT_REPORT_LIMIT, moves: Sequence[LikelyMove] = ()) -> str:
    """A plain-text report: failures first, then the non-failing changes, then a one-line verdict."""
    lines: list[str] = []
    lines += _section(
        "NEW violations (no baseline row)",
        [f"  {_where(f)} [{f.tool} {f.rule}] value={f.value}{_tag(f)}" for f in result.new],
        limit,
    )
    lines += _section(
        "WORSE than baseline",
        [f"  {_where(f)} [{f.tool} {f.rule}] {f.value} > ceiling {r.ceiling}{_tag(f)}" for f, r in result.worse],
        limit,
    )
    lines += _section(MOVE_TITLE, [_move_line(m) for m in moves], limit)
    lines += _section(
        "improved (not a failure; run `tighten` to lower the ceiling)",
        [f"  {_where(f)} [{f.tool} {f.rule}] {f.value} < ceiling {r.ceiling}" for f, r in result.improved],
        limit,
    )
    lines += _section(
        "gone (not a failure; run `tighten` or `delete` to remove the row)",
        [f"  {r.file} {r.symbol or ''} [{r.tool} {r.rule}]" for r in result.gone],
        limit,
    )
    verdict = "FAIL" if result.blocking_failed else "OK"
    note = f" ({len(result.report_only)} report-only)" if result.report_only else ""
    lines.append(
        f"{verdict}: {len(result.new)} new, {len(result.worse)} worse, {len(result.improved)} improved, "
        f"{len(result.gone)} gone, {result.unchanged} unchanged{note}"
    )
    return "\n".join(lines)


def skipped_note(skipped: Collection[str]) -> str:
    """The one-line note for tools that could not run: they were not measured, which is not the same as clean."""
    return "; ".join(f"{name} could not run {REPORT_ONLY_LABEL}; its findings were not measured" for name in sorted(skipped))


def format_summary(
    result: RatchetResult,
    changed_files: Collection[str] = (),
    limit: int = DEFAULT_REPORT_LIMIT,
    skipped: Collection[str] = (),
    moves: Sequence[LikelyMove] = (),
) -> str:
    """A Markdown job summary: one line on a pass; on a failure, violations in changed files come first.

    `changed_files` are repository-relative paths (for example the PR's `git diff --name-only`). A
    violation counts as "in a changed file" when its `file` is in that set; the lists are capped at
    `limit` each so a large baseline drift cannot flood the summary. Report-only findings and tools that
    could not run get their own lines and never change the verdict.
    """
    counts = f"{len(result.improved)} improved, {len(result.gone)} gone, {result.unchanged} unchanged"
    entries = [(f, f"NEW value={f.value}") for f in result.new if f.tool not in REPORT_ONLY_TOOLS]
    entries += [(f, f"WORSE {f.value} > ceiling {row.ceiling}") for f, row in result.worse if f.tool not in REPORT_ONLY_TOOLS]
    changed = set(changed_files)
    mine = [e for e in entries if e[0].file in changed]
    other = [e for e in entries if e[0].file not in changed]

    def block(title: str, items: list[tuple[Finding, str]]) -> list[str]:
        lines = [f"- `{_where(f)}` [{f.tool} {f.rule}] {what}" for f, what in items]
        return _section(title, lines, limit)

    if entries:
        out = [f"**Code health:** {len(entries)} new or worse blocking violations ({counts}).", ""]
        out += block("In files this PR changed", mine) + ([""] if mine and other else [])
        out += block("Elsewhere (baseline drift or other merged changes)", other)
    else:
        out = [f"**Code health:** OK, no new or worse blocking violations ({counts})."]
    if moves:
        out += ["", *_section(MOVE_TITLE, [f"- `{m.row.file}` -> `{m.finding.file}` {m.row.symbol} [{m.row.tool} {m.row.rule}]"
                                           f"{' (ambiguous)' if m.ambiguous else ''}: `{m.command}`" for m in moves], limit)]
    if result.report_only:
        out += ["", *block(f"Report-only findings {REPORT_ONLY_LABEL}, they do not fail the PR", list(result.report_only))]
    if skipped:
        out += ["", f"**{skipped_note(skipped)}**"]
    return "\n".join(out)
