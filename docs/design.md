# Matrix and reducer design

## Map

Each matrix cell is identified by harness, task, repetition, model, and profile. Shell-capable agent jobs run in isolated worktrees with read-only source/model permissions and upload candidate patches. Separate scoring jobs start from a fresh checkout, apply candidates, and execute the clean evaluator in a digest-pinned, networkless, capability-dropped, read-only container without model or attestation credentials. A third job validates inert score archives before receiving OIDC/attestation authority.

The initial matrix is serial (`max-parallel: 1`) because free GitHub Models quotas are low enough that concurrent agent loops can turn rate-limit failures into apparent harness differences. Both variants install the same pinned Outfitter package; the base cell directly executes that installation's nested Pi dependency, and reduction rejects any observed Pi-version mismatch.

## Reduce

The reducer runs only after every scoring cell has successfully produced an attestation. It verifies each cell archive with `gh attestation verify`, extracts results only from verified subjects, enforces the exact expected cell set, and rejects Pi-version, provider, requested-model, or resolved-model mismatches. Valid passes/failures remain separate from invalid agent or infrastructure executions.

The report predicate records the digests of every verified input archive. The initial reducer computes descriptive pass rates only. A real comparison must add repeated runs and uncertainty estimates before making performance claims.

## Provenance

Each metadata-normalized cell archive is validated for safe paths, manifest integrity, expected cell identity, source SHA, provider/model, predicate consistency, and observed Pi version before becoming the subject of an `actions/attest@v4` custom attestation. Runtime timestamps and sessions mean separate runs intentionally produce different archive bytes.

The reduced report receives a second custom attestation. This proves that a named GitHub workflow identity produced particular bytes. It does not prove that the scorer is correct, the task is uncontaminated, or the experimental design is fair.

## Reports

Reports are artifacts by default. Optional committed reports use a separate `publish` job with `github-actions[bot]`, re-verify the reduced-report attestation, and write under `reports/evals/<run-id>/`. Agent and scoring matrix cells never receive `contents: write`.
