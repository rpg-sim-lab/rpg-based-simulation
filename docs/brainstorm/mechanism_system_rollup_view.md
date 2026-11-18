# Mechanism System Rollup View

Generated from `registries/mechanisms.yaml` + `registries/system_registry.jsonl` — regenerate with `make mechanism-system-rollup-view`. Do not hand-edit.

**What features the simulation actually has, and which are loose versus deep, without reading all 93 mechanisms individually** — declared system membership (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`), never derived from `depends_on` or any other edge.

**Counts only, never a single summary status.** A badge reading "combat: partial" would conceal that most members are unverified — the verification axis exists so that unverified renders visibly rather than being summarised away; a badge here would rebuild that failure one tier higher.

**Every rate is shown against the whole-registry baseline, never in isolation** — a raw per-system percentage looked informative in this program's own value investigation until checked against baseline and found statistically indistinguishable from it. The baseline below is computed live from the current registry, not a fixed snapshot.

**Reading caution — a system standing out from baseline may reflect recent attention, not a property of the simulation.** A system this session (or any prior one) spent a week investigating will show a higher bound/verified rate for that reason alone — the view describes where work has concentrated, not an independent discovery that some systems are inherently deeper than others. Read a high rate as "recently worked on," not as "this system is more real."

**"Bound, Unverified" is this view's most actionable column.** It splits `unverified` into two problems with different costs that the per-mechanism view doesn't separate: *bound-but-unverified* (a real `implemented_by` binding exists — the expensive part, locating the code, is already done, so this is the cheapest verification target available) versus *unbound-and-unverified* (`unverified` minus this column — we don't even know where to look yet, and investigation has to happen before verification can start).

**Baseline (all 113 mechanisms)**: 102 bound (90.3%), 105 verified (92.9% — 49 runtime, 56 static, 46.7% of verified is runtime), 8 unverified (0 of those bound-but-unverified). State breakdown: done 56, partial 21, gap 11, orphan 17, gated 8, skeleton 0.

**Runtime Share is a property of the verification method, not of coverage — track it separately.** `Verified` counts mechanisms confirmed by *any* instrument; `code_trace` (the code says it should work) and `scenario`/`corpus_run` (the simulation actually did it) are not interchangeable evidence, and a batch of code_trace-only re-confirmations can raise `Verified` while silently lowering `Runtime Share` — exactly what happened in `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` (batch 3 of the unbound-claims program), whose 20 new `code_trace` verifications moved the registry-wide runtime share from 27% to 46.7% while `Verified` itself grew. Neither number tells the whole story alone.

| System | Mechanisms | Bound (vs baseline) | Verified (vs baseline) | Runtime Share of Verified (vs baseline) | Bound, Unverified | done | partial | gap | orphan | gated | skeleton |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `cognition` | 24 | 23/24 (95.8%, +5.6pt vs baseline) | 24/24 (100.0%, +7.1pt vs baseline) [15 runtime, 9 static] | 15/24 (62.5%, +15.8pt vs baseline) | 0 | 11 | 0 | 1 | 7 | 5 | 0 |
| `combat` | 8 | 8/8 (100.0%, +9.7pt vs baseline) | 8/8 (100.0%, +7.1pt vs baseline) [4 runtime, 4 static] | 4/8 (50.0%, +3.3pt vs baseline) | 0 | 6 | 1 | 0 | 1 | 0 | 0 |
| `economy` | 13 | 12/13 (92.3%, +2.0pt vs baseline) | 12/13 (92.3%, -0.6pt vs baseline) [5 runtime, 7 static] | 5/12 (41.7%, -5.0pt vs baseline) | 0 | 7 | 3 | 1 | 2 | 0 | 0 |
| `faction` | 15 | 12/15 (80.0%, -10.3pt vs baseline) | 13/15 (86.7%, -6.3pt vs baseline) [4 runtime, 9 static] | 4/13 (30.8%, -15.9pt vs baseline) | 0 | 7 | 3 | 3 | 2 | 0 | 0 |
| `progression` | 15 | 15/15 (100.0%, +9.7pt vs baseline) | 15/15 (100.0%, +7.1pt vs baseline) [8 runtime, 7 static] | 8/15 (53.3%, +6.7pt vs baseline) | 0 | 8 | 6 | 0 | 0 | 1 | 0 |
| `social` | 12 | 9/12 (75.0%, -15.3pt vs baseline) | 9/12 (75.0%, -17.9pt vs baseline) [2 runtime, 7 static] | 2/9 (22.2%, -24.4pt vs baseline) | 0 | 5 | 3 | 3 | 1 | 0 | 0 |
| `world` | 40 | 35/40 (87.5%, -2.8pt vs baseline) | 37/40 (92.5%, -0.4pt vs baseline) [18 runtime, 19 static] | 18/37 (48.6%, +2.0pt vs baseline) | 0 | 21 | 6 | 5 | 6 | 2 | 0 |
| `unassigned` | 0 | 0/0 (n/a) | 0/0 (n/a) | 0/0 (n/a) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`unassigned` mechanism count is 0 — a mechanism with no declared system renders here explicitly rather than being silently dropped, same discipline as `mechanisms_by_system()`'s own `"unassigned"` key.
