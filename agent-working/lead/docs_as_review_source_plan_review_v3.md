## External AI Review — Rev 3.1 Summary

**Reviewer:** External AI Reviewer (ChatGPT)  
**Scope:** `docs_as_review_source_plan.md`, Rev 3.1, including Batch J  
**Verdict:** **Approve direction, with minor corrections before full implementation.**

The plan is now mature enough to begin staged implementation. It correctly prioritizes existing documentation workflows, normative specification authority, verification evidence, and selective code inspection without introducing unnecessary infrastructure.

### What I agree with

- Batch J is a valuable addition for identifying potentially stale documents across approximately 450 living docs.
- Script-first detection followed by agent triage is appropriate.
- Reusing existing tools and avoiding a new specification folder, registry, or agent is the right decision.
- Deferring claim-by-claim verification of approximately 186 normative docs is reasonable given the estimated cost.
- Separating `unverified`, `accurate`, and evidence-backed verification is essential.

### Remaining issues

1. **Batch J acceptance criteria:** Some known stale documents may not be discoverable by the proposed heuristics. Do not require impossible detections or hardcode known findings to pass tests.

2. **Dependency inconsistency:** Batch E depends on B and C, but the proposed initial subset contains only A, B, and E. Correct the dependency or adjust the subset.

3. **Heuristic limitations:** Source timestamps and missing symbols indicate potential staleness, not confirmed incorrectness. Avoid false confidence and classify unresolved symbols appropriately.

4. **Plan lifecycle:** Clarify how active plans are distinguished from historical records. Do not exclude all `plans/` files before checking their status.

5. **Repeated triage:** Preserve previous `accurate` dispositions against unchanged evidence to avoid repeatedly reviewing the same false positives.

6. **Topic-map scope:** Keep the topic map focused on canonical sources and normative authority. Track all living-document verification states in the drift report instead.

### Recommended Batch J execution

- **J1 — Detection pilot:** Build and run the ranking script against a pinned revision.
- **J2 — Evaluate:** Measure flagged documents, false positives, known misses, and distribution by domain.
- **J3 — Remediation:** Estimate and dispatch domain-specific fixes based on actual results rather than assuming all 6–10 tickets are necessary.

### Owner decisions recommended

- **Implementation:** Approve staged implementation, with corrected dependencies. Approve Batch J's read-only pilot before committing to its full remediation scope.
- **CLAUDE.md:** Approve the proposed policy in principle, subject to reviewing the actual diff before merge.
- **Weekly audit:** Approve lightweight scripted checks at the existing weekly close, plus 2–3 independent code/document spot-checks during retrospectives.

### Final assessment

The architecture is sound. No additional major redesign is needed.

The remaining work is primarily about making Batch J's detection guarantees, acceptance criteria, execution scope, and dependency ordering precise.

**Proceed incrementally and evaluate effectiveness through missed findings and documentation correctness, not token savings alone.**

*Reviewer limitation: I am an external AI reviewer. This assessment is based on the supplied Rev 3.1 plan, not independent inspection of the live repository.*