#!/usr/bin/env python3
"""Validate and safely extract an inert scored-result bundle before attestation."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import tarfile


def digest(path: pathlib.Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=pathlib.Path)
    parser.add_argument("--extract-to", required=True, type=pathlib.Path)
    parser.add_argument("--cell-id", required=True)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()

    destination = args.extract_to.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.bundle, "r:gz") as archive:
        for member in archive.getmembers():
            path = pathlib.PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
                raise ValueError(f"unsafe archive member: {member.name}")
        archive.extractall(destination, filter="data")

    manifest = destination / "manifest.sha256"
    if not manifest.is_file():
        raise ValueError("bundle is missing manifest.sha256")
    expected: dict[pathlib.Path, str] = {}
    for line in manifest.read_text().splitlines():
        checksum, separator, name = line.partition("  ")
        if not separator or len(checksum) != 64:
            raise ValueError(f"invalid manifest line: {line}")
        path = pathlib.PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe manifest path: {name}")
        expected[destination / path] = checksum

    actual = {path for path in destination.rglob("*") if path.is_file() and path != manifest}
    if set(expected) != actual:
        missing = sorted(str(path.relative_to(destination)) for path in set(expected) - actual)
        unlisted = sorted(str(path.relative_to(destination)) for path in actual - set(expected))
        raise ValueError(f"manifest mismatch; missing={missing}, unlisted={unlisted}")
    for path, checksum in expected.items():
        if digest(path) != checksum:
            raise ValueError(f"digest mismatch: {path.relative_to(destination)}")

    result = json.loads((destination / "result.json").read_text())
    predicate = json.loads((destination / "attestation-predicate.json").read_text())
    checks = {
        "cell_id": (result.get("cell_id"), args.cell_id),
        "harness": (result.get("variant", {}).get("harness"), args.harness),
        "requested_model": (result.get("variant", {}).get("requested_model"), args.model),
        "provider": (result.get("variant", {}).get("provider"), args.provider),
        "source_sha": (result.get("run", {}).get("source_sha"), args.source_sha),
        "predicate_cell": (predicate.get("cellId"), args.cell_id),
        "predicate_harness": (predicate.get("harness"), args.harness),
        "predicate_model": (predicate.get("requestedModel"), args.model),
        "predicate_provider": (predicate.get("provider"), args.provider),
        "predicate_source": (predicate.get("sourceSha"), args.source_sha),
        "predicate_status": (predicate.get("resultStatus"), result.get("outcome", {}).get("status")),
    }
    failures = {name: values for name, values in checks.items() if values[0] != values[1]}
    if failures:
        raise ValueError(f"bundle identity mismatch: {failures}")
    if not result.get("execution", {}).get("runtime", {}).get("pi"):
        raise ValueError("bundle lacks observed Pi runtime version")

    print(json.dumps({"ok": True, "cell_id": args.cell_id, "bundle_sha256": digest(args.bundle)}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError, tarfile.TarError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
