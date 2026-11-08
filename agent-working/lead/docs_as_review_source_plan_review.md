# External AI Review — Documentation as a Trusted Review Source

**Review type:** Independent architecture and process review  
**Reviewer:** External AI Reviewer (ChatGPT)  
**Date:** 2026-11-07  
**Document reviewed:** `docs_as_review_source_plan.md`  
**Recommendation:** **Approve with targeted revisions before implementation**

---

## 1. Reviewer Position and Scope

I am an **external AI reviewer**, not an agent operating inside this repository.

I do not have direct access to the current repository state, implementation, complete documentation tree, CI execution results, or historical agent sessions.

This review is based on:

- The supplied `docs_as_review_source_plan.md`.
- The architecture, mechanisms, findings, and workflow details reported in that document.
- General software architecture, verification, documentation governance, and AI-assisted engineering principles.

**Important limitations:**

1. Repository-specific facts are treated as reported evidence, not independently verified facts.
2. I cannot confirm that the referenced files, line numbers, commits, tests, or workflows match the current repository.
3. Recommendations should be evaluated against existing repository mechanisms before implementation.
4. The local lead-planner and owning agents should retain authority over implementation details and scope.
5. I am reviewing the proposed architecture and governance model, not certifying the correctness of the current codebase.

Where a recommendation requires information not present in the plan, I will explicitly identify it as a question for local investigation.

### Overall assessment

The proposal addresses a real scalability problem in an AI-first SDLC: repeated repository exploration consumes substantial context and computation while producing inconsistent interpretations of system behavior.

The reported consumption of approximately 1.1 million agent tokens, repeated review of the same components, stale documentation, and inconsistent codebase measurements demonstrates a need for a more reliable knowledge-management approach.

The proposed direction is sound.

However, the plan should strengthen its distinction between:

- Document freshness.
- Document correctness.
- Verified implementation behavior.
- Intended system behavior.
- Evidence quality.
- Review scope and confidence.

The central recommendation is to adopt a **documentation-first, evidence-backed, risk-triggered verification model**.

Documentation should become the primary interface for understanding and reviewing the system, while source code and executable evidence remain the ultimate means of validating implementation behavior.

---

## 2. What the Existing Proposal Gets Right

### 2.1 Extend existing mechanisms rather than introduce parallel infrastructure

The plan correctly identifies several existing capabilities:

- `Document-Update` phase.
- `doc-updater` subagent.
- `doc-staleness` gate.
- `check_docs_to_update_coverage`.
- Mechanism registry and changed-code checks.
- Documentation registry.
- Existing fact-parity tests.
- Parity ledger.
- Architecture Decision Records.
- Known limitations and intentional divergences.

The proposal's decision to extend these mechanisms is strongly supported.

**Recommendation: Preserve this decision.**

Do not introduce another documentation-maintenance agent, another review phase, a separate fact database, or a complex knowledge graph unless the current mechanisms are demonstrably insufficient.

The most valuable improvement is likely to be making existing workflow phases more complete and reliable.

### 2.2 The satellite-documentation problem is correctly identified

The existing document-update process appears to rely too heavily on the list generated during Investigate.

If Investigate identifies the canonical contract but misses architectural explanations, secondary documents, or diagrams describing the same behavior, the documentation-update phase cannot reliably maintain consistency.

The proposed F1–F3 changes directly address this problem.

I support:

- Searching for additional documentation references during Investigate.
- Allowing doc-updater to discover secondary references.
- Recording explicitly skipped documents and reasons.
- Reporting potential documentation drift.
- Keeping broad text-search results advisory initially.

This is a proportionate improvement.

### 2.3 Canonical documentation is essential

P4 is one of the strongest parts of the proposal.

Repeated statements of the same architectural fact across numerous documents create avoidable maintenance complexity.

A single authoritative definition, referenced by other documents, greatly reduces the number of places that must change when behavior evolves.

However, I recommend refining the rule from:

> One canonical document per topic.

To:

> One canonical source for each normative fact, behavior contract, or architectural decision.

A large subsystem may legitimately have multiple canonical documents covering distinct concerns.

The important requirement is that the same authoritative statement should not be maintained independently in several places.

### 2.4 Generated facts are preferable to manually maintained statistics

P2 is appropriate.

Repository statistics, artifact counts, test counts, and similar measurable information should be generated from a pinned source revision whenever practical.

