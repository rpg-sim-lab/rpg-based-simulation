#!/bin/bash
# Tree check for the death-closes-project kit: a frozen tree must be EXACTLY `git ls-tree -r <sha>` (same paths, same blobs, symlinks included), hold no data/runs and no __pycache__.
# Usage: bash death_closes_project_tree_check.sh <repo checkout holding the shas> <sha> <tree> [<sha> <tree> ...]    (run it before AND after each arm's run; exit 0 only when every tree is EXACT and clean)
set -u
here=$(cd "$(dirname "$0")" && pwd)
py=${PY:-/mnt/data/venv-sync2/bin/python}
repo=${1:?repo}; shift
rc=0
while [ $# -ge 2 ]; do
  sha=$1; tree=$2; shift 2
  $py -I -B "$here/person_attack_tree_check.py" --repo "$repo" --sha "$sha" --tree "$tree" || rc=1
  n=$(find "$tree" -name __pycache__ | wc -l); r=$(ls "$tree/data/runs" 2>/dev/null | wc -l)
  echo "$tree: __pycache__=$n data/runs entries=$r"; { [ "$n" -eq 0 ] && [ "$r" -eq 0 ]; } || rc=1
done
exit $rc
