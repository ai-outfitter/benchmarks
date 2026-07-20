# Hosted validation log

## Inference mode decision

The no-secret proof now targets the legacy GitHub Models endpoint:

- endpoint: `https://models.inference.ai.azure.com/chat/completions`
- provider: `github-models-legacy`
- model ID: `gpt-4.1-mini`
- credential: ephemeral workflow `GITHUB_TOKEN` with `models: read`

A local authenticated Pi-shaped streaming/tool request returned HTTP 200, issued the expected tool call, and resolved the model to `gpt-4.1-mini-2025-04-14`. A real base-Pi fixture run through this provider also exited successfully, passed all five evaluator tests, and recorded the same resolved model. The newer `models.github.ai` path remains an optional future mode requiring organization enablement or an explicit key.

## Run 29783607320 — organization-aware endpoint policy gate

First hosted run: <https://github.com/ai-outfitter/benchmarks/actions/runs/29783607320>

Result: stopped intentionally at `preflight` before any agent job.

Observed evidence:

- Workflow requested `permissions: models: read`.
- `POST https://models.github.ai/inference/chat/completions` returned HTTP 403 for the repository's ephemeral `GITHUB_TOKEN`.
- The same endpoint succeeds with the maintainer's local GitHub credential.
- The organization-attributed endpoint returned HTTP 403 with that local credential.

Interpretation: GitHub Models is not enabled for the `ai-outfitter` organization. This is a policy gate on the organization-aware endpoint, not a model, Pi, Outfitter, or workflow syntax failure. The next hosted run tests the legacy endpoint instead.

If the organization-aware mode is desired later, GitHub's current setup path is:

1. Open <https://github.com/organizations/ai-outfitter/settings/models/development>.
2. Under **Models in your organization**, change **Disabled** to **Enabled**.
3. Leave **All publishers** enabled for the initial proof, or explicitly allow the OpenAI publisher and `gpt-4.1-mini`.
4. Re-run `fixture-eval.yml` with `commit_report=false`.

Primary source: [Managing your team's model usage](https://docs.github.com/en/github-models/github-models-at-scale/manage-models-at-scale).

Do not work around this gate with a broad human PAT. Use the legacy ephemeral-token mode for the free proof; if that path is retired, provision a dedicated fine-grained Models credential or change providers in a separately identified experiment.