This eliminates unnecessary manual recounting and avoids presenting incompatible measurements from different checkouts.

Preserve the distinction between:

- Generated factual measurements.
- Human-maintained explanations.
- Historical records.
- Estimates or approximate metrics.

Generated outputs should record the source revision and measurement rules.

### 2.5 Avoid regenerating documentation directly from implementation

The proposal correctly rejects regenerating documentation from code after every modification.

That approach risks converting existing implementation defects into apparently authoritative documentation.

For example, if implementation incorrectly acknowledges a message after a failed dead-letter write, documentation must not automatically redefine that behavior as the intended contract.

This distinction becomes even more important in AI-first development, where the same agent may implement code, update tests, and produce documentation.

Agreement between those artifacts does not necessarily establish correctness.

---

## 3. Critical Issue: Document Freshness Is Not Document Correctness

**Priority: High**

P1 proposes attaching `evidence_paths` and `verified_at` metadata to documentation.

This is a good, low-complexity mechanism.

However, the proposed trust rule is too strong:

> A document with no changed evidence remains trusted.

A more accurate statement would be:

> A previously verified document whose known evidence dependencies have not changed remains unchanged relative to its recorded verification baseline.

These are not equivalent.

### 3.1 Previously incorrect documents remain incorrect

Suppose a document was marked verified even though the verification missed an implementation defect.

If the relevant source files never change, a Git-based drift detector will never identify the error.

The documentation remains unchanged, but it was never correct.

The findings described in the current plan demonstrate this exact risk.

### 3.2 Indirect changes may invalidate existing documentation

A document might describe an event consumer while listing only the consumer implementation as evidence.

Its effective behavior could nevertheless depend on:

- A shared event schema.
- Serialization or validation logic.
- Retry infrastructure.
- Transaction boundaries.
- Broker configuration.
- External library behavior.

Changes in those components might invalidate the documentation without modifying the directly referenced implementation file.

### 3.3 Verification status should be explicit

I recommend introducing a small set of verification states:

| State | Meaning |
|---|---|
| `unverified` | No trustworthy verification baseline exists |
| `verified` | Document claims were checked against a recorded source revision and evidence |
| `needs_reverification` | A relevant dependency or evidence source has changed |
| `known_divergence` | Intended/documented behavior differs from observed implementation behavior |

Optionally, reports may identify documents as `unchanged_since_verified`, but this should be treated as a derived condition rather than independent proof of correctness.

Avoid introducing elaborate state machines or databases.

A small metadata extension and a deterministic report should be sufficient initially.

### 3.4 Verification requires provenance

A `verified_at` commit alone is insufficient if the verification activity cannot be reconstructed.

Where practical, retain links to:

- The source revision.
- Relevant tests or CI runs.
- Review findings.
- Verification scope.
- Known exclusions.
- Responsible ticket or review activity.

Do not require claim-level evidence for every sentence.

**Suggested revision to P1:**

> Documents should retain lightweight verification metadata that identifies the source revision and relevant implementation evidence. An unchanged evidence set preserves the previous verification baseline but does not establish absolute correctness. Documents become candidates for re-verification when dependencies change, evidence becomes invalid, or review signals indicate possible divergence.

---

## 4. Critical Issue: Change Detection Must Consider Indirect Impact

**Priority: High**

F1–F3 propose searching documentation for changed source paths, public symbols, and terminology associated with modified behavior.

This is a reasonable first implementation, but it cannot provide comprehensive impact detection.

Consider:

```text
Shared RNG behavior changes
        |
        v
Checkpoint restoration affected
        |
        v
Replay determinism potentially affected
        |
        v
Determinism and checkpoint contracts
may require re-verification
```

The replay documentation may not mention the modified source file or symbol.

A text search would therefore miss the affected documentation.

### Recommendation

Extend impact detection in stages.

**Stage 1 — Existing mechanisms**

Use source-path references, public symbols, canonical-document mappings, existing mechanism registry metadata, and text searches.

**Stage 2 — Lightweight dependency relationships**

Use module imports, known service dependencies, event contracts, schema relationships, and existing registries.

**Stage 3 — Selective semantic investigation**

Ask an agent to investigate unresolved or potentially indirect impacts only when deterministic analysis is insufficient.

Do not construct a comprehensive dependency graph for the entire repository immediately.

The goal is to improve the recall of affected-document detection without introducing a large parallel infrastructure project.

