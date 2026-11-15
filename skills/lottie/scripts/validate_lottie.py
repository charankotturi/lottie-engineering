#!/usr/bin/env python3
"""Conservative Lottie JSON / dotLottie validator. No network calls."""
import argparse, hashlib, json, math, pathlib, sys, zipfile
from datetime import datetime, timezone

def issue(items, status, code, message):
    items.append({"status": status, "code": code, "message": message})

def finite_tree(value, path="$", issues=None):
    issues = issues if issues is not None else []
    if isinstance(value, float) and not math.isfinite(value):
        issue(issues, "FAIL", "NON_FINITE_NUMBER", f"{path} contains a non-finite number")
    elif isinstance(value, dict):
        for k, v in value.items():
            finite_tree(v, f"{path}.{k}", issues)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            finite_tree(v, f"{path}[{i}]", issues)
    return issues

def validate_animation(data, base_dir, issues, label="animation"):
    if not isinstance(data, dict):
        issue(issues, "FAIL", "ROOT_NOT_OBJECT", f"{label}: root must be an object")
        return
    required = ["w", "h", "fr", "ip", "op", "layers"]
    for key in required:
        if key not in data:
            issue(issues, "FAIL", "MISSING_ROOT_FIELD", f"{label}: missing root field '{key}'")
    for key in ("w", "h", "fr"):
        val = data.get(key)
        if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
            issue(issues, "FAIL", "INVALID_DIMENSION_OR_RATE", f"{label}: '{key}' must be a positive number")
    ip, op = data.get("ip"), data.get("op")
    if not isinstance(ip, (int, float)) or not isinstance(op, (int, float)) or op <= ip:
        issue(issues, "FAIL", "INVALID_FRAME_RANGE", f"{label}: op must be greater than ip")
    if not isinstance(data.get("layers"), list):
        issue(issues, "FAIL", "LAYERS_NOT_ARRAY", f"{label}: layers must be an array")
        layers = []
    else:
        layers = data["layers"]
    if not layers:
        issue(issues, "WARN", "EMPTY_LAYERS", f"{label}: no layers found")
    ids = set()
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            issue(issues, "FAIL", "LAYER_NOT_OBJECT", f"{label}: layer {i} is not an object")
            continue
        for key in ("ty", "ip", "op", "st"):
            if key not in layer:
                issue(issues, "WARN", "LAYER_FIELD_MISSING", f"{label}: layer {i} has no '{key}'")
        if "ind" in layer:
            if layer["ind"] in ids:
                issue(issues, "WARN", "DUPLICATE_LAYER_INDEX", f"{label}: duplicate layer index {layer['ind']}")
            ids.add(layer["ind"])
        if "refId" in layer and layer["refId"] not in {a.get("id") for a in data.get("assets", []) if isinstance(a, dict)}:
            issue(issues, "FAIL", "UNRESOLVED_ASSET_REF", f"{label}: layer {i} references missing asset '{layer['refId']}'")
    for i, asset in enumerate(data.get("assets", []) if isinstance(data.get("assets", []), list) else []):
        if not isinstance(asset, dict):
            issue(issues, "FAIL", "ASSET_NOT_OBJECT", f"{label}: asset {i} is not an object")
            continue
        path = asset.get("p")
        if path and not asset.get("u") and not str(path).startswith(("data:", "http://", "https://")):
            candidate = (base_dir / str(path)).resolve()
            if not candidate.exists():
                issue(issues, "WARN", "MISSING_EXTERNAL_ASSET", f"{label}: asset path not found locally: {path}")
    finite_tree(data, issues=issues)
    if not any(x["status"] == "FAIL" for x in issues):
        issue(issues, "PASS", "BASELINE_STRUCTURE_VALID", f"{label}: baseline structural checks passed")
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode()
    if len(raw) > 5 * 1024 * 1024:
        issue(issues, "WARN", "LARGE_JSON", f"{label}: JSON exceeds 5 MiB")
    if len(layers) > 500:
        issue(issues, "WARN", "MANY_LAYERS", f"{label}: more than 500 layers")
    return

def validate_path(path, issues):
    path = pathlib.Path(path)
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                bad = z.testzip()
                if bad:
                    issue(issues, "FAIL", "ZIP_CRC_ERROR", f"dotLottie archive has corrupt member: {bad}")
                    return
                names = set(z.namelist())
                manifest_name = "manifest.json"
                if manifest_name not in names:
                    issue(issues, "FAIL", "MISSING_MANIFEST", "dotLottie archive has no manifest.json")
                    return
                manifest = json.loads(z.read(manifest_name))
                anims = manifest.get("animations", [])
                if not isinstance(anims, list) or not anims:
                    issue(issues, "FAIL", "NO_ANIMATIONS", "dotLottie manifest has no animations array")
                    return
                for item in anims:
                    if not isinstance(item, dict) or not item.get("id"):
                        issue(issues, "FAIL", "BAD_ANIMATION_ENTRY", "manifest animation entry must contain an id")
                        continue
                    name = f"animations/{item['id']}.json"
                    if name not in names:
                        issue(issues, "FAIL", "MISSING_ANIMATION_FILE", f"missing {name}")
                        continue
                    data = json.loads(z.read(name))
                    validate_animation(data, path.parent, issues, name)
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
            validate_animation(data, path.parent, issues)
    except (OSError, json.JSONDecodeError, zipfile.BadZipFile, KeyError) as e:
        issue(issues, "FAIL", "READ_OR_PARSE_ERROR", str(e))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--report")
    ap.add_argument("--html")
    ap.add_argument("--schema", help="Optional pinned JSON Schema file")
    args = ap.parse_args()
    p = pathlib.Path(args.file)
    issues = []
    if not p.exists():
        issue(issues, "FAIL", "FILE_NOT_FOUND", str(p))
    else:
        validate_path(p, issues)
    if args.schema and p.exists() and not zipfile.is_zipfile(p):
        try:
            from jsonschema import validate
            schema = json.loads(pathlib.Path(args.schema).read_text())
            data = json.loads(p.read_text())
            validate(instance=data, schema=schema)
            issue(issues, "PASS", "SCHEMA_VALID", "File passed configured JSON Schema")
        except ImportError:
            issue(issues, "SKIP", "JSONSCHEMA_NOT_INSTALLED", "Install requirements.txt to run schema validation")
        except Exception as e:
            issue(issues, "FAIL", "SCHEMA_VALIDATION_FAILED", str(e))
    counts = {s: sum(1 for x in issues if x["status"] == s) for s in ("PASS","FAIL","WARN","SKIP")}
    result = {
        "file": str(p),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "overall": "FAIL" if counts["FAIL"] else ("WARN" if counts["WARN"] or counts["SKIP"] else "PASS"),
        "checks": issues,
        "note": "Baseline structural validation only; not proof of cross-player compatibility."
    }
    print(json.dumps(result, indent=2))
    if args.report:
        out = pathlib.Path(args.report); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\\n")
    if args.html:
        rows = "".join(f"<tr><td>{x['status']}</td><td>{x['code']}</td><td>{x['message']}</td></tr>" for x in issues)
        html = f"""<!doctype html><meta charset='utf-8'><title>Lottie validation</title>
<h1>Lottie validation: {result['overall']}</h1><p>File: {p}</p>
<p>SHA-256: {result['sha256']}</p><table border='1' cellpadding='6'><tr><th>Status</th><th>Code</th><th>Message</th></tr>{rows}</table>"""
        out = pathlib.Path(args.html); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html)
    sys.exit(1 if counts["FAIL"] else 0)

if __name__ == "__main__":
    main()
