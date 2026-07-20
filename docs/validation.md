# Hosted validation log

## Inference mode decision

The no-secret proof now targets the legacy GitHub Models endpoint:

- endpoint: `https://models.inference.ai.azure.com/chat/completions`
- provider: `github-models-legacy`
- model ID: `gpt-4.1-mini`
- credential: ephemeral workflow `GITHUB_TOKEN` with `models: read`

A local authenticated Pi-shaped streaming/tool request returned HTTP 200, issued the expected tool call, and resolved the model to `gpt-4.1-mini-2025-04-14`. A real base-Pi fixture run through this provider also exited successfully, passed all five evaluator tests, and recorded the same resolved model. The newer `models.github.ai` path remains an optional future mode requiring organization enablement or an explicit key.

## Run 29785706884 — complete committed attested proof

Hosted run: <https://github.com/ai-outfitter/benchmarks/actions/runs/29785706884>

All jobs passed: legacy-token preflight, both agents, sandboxed scoring, inert-bundle validation, both cell attestations, online cell verification, strict parity reduction, reduced-report attestation, independent publisher verification, and report commit.

Committed evidence: [`reports/evals/29785706884/`](../reports/evals/29785706884/).

Independent verification of the committed `report.tar.gz` succeeded. Both valid fixture cells passed all five tests, used Pi `0.80.10`, and recorded resolved model `gpt-4.1-mini-2025-04-14`. The attestation predicate binds both cell archive digests and states the infrastructure-only claim boundary.

Conclusion: the no-secret legacy GitHub Models + GitHub Actions + native attestation + committed reducer-report path is feasible. This does not yet answer whether an Outfitter profile outperforms base Pi.

## Run 29785470056 — valid report, incomplete committed subject

Hosted run: <https://github.com/ai-outfitter/benchmarks/actions/runs/29785470056>

All jobs, including publication, completed successfully and both cells produced valid passing fixture results with matching Pi/model evidence. The publisher verified and extracted the attested report archive before committing. However, the repository's `*.tar.gz` ignore rule prevented the copied attested subject from entering the commit, leaving only extracted files and the Sigstore bundle.

The report path is now explicitly unignored, and the local check suite fails if `reports/evals/*/report.tar.gz` is ignored. A final publication run must prove the committed tar verifies independently.

## Run 29785326265 — valid independently verified report

Hosted run: <https://github.com/ai-outfitter/benchmarks/actions/runs/29785326265>

Both harness cells passed the five-test fixture with no infrastructure errors, matching Pi `0.80.10`, provider `github-models-legacy`, and resolved model `gpt-4.1-mini-2025-04-14`. The reduced report attestation independently verified, including both input cell digests and the explicit no-performance-claim boundary.

## Run 29785085292 — complete provenance path, invalid handoff result

Hosted run: <https://github.com/ai-outfitter/benchmarks/actions/runs/29785085292>

The workflow completed successfully through reduced-report attestation, and the downloaded report independently verified with `gh attestation verify`. Both cells used Pi `0.80.10` and resolved `gpt-4.1-mini-2025-04-14`.

The normalized report marked both cells invalid instead of issuing false scores. Two candidate-handoff bugs were preserved as infrastructure evidence:

- `git -C` resolved the relative patch path inside the scoring worktree, so no candidate patch was applied;
- a `jq select()` expression emitted an empty execution metadata document when no prior infrastructure error existed.

The workflow now applies an absolute candidate-patch path and always emits explicit `agent_status` plus nullable `infrastructure_error`. Local checks reproduce the candidate capture/apply handoff.

## Run 29784881944 — legacy inference and cell attestations

Hosted run: <https://github.com/ai-outfitter/benchmarks/actions/runs/29784881944>

Validated successfully:

- legacy endpoint preflight with ephemeral `GITHUB_TOKEN` and `models: read`;
- Outfitter+Pi and base-Pi agent cells;
- credentialless, networkless container scoring;
- bundle integrity validation;
- both custom cell attestations;
- online verification of both cell attestations before reduction.

Reduction failed closed on a real comparison confound: Outfitter resolved Pi `0.80.10`, while base Pi was separately pinned to `0.80.9`. The base cell now installs the same pinned Outfitter package and directly executes its nested Pi dependency. The parity gate remains strict.

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