The drift report should distinguish:

- Directly affected documents.
- Potentially indirectly affected documents.
- Unresolved impact relationships.

False positives are acceptable when advisory, but silent false negatives are more concerning because they create false confidence.

---

## 5. Critical Issue: Review Must Not Depend Exclusively on Drift Detection

**Priority: High**

P5 currently establishes a documentation-first review process in which reviewers inspect code when documentation drift is detected or a question is unanswered.

I agree with the documentation-first objective.

However, this condition is insufficient.

A document can be complete, internally consistent, and unchanged while the implementation violates its stated contract.

The plan itself reports serious findings that were discovered only through code inspection.

### Recommended review policy

Replace the proposed principle with:

**Documentation-first, evidence-backed, risk-triggered code inspection.**

Reviewers should normally begin with:

1. Canonical specifications and documentation.
2. Known limitations and intentional divergences.
3. Verification metadata.
4. Relevant test and CI evidence.
5. Recent changes and impact reports.

Code inspection should be triggered when:

- The documentation lacks a trustworthy verification baseline.
- A relevant source or dependency has changed.
- Tests or verification evidence are missing or failing.
- A reported behavior contradicts an invariant.
- A change affects critical concurrency, security, transaction, persistence, or recovery contracts.
- The documentation is insufficient to answer an important question.
- Independent sampling is necessary to validate the effectiveness of the documentation-maintenance process.

The review should remain proportional to the identified risk.

### Separate two review objectives

**Documentation and governance audit**

Evaluates architectural consistency, completeness, maintainability, process compliance, limitations, and evidence provenance.

This can often be performed without directly reading source code.

**Implementation correctness audit**

Evaluates whether actual implementation behavior satisfies the intended specification.

This requires appropriate implementation-level evidence and may require targeted source inspection.

A documentation-only audit should never claim to have independently established implementation correctness.

---

## 6. Additional Proposal: Introduce an Explicit Specification Layer

**Priority: Medium–High**

I recommend adding a **Specification Layer** to the documentation architecture.

This is not a recommendation to create a large new documentation hierarchy immediately.

It is a recommendation to formally distinguish normative requirements from explanatory documentation.

### 6.1 Why this distinction matters

The current proposal focuses on making documentation trustworthy.

However, not all documentation has the same authority.

For example:

- Architecture documents explain design and trade-offs.
- Operational guides explain how to use or operate the system.
- ADRs record architectural decisions.
- Historical audits record observations at a particular time.
- Specifications define behavior that implementation is required to satisfy.

Without an explicit distinction, agents may treat explanatory text or historical implementation observations as requirements.

This creates a risk of documentation and implementation reinforcing the same error.

### 6.2 Proposed conceptual model

**Specifications define what must be true.**

**Architecture documentation explains why and how the design is organized.**

**Implementation provides the actual behavior.**

**Verification evidence demonstrates whether implementation satisfies the specification.**

The desired relationship is:

```text
Feature
   |
   v
Normative Specification
   |
   +---- Required behavior
   +---- Invariants
   +---- Interfaces and contracts
   +---- Failure semantics
   +---- Acceptance conditions
   |
   v
Implementation Mapping
   |
   v
Verification Evidence
   |
   v
Known Divergences / Findings
```

This relationship is particularly valuable for AI-assisted planning, development, testing, review, and audit.

### 6.3 Avoid duplicating existing contracts

The supplied plan already reports existing contract documents, Bible chapters, mechanism registries, and a parity ledger.

These may already function as specifications.

The local team should first inventory their normative responsibilities.

Do not create a new specification document if an existing canonical contract already fulfills that role.

Instead:

- Identify existing normative sources.
- Establish their authority.
- Standardize references where useful.
- Migrate only when there is a concrete organizational benefit.

The first deliverable should be an **authority map**, not a mass file migration.

### 6.4 Recommended folder placement

For the current project, I would initially prefer:

```text
docs/
├── specs/
│   ├── engine/
│   ├── simulation/
│   ├── observability/
│   └── agent-workflow/
├── architecture/
├── guides/
├── audits/
└── ...
```

This is an illustrative target structure, not an instruction to create every directory.

Existing canonical contracts may remain in their current locations and be registered as specifications.

A top-level `specs/` directory becomes more attractive if the project later adopts numerous machine-readable artifacts such as JSON Schema, OpenAPI, AsyncAPI, or schemas used directly for generation and validation.

