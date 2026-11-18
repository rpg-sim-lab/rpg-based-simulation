---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
artifact_type: investigation
tags: [skills, simulation-quality, testing]
---

# Source-backed research (P3)

Read-status key: READ = I read the source text this session. SNIPPET = seen only in a search summary, not read. MEMORY = known background, not re-fetched. Only READ rows carry quoted claims. Defect numbers refer to `defect_set.md`.

## Sources

| # | Source | Status |
|---|---|---|
| S1 | NASA-STD-7009B, Standard for Models and Simulations, approved 2024-03-05 (https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf). Sections 4.2.3-4.2.5, 4.3.6 read. | READ |
| S2 | Sargent, "Verification and Validation of Simulation Models", WSC 2005 (https://www.informs-sim.org/wsc05papers/014.pdf). Technique list and dynamic-testing paragraph read. | READ |
| S3 | Anthropic, "Skill authoring best practices" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). | READ (via fetch agent) |
| S4 | Hypothesis docs, "Stateful testing" (https://hypothesis.readthedocs.io/en/latest/stateful.html). | READ (via fetch agent) |
| S5 | Segura et al., "A Survey on Metamorphic Testing", IEEE TSE 42(9), 2016; Chen et al., "Metamorphic Testing: A Review of Challenges and Opportunities", ACM Computing Surveys 51(1), 2018. | SNIPPET (bibliographic facts and the oracle-problem framing only) |
| S6 | Grimm, Railsback et al., ODD protocol and its 2020 second update (JASSS). | SNIPPET |
| S7 | Claessen and Hughes, QuickCheck, ICFP 2000 (origin of property-based testing). | MEMORY |
| S8 | In-repo: `docs/testing/test_taxonomy.md` §6-§9, `registries/mechanisms.yaml` header, `docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md`, skill-catalog epic investigation. | READ (excerpts) |

## What each source says that matters here

**S1 NASA-STD-7009B.** Verification is "testing with respect to model specification and design"; validation compares M&S responses to the represented system (4.2.3, 4.2.5). Requirements MS15-MS18 require M&S to be verified and validated and a record of the domain of verification and of validation to be kept. Verification splits into implementation (code) verification: "contains everything in the M&S Design (and nothing more)" and solution verification. It recommends recording "aspects of M&S not verified" (4.2.4d). Results are assessed per six factors, among them input pedigree, uncertainty characterization and results robustness (4.3.6.1), and the Standard "levies no requirements with respect to what levels to achieve... merely that the levels be determined and reported." I did not read Appendix E or the capability-assessment factors.

**S2 Sargent.** Gives a technique list used "either subjectively or objectively", with combinations normal, for submodels and the whole model. Those relevant here: Degenerate Tests (does behaviour degenerate as inputs/parameters move, such as a queue that grows forever when arrivals exceed service), Extreme Condition Tests (plausible output for extreme factor combinations), Event Validity, Traces (follow specific entity types through the model), Comparison to Other Models, and Internal consistency checks. For program verification he lists dynamic testing by "traces, investigations of input-output relations... internal consistency checks, and reprogramming critical components."

**S3 Anthropic.** Evaluate before writing: run Claude on representative tasks without the skill, build at least three scenarios, measure the baseline, write minimal instructions, iterate against the baseline. "There is not currently a built-in way to run these evaluations." Descriptions drive selection among possibly 100+ skills and must say what and when. Keep SKILL.md under 500 lines, references one level deep, only add context Claude lacks, match freedom to fragility (low freedom for fragile operations), test with every model you will use.

**S4 Hypothesis.** `RuleBasedStateMachine` generates sequences of rules; `@invariant` runs after every step; `@precondition` filters inapplicable rules; on failure it prints a short reproducing program. Stated limits: preconditions and invariants cannot read bundles; strategies cannot see machine state except via `runner()`/`data()`; many `assume()` calls starve rule selection. The page says nothing on seeded or deterministic targets.

## Which methods apply to this project

| Method | Applies? | Why (project evidence) | Reusable form |
|---|---|---|---|
| Verification vs validation split and "record what is not verified" (S1, S2) | Yes, partly in place | The mechanism registry `verified` axis already separates static from runtime evidence; the missing part is the "aspects not verified" record for a change | Add a not-verified line to the test plan template; no new skill |
| Dynamic traces / internal consistency checks (S2) | Yes | Defects 2, 3, 4, 5 appeared in run traces; the first-sign column shows traces already work, but late | Trace checklist inside the lifecycle and interaction checks |
| Degenerate and extreme-condition tests (S2) | Yes | Defect 5 (state with no exit fills a cap), defect 6 (case cannot occur in the window) are degeneracy/extreme cases | Checklist items: "does any state or count grow without bound?", "can the case occur inside the window?" |
| Stateful property tests (S4, S7) | Yes, strongest fit | Defects 2, 4, 5 and the latch were missed because tests ran one pass or one transition. A rule machine over "two passes in a row", "every non-terminal state eventually exits", "value after a successful step" targets exactly that. `hypothesis` is declared in `pyproject.toml` but 0 test files import it | Pilot in one lifecycle area, owned by the test-architecture track; technique already sanctioned by `test_taxonomy.md` §6 |
| Metamorphic testing (S5) | Partly | Addresses the oracle problem, but `test_taxonomy.md` §6 gates it on replay reliability and long-run determinism is parked | Do not propose now; revisit when the parked determinism work reopens |
| NASA credibility scoring with levels (S1) | Partly / not | The score-and-report-levels machinery is aimed at decision-critical M&S; the project's `verified` axis and SimQ already report evidence. Reusing the idea (explicit domain of verification) costs little; adopting the scale does not pay | Borrow the "domain of verification" notion in the test plan only |
| ODD protocol (S6) | Not as a skill | It is a model-description format; the Bible and world_rules are the project's description. Adopting it would duplicate those documents | None |
| Face validity / Turing tests (S2) | Already done by the owner | Designer reviews are the project's face-validity step (defects 1, 4, 6 were found that way) | Make the review prompts explicit (see proposal) |
| Event validity, predictive validation (S2) | Not now | Needs a real-system reference; the project has no real system, only Rule IDs and design intent | None |
| Evaluation-first authoring (S3) | Yes, binding on this work | Dictates the eval plan and the "no skill without a baseline gain" rule | Eval plan in proposal |

## Implications carried into P4
1. The strongest evidence points at one class, lifecycle of durable records (5 of 10 defects, by my count), and a second smaller class, time and scale (2 of 10). The four candidate areas in the request are not equally supported; interaction review has 2, measurement design 1.
2. Methods that apply already live partly in repo docs (`test_taxonomy.md`, mechanism registry). The gap is operationalisation at review time, not knowledge.
3. S3 plus the catalog epic finding (domain skills almost never invoked; only binding gates work) means delivery form decides outcomes: a skill that agents must remember to call is the weakest option.
