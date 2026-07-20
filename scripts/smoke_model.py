#!/usr/bin/env python3
"""Make one minimal GitHub Models request and save non-secret evidence."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = "https://models.github.ai/inference/chat/completions"
API_VERSION = "2026-03-10"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="openai/gpt-4.1-mini")
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": "Reply with exactly: github-models-ok"}],
        "temperature": 0,
        "max_tokens": 16,
        "stream": False,
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "Content-Type": "application/json",
        },
    )

    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.load(response)
            status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read().decode(errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"message": raw[:1000]}
        evidence = {
            "schema_version": 1,
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ok": False,
            "endpoint": ENDPOINT,
            "api_version": API_VERSION,
            "requested_model": args.model,
            "http_status": error.code,
            "error": detail,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        print(json.dumps(evidence, indent=2), file=sys.stderr)
        return 1

    content = body.get("choices", [{}])[0].get("message", {}).get("content")
    evidence = {
        "schema_version": 1,
        "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": status == 200 and content == "github-models-ok",
        "endpoint": ENDPOINT,
        "api_version": API_VERSION,
        "requested_model": args.model,
        "resolved_model": body.get("model"),
        "http_status": status,
        "response": content,
        "usage": body.get("usage"),
        "client_elapsed_ms": round((time.monotonic() - started) * 1000),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