**Recommendation: Begin with a logical Specification Layer; decide on physical relocation only after inspecting the existing structure.**

### 6.5 What belongs in a specification?

A specification should concentrate on externally observable or architecturally significant obligations.

Typical content includes:

- Required behavior.
- Preconditions and postconditions.
- Invariants.
- Failure and recovery semantics.
- Concurrency guarantees.
- Persistence and ordering guarantees.
- Interface and event contracts.
- Explicitly unsupported behavior.
- Acceptance or verification conditions.

It should not reproduce implementation details or contain extensive code walkthroughs.

An illustrative specification:

```yaml
id: SPEC-ENGINE-RESTORE-001
title: Deterministic checkpoint restoration
status: approved

requirements:
  - id: RNG-001
    statement: >
      Restoring a checkpoint must preserve
      deterministic RNG continuation.

  - id: RNG-002
    statement: >
      Equivalent restored states and input
      sequences must produce equivalent
      resulting state hashes.

verification:
  tests:
    - tests/engine/test_checkpoint_restore.py

implementation:
  - src/engine/scenario_checkpoint.py

known_divergences:
  - R-eng-03
```

This example illustrates structure only. The exact paths, requirements, and IDs must be reconciled with the repository's actual contracts.

Existing parity-ledger entries or tests should be reused rather than copied into a new registry.

### 6.6 Specification authority must be explicit

A critical rule:

**An implementation defect must not automatically trigger a specification change.**

When implementation and specification disagree, the workflow should determine whether:

1. The implementation is defective.
2. The specification is obsolete.
3. A deliberate behavior change has been approved.
4. The discrepancy is unresolved.

A specification change should be reviewed as a change in intended behavior, not treated as a routine documentation cleanup.

This creates an independent reference against which AI-generated implementation can be evaluated.

### 6.7 Specifications should participate in ticket workflows

The existing ticket process can incorporate specifications without adding another mandatory agent or phase.

During Investigate:

- Identify affected normative requirements.
- Determine whether intended behavior is changing.
- Identify affected verification obligations.

During implementation and verification:

- Preserve unchanged invariants.
- Update tests where required.
- Record intentional divergences.

During Document-Update:

- Update specifications only when intended behavior has been approved to change.
- Update explanatory documentation as needed.
- Preserve the distinction between desired and observed behavior.

During Review:

- Check that changes to normative requirements were authorized.
- Confirm suitable evidence exists for critical obligations.

Do not require a new specification for every minor ticket.

Use specifications where their value justifies maintenance.

---

## 7. F1–F5: Detailed Recommendations

### F1 — Improve Investigate documentation discovery

**Approve with extension.**

Searching by changed paths, symbols, and removed behavior terminology is appropriate.

Also search for existing canonical topic references and known dependency relationships.

The output should distinguish:

- Required updates.
- Potentially affected documents.
- Explicitly excluded documents.

Avoid expanding the phase into a full repository audit.

### F2 — Extend doc-updater to satellite documentation

**Approve.**

Allow discovery beyond the initial Investigate list.

Require meaningful reasons for skipped documents.

Maintain a strict distinction between:

- Updating implementation explanations.
- Changing normative specifications.
- Preserving historical records.

The doc-updater should not autonomously rewrite approved requirements merely to match implementation.

### F3 — Satellite drift advisory

**Approve with risk-based escalation.**

Broad grep findings should remain advisory initially.

However, missing verification for critical invariants should receive stronger treatment than a low-risk documentation reference.

Define escalation rules based on concrete risks, not arbitrary documentation counts.

### F4 — Hand-orchestrated workflow parity

**Approve.**

All supported ticket-close paths should maintain equivalent documentation integrity expectations.

The implementation may differ between orchestration modes, but the resulting verification obligations should be consistent.

### F5 — Comments and docstrings

**Approve with scope clarification.**

Incorrect comments and docstrings can mislead agents.

However, comments should not automatically be treated as canonical documentation.

Check documentation-bearing comments in changed code, especially statements about invariants, behavior, concurrency, recovery, or lifecycle contracts.

Avoid requiring exhaustive comment review for unrelated changes.

---

## 8. P1–P5: Detailed Recommendations

