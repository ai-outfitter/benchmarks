# Hosted validation log

## Run 29783607320 — GitHub Models policy gate

First hosted run: <https://github.com/ai-outfitter/benchmarks/actions/runs/29783607320>

Result: stopped intentionally at `preflight` before any agent job.

Observed evidence:

- Workflow requested `permissions: models: read`.
- `POST https://models.github.ai/inference/chat/completions` returned HTTP 403 for the repository's ephemeral `GITHUB_TOKEN`.
- The same endpoint succeeds with the maintainer's local GitHub credential.
- The organization-attributed endpoint returned HTTP 403 with that local credential.

Interpretation: GitHub Models is not enabled for the `ai-outfitter` organization. This is an organization policy gate, not a model, Pi, Outfitter, or workflow syntax failure.

GitHub's current setup path for an organization owner:

1. Open <https://github.com/organizations/ai-outfitter/settings/models/development>.
2. Under **Models in your organization**, change **Disabled** to **Enabled**.
3. Leave **All publishers** enabled for the initial proof, or explicitly allow the OpenAI publisher and `openai/gpt-4.1-mini`.
4. Re-run `fixture-eval.yml` with `commit_report=false`.

Primary source: [Managing your team's model usage](https://docs.github.com/en/github-models/github-models-at-scale/manage-models-at-scale).

Do not work around this gate with a broad human PAT. If organization enablement is intentionally unavailable, provision a dedicated fine-grained Models credential or change inference providers in a separate experiment.
