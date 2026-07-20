# Security and trust boundaries

## Credentials

- Shell-capable agent cells: `contents: read`, `models: read`.
- Fresh scoring cells: `contents: read`; no model, OIDC, or attestation permission.
- Inert-bundle attestors: `contents: read`, `id-token: write`, `attestations: write`; no candidate execution.
- Reducer: `contents: read`, `id-token: write`, `attestations: write`.
- Separate optional publisher: `contents: write`; no model or OIDC permission.

No long-lived model API key is required for the GitHub-hosted proof. Agent cells cannot mint OIDC tokens, publish attestations, or receive a machine-account/report-writer token.

## Untrusted inputs

Benchmark repositories and task descriptions can contain prompt injection. Token scope—not prompt wording—is the enforcement boundary. Agent output is treated only as a candidate patch. Scoring starts from a fresh checkout and executes candidate code inside a networkless, read-only, capability-dropped container without credentials. Attestation happens later over inert archives.

## Attestation limits

GitHub attestations bind artifact digests to workflow identity and predicate claims. They do not establish semantic correctness. Verification still depends on source review, workflow revision, runner security, evaluator integrity, and experiment design.

## Report commits

The workflow is `workflow_dispatch`-only and generated commits include `[skip ci]`. Publication requires a successful reduced-report attestation and independently verifies that attestation before pushing. If default-branch protection blocks direct pushes, replace direct commits with an `eval-reports/*` branch and pull request.