| Proposal | Verdict | Recommended adjustment |
|---|---|---|
| P1 — Evidence anchors and verification SHA | Approve with changes | Add lightweight verification state and evidence provenance; avoid equating unchanged evidence with correctness |
| P2 — Generated numbers | Approve | Record revision and counting definitions |
| P3 — Known defects and limitations | Approve | Link findings to tickets, affected features, status, and verification |
| P4 — Canonical documentation | Strongly approve | Define canonical authority per contract/fact, not necessarily one file per entire subsystem |
| P5 — Review rules | Approve with changes | Use documentation-first, evidence-backed, risk-triggered inspection |

### Additional point for P3

Known limitations should have a basic lifecycle.

A finding should be discoverable while open, linked to its resolution, and retained where historically relevant.

Do not let the rule against documentation-only PRs prevent urgent correction of dangerously incorrect documentation.

### Additional point for P4

Historical ADRs and audit records should not automatically be rewritten to describe current behavior.

They represent decisions or observations made at a specific point in time.

Where necessary, add supersession links or status metadata.

Canonical current-state documentation and historical records have different responsibilities.

---

## 9. Additional Concern: Evidence Must Be Independent Enough to Be Useful

The plan aims to make documentation trustworthy through verification evidence.

That evidence must have meaningful quality.

In AI-first workflows, the same agent may:

1. Interpret a requirement.
2. Implement the feature.
3. Write the tests.
4. Update the documentation.
5. Declare verification successful.

All five artifacts could agree while sharing the same misunderstood requirement.

This does not mean every ticket needs multiple agents or extensive independent review.

It means the workflow should differentiate between:

- Evidence generated during implementation.
- Automated checks with independently defined expectations.
- Independent review findings.
- Runtime or integration evidence.
- Explicitly unverified assumptions.

For high-risk invariants, tests should preferably be derived from approved specifications or independently reviewed acceptance criteria rather than merely reflecting existing implementation behavior.

For low-risk changes, existing automated checks may be sufficient.

A useful rule is:

> Evidence establishes confidence only within its recorded verification scope.

For example, a passing unit test does not necessarily establish distributed recovery correctness.

### Existing parity ledger

The proposal reports approximately 2,300 parity-ledger entries, with 200 of 1,687 P0 entries having a `test_path`.

These figures should be confirmed from the pinned repository revision.

The ratio indicates a potential traceability or verification gap, but it does not independently establish that all remaining entries lack tests.

A missing `test_path` may mean missing evidence, incomplete registration, or a non-test-based verification mechanism.

Before introducing mandatory executable specifications, investigate this distinction.

---

## 10. Recommended Weekly Audit Model

I recommend treating weekly review primarily as a **documentation-governance and evidence audit**, not a repeated codebase-wide correctness audit.

### Normal weekly workflow

```text
Weekly Audit
    |
    v
Load Canonical Topic Map
    |
    v
Read Relevant Specs and Documents
    |
    v
Inspect Changes Since Prior Baseline
    |
    v
Evaluate Documentation Drift
    |
    v
Review Verification Evidence
    |
    v
Inspect Known Findings and Divergences
    |
    v
Risk Assessment
    |
    +---- Low risk, sufficient evidence
    |          |
    |          v
    |     Docs/Evidence Review Complete
    |
    +---- Unresolved or high-risk
               |
               v
        Targeted Code Verification
               |
               v
          Audit Report
```

The weekly report should make clear:

- Which domains were reviewed.
- Which source revision was used.
- Which documents were considered verified.
- Which documents require re-verification.
- Which risks were evaluated through code or tests.
- Which findings remain unresolved.
- Which areas were not examined.

Avoid reporting global correctness from partial evidence.

### Continuous verification remains essential

Ticket-level implementation verification should continue to operate close to the changes being made.

Weekly audit should evaluate whether that continuous process produced sufficient trustworthy evidence.

This is more scalable than forcing the weekly reviewer to rediscover the entire implementation.

### Independent sampling

Introduce occasional targeted spot-checks of apparently verified documentation.

The purpose is not to repeat all code reviews.

It is to evaluate whether the documentation-maintenance process itself is reliable.

If spot-checks repeatedly discover serious discrepancies, expand the relevant audit scope and improve the upstream workflow.

---

## 11. Baseline and Repository Revision Discipline

The plan identifies stale-checkout review as a significant source of incorrect conclusions.

I agree that repository revision discipline deserves special attention.

