#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 FIXTURE_REPO WORKTREE" >&2
  exit 2
fi

fixture_repo="$(realpath "$1")"
worktree="$2"
rm -rf "$worktree"
mkdir -p "$worktree"
cp -a "$fixture_repo/." "$worktree/"

git -C "$worktree" init -q
git -C "$worktree" config user.name "benchmark-fixture"
git -C "$worktree" config user.email "benchmark-fixture@example.invalid"
git -C "$worktree" add .
git -C "$worktree" commit -qm "fixture baseline"
