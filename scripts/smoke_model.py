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

DEFAULT_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--api-version", default="")
    parser.add_argument("--pi-shaped", action="store_true")
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    if args.pi_shaped:
        payload = {
            "model": args.model,
            "messages": [
                {"role": "system", "content": "Use tools when asked."},
                {"role": "user", "content": "Call echo with value ok."},
            ],
            "stream": True,
            "stream_options": {"include_usage": True},
            "store": False,
            "max_completion_tokens": 32,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "echo",
                        "description": "Echo a value",
                        "parameters": {
                            "type": "object",
                            "properties": {"value": {"type": "string"}},
                            "required": ["value"],
                            "additionalProperties": False,
                        },
                        "strict": False,
                    },
                }
            ],
            "tool_choice": "auto",
        }
    else:
        payload = {
            "model": args.model,
            "messages": [{"role": "user", "content": "Reply with exactly: github-models-ok"}],
            "temperature": 0,
            "max_tokens": 16,
            "stream": False,
        }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if args.api_version:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = args.api_version
    request = urllib.request.Request(
        args.endpoint,
        data=json.dumps(payload).encode(),
        method="POST",
        headers=headers,
    )

    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_body = response.read().decode(errors="replace")
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
            "endpoint": args.endpoint,
            "api_version": args.api_version or None,
            "requested_model": args.model,
            "pi_shaped": args.pi_shaped,
            "http_status": error.code,
            "error": detail,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        print(json.dumps(evidence, indent=2), file=sys.stderr)
        return 1

    if args.pi_shaped:
        chunks = []
        for line in raw_body.splitlines():
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            chunks.append(json.loads(line.removeprefix("data: ")))
        resolved_models = {chunk.get("model") for chunk in chunks if chunk.get("model")}
        tool_names = {
            call.get("function", {}).get("name")
            for chunk in chunks
            for choice in chunk.get("choices", [])
            for call in choice.get("delta", {}).get("tool_calls", [])
            if call.get("function", {}).get("name")
        }
        usage = next((chunk.get("usage") for chunk in reversed(chunks) if chunk.get("usage")), None)
        content = "tool_call:echo" if "echo" in tool_names else None
        resolved_model = sorted(resolved_models)[0] if len(resolved_models) == 1 else None
        expected_content = "tool_call:echo"
    else:
        body = json.loads(raw_body)
        content = body.get("choices", [{}])[0].get("message", {}).get("content")
        resolved_model = body.get("model")
        usage = body.get("usage")
        expected_content = "github-models-ok"

    evidence = {
        "schema_version": 1,
        "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": status == 200 and content == expected_content,
        "endpoint": args.endpoint,
        "api_version": args.api_version or None,
        "requested_model": args.model,
        "resolved_model": resolved_model,
        "pi_shaped": args.pi_shaped,
        "http_status": status,
        "response": content,
        "usage": usage,
        "client_elapsed_ms": round((time.monotonic() - started) * 1000),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
