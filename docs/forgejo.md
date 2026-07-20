# Forgejo/Gitea fallback

Forgejo/Gitea is a stretch portability target after the GitHub-native proof.

Proposed shape:

- same matrix → artifact → reducer pipeline;
- dedicated `benchmark-bot` machine account;
- repository-scoped report token injected only into the reducer;
- no write token in agent matrix cells;
- explicit recursion guards for generated report commits;
- `tea`, `fj`, or raw API calls instead of assuming `gh`;
- in-toto/SLSA-shaped portable provenance signed with keyless OIDC when trustworthy and supported, otherwise a protected key-backed signer.

A machine-account access token supplies Forgejo actor authorization; it is not a cryptographic attestation.

Before porting, verify the exact server/runner versions support matrix contexts and cross-job artifacts. If artifact actions are incompatible, use a runner-accessible object store with run- and cell-specific keys.