However, a simple warning about being behind `origin/main` is not sufficient for every workflow.

A review should establish:

- The exact reviewed commit.
- Whether the working tree was clean.
- The intended reference branch.
- The verification artifacts associated with that revision.
- Whether repository movement or new merges occurred during the review.

A pinned revision is preferable to a moving branch reference for reproducible analysis.

Do not automatically advance a documentation verification baseline to HEAD merely because the weekly review completed.

Baseline advancement should correspond to the evidence actually collected.

If verification fails or remains incomplete, preserve that state.

Git-based detection also needs reasonable treatment of file renames, deleted files, dependency updates, and changes to configuration or schemas outside the listed implementation paths.

These can be handled incrementally; a sophisticated indexing platform is not required immediately.

---

## 12. Proposed Implementation Priority

I would not implement every recommendation in a single initiative.

The plan already contains substantial seed work, and the existing AI-first SDLC must remain operational.

### Priority 0 — Correct existing reliability problems

1. Correct the confirmed stale or contradictory documents.
2. Record known behavior defects and unresolved divergences.
3. Strengthen F1 and F2 to discover satellite documentation.
4. Implement F3 as an advisory signal.
5. Ensure all ticket-close paths apply equivalent documentation checks.

**Success criterion:** The specific missed-documentation patterns identified in the proposal are reproduced in regression scenarios and detected by the improved workflow.

### Priority 1 — Establish trustworthy review baselines

1. Pilot `evidence_paths` and `verified_at` on a small set of canonical documents.
2. Add basic verification status and provenance.
3. Introduce risk-triggered inspection criteria.
4. Define canonical authority for the pilot domains.
5. Establish a repeatable documentation-first weekly review.

**Success criterion:** A reviewer can identify what has been verified, at which revision, using what evidence, and what remains uncertain without repeatedly exploring the entire subsystem.

### Priority 2 — Formalize specifications

1. Inventory existing normative contracts and Bible-derived requirements.
2. Identify duplication and unclear authority.
3. Choose one or two critical domains for a Specification Layer pilot.
4. Link existing specifications to tests, implementation references, and known divergences.
5. Extend ticket workflow instructions to distinguish specification changes from ordinary documentation updates.

**Success criterion:** Planner, implementer, tester, and reviewer can use the same authoritative requirements without duplicating them or deriving intended behavior from possibly defective code.

### Priority 3 — Improve coverage based on evidence

Consider further enhancements only after measuring the effectiveness of the preceding changes:

- Indirect dependency impact analysis.
- More executable contract checks.
- Additional generated documentation.
- Better verification coverage for important invariants.
- Automated detection of repeated drift.
- More sophisticated retrieval or indexing.

Avoid implementing these solely because they are technically interesting.

---

## 13. Specific Acceptance Criteria

Before considering the revised plan complete, I would expect the local team to demonstrate the following:

**Documentation discovery**

- A known satellite-documentation miss is detected.
- Historical or intentionally unchanged documents can be excluded with a recorded reason.
- The system can distinguish required updates from advisory candidates.

**Verification metadata**

- A document can be linked to a specific source revision.
- A changed evidence dependency triggers a re-verification signal.
- A never-verified document cannot silently appear verified.
- Advancing the baseline requires a recorded verification activity.

**Documentation correctness**

- A known documentation/implementation contradiction is represented explicitly.
- Documentation is not automatically changed to match defective implementation.
- Critical behavior changes trigger appropriate verification.

**Specification governance**

- A normative specification can be identified without ambiguity.
- Its implementation and verification references are discoverable.
- Existing contracts are reused rather than duplicated.
- Changes to intended behavior require appropriate authorization.

**Weekly review**

- A reviewer can begin from documents and evidence.
- The reviewer can identify when code inspection is necessary.
- The resulting report states its scope and unresolved limitations.
- The reviewer does not need to scan unrelated repository areas merely to reconstruct context.

**Operational cost**

- The new process does not introduce disproportionate ticket overhead.
- The project measures repeated context consumption and review efficiency.
- Improvements are evaluated against actual missed findings, not token savings alone.

---

## 14. Answers to the Owner's Existing Questions

### Q1. Approve the five parts and seed batch?

**Yes, with targeted modifications.**

Preserve the existing architecture and implementation sequence, but revise the trust semantics in P1 and the code-inspection policy in P5.

Add lightweight consideration of indirect dependencies and specification authority.

