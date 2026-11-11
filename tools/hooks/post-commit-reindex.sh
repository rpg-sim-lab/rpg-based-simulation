#!/usr/bin/env bash
# Post-commit hook, two jobs:
#  1. Registry regen for a merge commit that leaves docs/REGISTRY.yaml stale (always on).
#  2. Incremental knowledge-index reindex when docs/ or agent-working/tickets/done/ changed. OPT-IN per clone:
#       git config --bool knowledge.reindexOnCommit true     (shared by every worktree of the clone)
#     The reindex loads the embedding model and can exhaust memory (TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED),
#     so by default a commit that would have triggered it prints one skip line instead. `make knowledge-index-update`
#     runs it by hand.
# Install: make install-hooks
# No-op for the reindex if agent-working/.index/knowledge-index/ does not exist or if HEAD~1 is unavailable (first commit).

set -euo pipefail

# Guard: no HEAD~1 on first commit
git rev-parse HEAD~1 2>/dev/null || exit 0

changed=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || true)

if echo "$changed" | grep -qE '^(docs/|agent-working/tickets/done/)'; then
    if [ -f agent-working/.index/knowledge-index/knowledge.db ]; then
        opt_in=$(git config --bool knowledge.reindexOnCommit 2>/dev/null || true)
        if [ "$opt_in" = "true" ]; then
            echo "[knowledge-search] Relevant files changed — running incremental reindex..."
            python3 tools/knowledge_search.py build --incremental
        else
            echo "[knowledge-search] reindex skipped (opt-in): run 'git config --bool knowledge.reindexOnCommit true' to reindex on commit, or 'make knowledge-index-update' by hand"
        fi
    fi
fi

# A merge finished with `git commit` (it stopped on another conflict) never runs post-merge, so the
# registry-regen driver's "keep ours" result stands. Regenerate here, for merge commits only.
# Idempotent: if post-merge also ran, --check returns 0. The regen commit has one parent, so it cannot loop.
if git rev-parse -q --verify HEAD^2 >/dev/null && [ -f tools/generate_registry.py ]; then
    rc=0
    python3 tools/generate_registry.py --check >/dev/null 2>&1 || rc=$?
    if [ "$rc" -eq 2 ]; then
        python3 tools/generate_registry.py
        git add docs/REGISTRY.yaml
        git commit -q -m "auto-regenerate docs/REGISTRY.yaml after merge"
        echo "[registry-post-commit] docs/REGISTRY.yaml regenerated and committed"
    fi
fi
