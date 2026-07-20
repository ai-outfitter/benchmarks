# ai-outfitter/benchmarks

Reproducible, attested benchmarks for measuring AI agent profiles and harnesses while holding the model and evaluation task constant.

The initial milestone is deliberately smaller than a leaderboard run: prove that GitHub Actions can execute an Outfitter+Pi versus base-Pi matrix using GitHub Models, reduce normalized results into a report, and cryptographically attest the raw and reduced artifacts.

## Current experiment

`fixture-eval.yml` runs two serial matrix cells:

- `outfitter-pi` — [`ai-outfitter/actions`](https://github.com/ai-outfitter/actions) with the fixture profile.
- `base-pi` — Pi directly, with the same requested model and built-in tool allowlist.

Both receive:

- GitHub Models provider `github-models`
- requested model `openai/gpt-4.1-mini`
- the same task repository
- the same user prompt
- the same evaluator
- isolated Pi state

Agent jobs upload candidate patches without attestation authority. Fresh credential-separated scoring jobs apply those patches and run candidate code in a networkless container without model or OIDC credentials. Separate attestor jobs validate inert result archives before signing them. The reducer verifies every expected cell attestation and runtime/model parity before emitting an attested Markdown/JSON report.

> **Claim boundary:** the included task is an infrastructure fixture. A pass, failure, or difference between its two cells is not evidence that one scaffold outperforms another. Comparative claims require preregistered tasks, repeated runs, locked settings, and uncertainty estimates.

## Run it

The workflow is manual while the harness is being validated:

```bash
gh workflow run fixture-eval.yml --repo ai-outfitter/benchmarks -f commit_report=false
```

After it completes:

```bash
gh run download --repo ai-outfitter/benchmarks RUN_ID --name report-RUN_ID

gh attestation verify reduced-report.tar.gz \
  --repo ai-outfitter/benchmarks
```

Set `commit_report=true` only after the no-commit run and attestation verification succeed. Committed reports land under `reports/evals/<run-id>/`.

## Development

Use the Nix development shell:

```bash
nix develop
./scripts/check.sh
```

The check suite runs:

- Python compilation and unit tests
- shell parsing
- workflow validation with `actionlint`
- fixture collection and reduction
- normalized result JSON Schema validation

## Repository layout

```text
.github/workflows/fixture-eval.yml  GitHub matrix/reducer workflow
fixtures/                           Small infrastructure fixtures and evaluators
profiles/                           Outfitter profiles under comparison
schemas/                            Normalized result schemas
scripts/                            Preflight, collection, validation, reduction
reports/evals/                      Optional committed run reports
docs/                               Design, security, and portability notes
```

## Roadmap

1. Validate GitHub-hosted model auth and native attestations.
2. Validate committed report behavior and branch protection.
3. Add repetitions and infrastructure-failure classification.
4. Select a low-cost real benchmark slice.
5. Preregister the comparison protocol before profile tuning.
6. Add a Forgejo/Gitea fallback with portable signed provenance.

## License

MIT — see [`LICENSE.md`](LICENSE.md).
