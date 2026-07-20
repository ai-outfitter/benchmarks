# Agent benchmark infrastructure fixture

> **Claim boundary:** This fixture validates matrix execution, result normalization,
> reduction, report publication, and attestation plumbing. It does **not** establish
> that one scaffold outperforms another.

## Aggregate

| Harness | Total | Valid | Pass | Fail | Invalid | Pass rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| base-pi | 1 | 1 | 1 | 0 | 0 | 100.0% |
| outfitter-pi | 1 | 1 | 1 | 0 | 0 | 100.0% |

## Cells

| Cell | Harness | Task | Model | Agent | Outcome | Failure class |
| --- | --- | --- | --- | --- | --- | --- |
| base-pi-task-001-r1 | base-pi | task-001 | gpt-4.1-mini | success | pass | none |
| outfitter-pi-task-001-r1 | outfitter-pi | task-001 | gpt-4.1-mini | success | pass | none |

## Interpretation

A green report means the infrastructure transported and scored the fixture.
Real scaffold comparison requires preregistered tasks, repeated runs, locked model/tool
settings, and confidence intervals.