The existing seed batch remains appropriate, subject to checking which defects and documentation corrections are still outstanding at implementation time.

### Q2. Where should the topic map and generated facts page live?

My default preference is `docs/architecture/`, registered in the existing documentation registry.

The location should support discoverability and avoid duplicating other indexes.

However, repository ownership conventions take precedence over this external preference.

### Q3. Should the review rule be added to CLAUDE.md?

**Yes, but not as an unconditional documentation-only rule.**

Suggested wording:

> Start feature, design, and architecture reviews from canonical specifications and documentation. Use recorded verification evidence and drift reports to establish review confidence. Inspect implementation selectively when evidence is insufficient, dependencies have changed, or risk requires independent verification. Do not infer implementation correctness solely from documentation freshness.

Keep the governing instruction concise; retain detailed procedures in the existing delivery-process documentation.

### Q4. Should the lead-planner dispatch the seed work after approval?

**Yes.**

Use existing ownership boundaries and agent responsibilities.

Prioritize remediation and improvements to the existing documentation-maintenance workflow.

Do not initiate a repository-wide specification migration as part of the first batch.

---

## 15. Additional Questions for the Local Lead-Planner

These questions require repository knowledge that I do not possess.

1. Which existing documents are currently normative, and which are merely explanatory or historical?
2. Do the existing Bible chapters, contract documents, mechanism registry, and parity ledger already establish specification authority?
3. What evidence is currently required before `doc-updater` or the workflow can declare documentation verified?
4. Can an existing gate distinguish stale documentation from incorrect documentation that was never validated properly?
5. Are cross-module and cross-service dependencies already represented in a reusable form?
6. Which implementation areas are classified as critical, and what verification requirements do they currently have?
7. Can the weekly review distinguish missing verification evidence from genuinely absent tests?
8. Which current workflow is responsible for approving changes to intended behavior rather than merely recording implementation changes?

These questions should guide a limited repository investigation.

They are not justification for building new infrastructure before reviewing existing mechanisms.

---

## 16. Final Recommendation

**Approve the direction and refine the trust model.**

The proposal addresses an important scaling limitation in AI-first software development.

Its primary strength is that it tries to remove repeated repository exploration by improving the reliability and accessibility of existing project knowledge.

Its primary weakness is that it risks treating unchanged, previously reviewed documentation as stronger evidence of implementation correctness than it actually is.

The recommended target architecture has four distinct responsibilities:

**1. Specification — What must be true**

Authoritative requirements, contracts, invariants, and expected behavior.

**2. Documentation — How the system is designed and understood**

Architecture, rationale, operations, explanations, limitations, and historical decisions.

**3. Implementation — What the system actually does**

Source code, configuration, runtime behavior, and integrations.

**4. Verification Evidence — Why we believe implementation satisfies expectations**

Tests, CI results, analysis, reviews, and recorded observations.

These layers should be connected, not duplicated.

A trustworthy AI-first SDLC should enable agents to navigate:

**Feature → Specification → Architecture → Implementation Mapping → Verification Evidence → Known Divergences**

The practical outcome should be that reviewers rarely need to reconstruct the entire repository context.

They should be able to answer most architecture and feature questions from trustworthy documentation and supporting evidence, then inspect only the implementation areas that warrant further validation.

**The objective is not to eliminate code reading. It is to eliminate unnecessary code reading while preserving independent verification.**

Finally, I strongly recommend treating the Specification Layer as an incremental governance improvement rather than a large new documentation project.

Start by identifying and strengthening the authoritative contracts that already exist.

Do not duplicate them, and do not create a second source of truth.

### Final decision

**APPROVE WITH CHANGES**

Required revisions before broad rollout:

1. Clarify the difference between document freshness and verified correctness.
2. Strengthen evidence provenance and baseline semantics.
3. Extend change-impact detection beyond direct text references where practical.
4. Replace unconditional documentation-only review with risk-triggered code verification.
5. Establish specification authority while reusing existing normative documents.

The remaining enhancements can be delivered incrementally, guided by actual drift findings, missed defects, verification gaps, and measured maintenance cost.

---

**External reviewer disclaimer**

This review is an independent architectural recommendation based on the supplied plan. It does not represent an implementation audit or direct verification of the repository. Repository-specific claims, proposed paths, ownership assignments, and implementation scope must be validated by the local agents and project owner before changes are made.
