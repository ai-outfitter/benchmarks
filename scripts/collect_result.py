#!/usr/bin/env python3
"""Evaluate one matrix cell and emit a normalized result bundle."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any


def run(command: list[str], cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_sessions(session_root: pathlib.Path) -> dict[str, Any]:
    observed_models: set[str] = set()
    response_models: set[str] = set()
    observed_providers: set[str] = set()
    usage = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "cost": 0.0}
    jsonl_files = 0

    if not session_root.exists():
        return {
            "jsonl_files": 0,
            "models": [],
            "response_models": [],
            "providers": [],
            "usage": usage,
        }

    # Session JSONL contains one durable record per message. Count only assistant
    # message usage; recursively scanning event objects can count the same usage
    # more than once and can mistake nested dollar-cost fields for token counts.
    for path in session_root.rglob("*.jsonl"):
        jsonl_files += 1
        for line in path.read_text(errors="replace").splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if value.get("type") == "model_change":
                provider = value.get("provider")
                model_id = value.get("modelId")
                if isinstance(provider, str):
                    observed_providers.add(provider)
                if isinstance(model_id, str):
                    observed_models.add(model_id)
            if value.get("type") != "message":
                continue
            message = value.get("message")
            if not isinstance(message, dict) or message.get("role") != "assistant":
                continue
            provider = message.get("provider")
            model = message.get("model")
            response_model = message.get("responseModel")
            if isinstance(provider, str):
                observed_providers.add(provider)
            if isinstance(model, str):
                observed_models.add(model)
            if isinstance(response_model, str):
                response_models.add(response_model)
            found_usage = message.get("usage")
            if not isinstance(found_usage, dict):
                continue
            key_map = {
                "input": "input",
                "output": "output",
                "cacheRead": "cache_read",
                "cacheWrite": "cache_write",
            }
            for source, destination in key_map.items():
                number = found_usage.get(source)
                if isinstance(number, (int, float)) and not isinstance(number, bool):
                    usage[destination] += number
            cost = found_usage.get("cost")
            if isinstance(cost, dict):
                total = cost.get("total")
                if isinstance(total, (int, float)) and not isinstance(total, bool):
                    usage["cost"] += total

    return {
        "jsonl_files": jsonl_files,
        "models": sorted(observed_models),
        "response_models": sorted(response_models),
        "providers": sorted(observed_providers),
        "usage": usage,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True, type=pathlib.Path)
    parser.add_argument("--evaluator", type=pathlib.Path)
    parser.add_argument("--test-log", type=pathlib.Path)
    parser.add_argument("--test-exit-code", type=int)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--agent-status", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--profile-ref", default="")
    parser.add_argument("--action-ref", default="")
    parser.add_argument("--outfitter-version", default="")
    parser.add_argument("--pi-version", default="")
    parser.add_argument("--run-id", default="local")
    parser.add_argument("--run-attempt", default="1")
    parser.add_argument("--repository", default="local")
    parser.add_argument("--sha", default="local")
    parser.add_argument("--repetition", default="1")
    parser.add_argument("--session-root", type=pathlib.Path)
    parser.add_argument("--runtime-metadata", type=pathlib.Path)
    parser.add_argument("--infrastructure-error", default="")
    args = parser.parse_args()

    worktree = args.worktree.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    if args.test_log is not None:
        if args.test_exit_code is None:
            parser.error("--test-exit-code is required with --test-log")
        evaluation_output = args.test_log.read_text(errors="replace")
        evaluation_returncode = args.test_exit_code
    elif args.evaluator is not None:
        evaluation = run([sys.executable, str(args.evaluator.resolve()), "--repo", str(worktree)])
        evaluation_output = evaluation.stdout + evaluation.stderr
        evaluation_returncode = evaluation.returncode
    else:
        parser.error("provide either --evaluator or --test-log/--test-exit-code")
    test_log = out / "test.log"
    test_log.write_text(evaluation_output)

    git_add = run(["git", "add", "-N", "."], cwd=worktree)
    patch = run(["git", "diff", "--binary", "HEAD", "--"], cwd=worktree)
    patch_path = out / "patch.diff"
    patch_path.write_text(patch.stdout)

    infrastructure_error = args.infrastructure_error
    if git_add.returncode != 0 or patch.returncode != 0:
        infrastructure_error = infrastructure_error or "patch_capture_failed"

    match = re.search(r"Ran (\d+) tests?", evaluation_output)
    tests_run = int(match.group(1)) if match else None
    agent_ok = args.agent_status == "success"
    if infrastructure_error:
        status = "invalid"
        failure_class = "infrastructure"
    elif not agent_ok:
        status = "invalid"
        failure_class = "agent_execution"
    elif evaluation_returncode == 0:
        status = "pass"
        failure_class = "none"
    else:
        status = "fail"
        failure_class = "benchmark"

    session_summary: dict[str, Any] = {
        "jsonl_files": 0,
        "models": [],
        "response_models": [],
        "providers": [],
        "usage": {},
    }
    if args.session_root and args.session_root.exists():
        session_summary = scan_sessions(args.session_root)
        destination = out / "sessions"
        shutil.copytree(args.session_root, destination, dirs_exist_ok=True)

    runtime_metadata: dict[str, Any] = {}
    if args.runtime_metadata and args.runtime_metadata.exists():
        runtime_metadata = json.loads(args.runtime_metadata.read_text())

    cell_id = f"{args.harness}-{args.task_id}-r{args.repetition}"
    result = {
        "schema_version": 1,
        "cell_id": cell_id,
        "run": {
            "repository": args.repository,
            "workflow_run_id": args.run_id,
            "workflow_run_attempt": args.run_attempt,
            "source_sha": args.sha,
            "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
        "experiment": {
            "kind": "infrastructure-fixture",
            "task_id": args.task_id,
            "repetition": int(args.repetition),
        },
        "variant": {
            "harness": args.harness,
            "profile": args.profile,
            "profile_ref": args.profile_ref or None,
            "action_ref": args.action_ref or None,
            "provider": args.provider,
            "requested_model": args.model,
            "outfitter_version": args.outfitter_version or None,
            "pi_version": args.pi_version or None,
            "tools": ["read", "bash", "edit", "write", "grep", "find", "ls"],
        },
        "execution": {
            "agent_status": args.agent_status,
            "infrastructure_error": infrastructure_error or None,
            "runtime": runtime_metadata,
            "session": session_summary,
        },
        "outcome": {
            "status": status,
            "failure_class": failure_class,
            "score": 1 if status == "pass" else 0,
            "test_exit_code": evaluation_returncode,
            "tests_run": tests_run,
        },
    }
    result_path = out / "result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    predicate = {
        "schemaVersion": 1,
        "experimentKind": "infrastructure-fixture",
        "cellId": cell_id,
        "harness": args.harness,
        "taskId": args.task_id,
        "requestedModel": args.model,
        "provider": args.provider,
        "sourceSha": args.sha,
        "resultStatus": status,
    }
    (out / "attestation-predicate.json").write_text(
        json.dumps(predicate, indent=2, sort_keys=True) + "\n"
    )

    manifest = out / "manifest.sha256"
    manifest_files = sorted(path for path in out.rglob("*") if path.is_file() and path != manifest)
    manifest.write_text(
        "".join(f"{sha256(path)}  {path.relative_to(out)}\n" for path in manifest_files)
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
