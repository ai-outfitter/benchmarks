# Contributing

## Development

Enter the pinned development environment and run all checks:

```bash
nix develop
./scripts/check.sh
```

## Experiment changes

A pull request that changes a comparison must state:

- research question and decision informed;
- independent variable;
- controlled model, tasks, tools, prompt, timeout, and retry settings;
- evaluator and failure-classification rules;
- sample size and stopping rule;
- claims the resulting evidence can and cannot support.

Do not tune one profile against evaluation tasks and then report those same tasks as an unbiased test set.

## Security

Treat task repositories, issue text, patches, and model output as untrusted. Matrix jobs receive read-only repository access. Keep report-writing credentials in the reducer only.
