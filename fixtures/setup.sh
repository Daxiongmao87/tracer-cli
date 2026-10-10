#!/usr/bin/env bash
# One-time fixture setup: turn each fixture directory into a clean git repo
# so the harness can reset it with `git checkout -- . && git clean -fdq`.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
for repo in pycalc pytask nodeblog; do
  d="$HERE/$repo"
  if [ ! -d "$d/.git" ]; then
    git -C "$d" init -q
    git -C "$d" add -A
    git -C "$d" -c user.name=tracer -c user.email=tracer@local \
      commit -qm "tracer fixture: clean baseline"
    echo "initialized $repo"
  else
    echo "$repo already a git repo, skipping"
  fi
done
