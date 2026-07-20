#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

python3 -m py_compile scripts/*.py fixtures/task-001/evaluator/evaluate.py tests/*.py
bash -n scripts/*.sh
actionlint .github/workflows/*.yml
python3 -m unittest discover -s tests -v

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"; find "$root" -type d -name __pycache__ -prune -exec rm -rf {} +' EXIT

scripts/prepare_fixture.sh fixtures/task-001/repo "$tmp/worktree"
printf '{"node":"test","outfitter":null,"pi":"test","harness":"base-pi"}\n' > "$tmp/runtime.json"
python3 scripts/collect_result.py \
  --worktree "$tmp/worktree" \
  --evaluator fixtures/task-001/evaluator/evaluate.py \
  --out "$tmp/results/base-pi" \
  --harness base-pi \
  --agent-status success \
  --task-id task-001 \
  --model gpt-4.1-mini \
  --provider github-models-legacy \
  --profile base \
  --runtime-metadata "$tmp/runtime.json" \
  >/dev/null

check-jsonschema \
  --schemafile schemas/result.schema.json \
  "$tmp/results/base-pi/result.json"

tar --sort=name --mtime='UTC 1970-01-01' \
  --owner=0 --group=0 --numeric-owner \
  -C "$tmp/results/base-pi" -cf - . | gzip -n > "$tmp/result-base-pi.tar.gz"
python3 scripts/validate_bundle.py \
  --bundle "$tmp/result-base-pi.tar.gz" \
  --extract-to "$tmp/validated" \
  --cell-id base-pi-task-001-r1 \
  --harness base-pi \
  --model gpt-4.1-mini \
  --provider github-models-legacy \
  --source-sha local \
  >/dev/null

python3 scripts/reduce_results.py "$tmp/results" "$tmp/report" >/dev/null
test -s "$tmp/report/report.md"
test -s "$tmp/report/results.json"

echo "all checks passed"
