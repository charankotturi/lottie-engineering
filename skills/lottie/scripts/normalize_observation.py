#!/usr/bin/env python3
"""Normalize a captured MCP tool call/result into an evidence record.

Input JSON may be a raw object or a wrapper with tool/name, arguments/input,
result/output, and error fields. This script does not call LottieFiles.
"""
import argparse, datetime, hashlib, json, pathlib, re

def redact(value):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if re.search(r"(token|authorization|cookie|secret|password|signed.?url|access.?key)", k, re.I):
                out[k] = "[REDACTED]"
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, list):
        return [redact(x) for x in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\\1[REDACTED]", value)
        return value
    return value

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--surface", default="unknown")
    p.add_argument("--status", default="OBSERVED")
    p.add_argument("--source-url", default="")
    a = p.parse_args()
    raw = json.loads(pathlib.Path(a.input).read_text())
    clean = redact(raw)
    record = {
        "id": "observation-" + hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()[:12],
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "surface": a.surface,
        "status": a.status,
        "source_url": a.source_url or None,
        "tool": clean.get("tool") or clean.get("name"),
        "arguments": clean.get("arguments") or clean.get("input"),
        "result": clean.get("result") or clean.get("output"),
        "error": clean.get("error"),
        "raw_redacted": clean
    }
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\\n")
    print(out)

if __name__ == "__main__":
    main()
