#!/usr/bin/env python3
"""Reduce normalized matrix-cell results into JSON and Markdown reports."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import sys
from typing import Any


def load_results(root: pathlib.Path) -> list[dict[str, Any]]:
    by_cell: dict[str, dict[str, Any]] = {}
    for path in root.rglob("result.json"):
        value = json.loads(path.read_text())
        if value.get("schema_version") != 1:
            raise ValueError(f"unsupported schema in {path}")
        cell_id = value.get("cell_id")
        if not isinstance(cell_id, str) or not cell_id:
            raise ValueError(f"missing cell_id in {path}")
        if cell_id in by_cell:
            raise ValueError(f"duplicate cell_id {cell_id}: {path}")
        by_cell[cell_id] = value
    if not by_cell:
        raise ValueError(f"no result.json files found under {root}")
    return [by_cell[key] for key in sorted(by_cell)]


def validate_comparison(
    results: list[dict[str, Any]], expected_cells: set[str], require_parity: bool
) -> None:
    actual_cells = {result["cell_id"] for result in results}
    if expected_cells and actual_cells != expected_cells:
        missing = sorted(expected_cells - actual_cells)
        unexpected = sorted(actual_cells - expected_cells)
        raise ValueError(f"cell set mismatch; missing={missing}, unexpected={unexpected}")
    if not require_parity:
        return

    requested_models = {result["variant"]["requested_model"] for result in results}
    providers = {result["variant"]["provider"] for result in results}
    pi_versions = {result["execution"]["runtime"].get("pi") for result in results}
    response_models = {
        tuple(result["execution"]["session"].get("response_models", [])) for result in results
    }
    if len(requested_models) != 1:
        raise ValueError(f"requested model mismatch: {sorted(requested_models)}")
    if len(providers) != 1:
        raise ValueError(f"provider mismatch: {sorted(providers)}")
    if None in pi_versions or len(pi_versions) != 1:
        raise ValueError(f"Pi runtime mismatch or missing version: {sorted(str(v) for v in pi_versions)}")
    if any(not models for models in response_models) or len(response_models) != 1:
        raise ValueError(f"resolved response model mismatch or missing evidence: {sorted(response_models)}")


def summarize(
    results: list[dict[str, Any]], input_subjects: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    variants: dict[str, collections.Counter[str]] = {}
    for result in results:
        harness = result["variant"]["harness"]
        status = result["outcome"]["status"]
        variants.setdefault(harness, collections.Counter())[status] += 1

    summary_variants = {}
    for harness, counts in sorted(variants.items()):
        valid = counts["pass"] + counts["fail"]
        summary_variants[harness] = {
            "total": sum(counts.values()),
            "valid": valid,
            "passed": counts["pass"],
            "failed": counts["fail"],
            "invalid": counts["invalid"],
            "pass_rate": counts["pass"] / valid if valid else None,
        }
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment_kind": "infrastructure-fixture",
        "claim_boundary": "This fixture validates orchestration and provenance only; it does not measure scaffold superiority.",
        "cell_count": len(results),
        "input_subjects": input_subjects or [],
        "variants": summary_variants,
        "results": results,
    }


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Agent benchmark infrastructure fixture",
        "",
        "> **Claim boundary:** This fixture validates matrix execution, result normalization,",
        "> reduction, report publication, and attestation plumbing. It does **not** establish",
        "> that one scaffold outperforms another.",
        "",
        "## Aggregate",
        "",
        "| Harness | Total | Valid | Pass | Fail | Invalid | Pass rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for harness, value in summary["variants"].items():
        rate = "n/a" if value["pass_rate"] is None else f"{value['pass_rate']:.1%}"
        lines.append(
            f"| {harness} | {value['total']} | {value['valid']} | "
            f"{value['passed']} | {value['failed']} | {value['invalid']} | {rate} |"
        )
    lines.extend(
        [
            "",
            "## Cells",
            "",
            "| Cell | Harness | Task | Model | Agent | Outcome | Failure class |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for result in summary["results"]:
        lines.append(
            f"| {result['cell_id']} | {result['variant']['harness']} | "
            f"{result['experiment']['task_id']} | {result['variant']['requested_model']} | "
            f"{result['execution']['agent_status']} | {result['outcome']['status']} | "
            f"{result['outcome']['failure_class']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A green report means the infrastructure transported and scored the fixture.",
            "Real scaffold comparison requires preregistered tasks, repeated runs, locked model/tool",
            "settings, and confidence intervals.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--expected-cell", action="append", default=[])
    parser.add_argument("--require-parity", action="store_true")
    parser.add_argument("--input-manifest", type=pathlib.Path)
    args = parser.parse_args()
    try:
        results = load_results(args.input.resolve())
        validate_comparison(results, set(args.expected_cell), args.require_parity)
        input_subjects = (
            json.loads(args.input_manifest.read_text()) if args.input_manifest else []
        )
        if not isinstance(input_subjects, list):
            raise ValueError("input manifest must be a JSON array")
    except (ValueError, json.JSONDecodeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1

    summary = summarize(results, input_subjects)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output / "report.md").write_text(markdown(summary))
    predicate = {
        "schemaVersion": 1,
        "experimentKind": summary["experiment_kind"],
        "cellCount": summary["cell_count"],
        "inputSubjects": summary["input_subjects"],
        "variants": summary["variants"],
        "claimBoundary": summary["claim_boundary"],
    }
    (output / "attestation-predicate.json").write_text(
        json.dumps(predicate, indent=2, sort_keys=True) + "\n"
    )
    print(output / "report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
