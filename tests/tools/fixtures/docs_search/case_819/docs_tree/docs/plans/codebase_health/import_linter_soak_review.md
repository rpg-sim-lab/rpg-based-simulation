---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-08
tags: [delivery, planning]
---

178: (`e5cf25404` and `0a12a0152` are one unit). The phase19 hot-path test stays a test; its OFF-mode condition is
179: UNENFORCED until `TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK` lands (owner decision 2026-10-18, #547).
180: 
139: 
140: - `uvx --from import-linter==2.15 lint-imports --config codebase/structure/importlinter.toml`: exit 0,
141:   `Contracts: 17 kept, 0 broken.` No unmatched-ignore warning (`unmatched_ignore_imports_alerting = "warn"` is set on
161: None so far. The contracts count a `TYPE_CHECKING` import on purpose (`exclude_type_checking_imports = false`, see the
162: header of `codebase/structure/importlinter.toml`: a contract may not be looser than the test it replaces). The
163: `src.core.strategic -> src.ai.goals.base` finding is the case that rule exists for: the import is annotation-only, yet
