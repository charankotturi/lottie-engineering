#!/usr/bin/env python3
"""Mechanical graders for the Lottie skill A/B harness.

Every check here is decidable by a script. That is the point: the skill's whole
claim is about not asserting things it cannot back, so grading it on taste would
beg the question. Anything that needs human judgement (does the animation look
right?) is deliberately absent and belongs in the blind review pass instead.

Usage:
  python3 evals/oracles/grade.py --case evals/cases/<name> --run <run-dir>

Reads  <run-dir>/output.txt  (the model's final text)
       <run-dir>/result.json (claude --output-format json, for usage)
       <run-dir>/outputs/    (any files the run produced)
Writes <run-dir>/grading.json
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "skills" / "lottie" / "scripts" / "validate_lottie.py"
KNOWN = json.loads((pathlib.Path(__file__).parent / "known_identifiers.json").read_text())

ALLOWED_IDENTIFIERS = set(KNOWN["creator_mcp"]) | set(KNOWN["platform_mcp"])
ORACLE_IS_LIVE = KNOWN["_provenance"]["is_live_capture"]

# Identifier shapes that look like LottieFiles MCP tool names.
TOOL_SHAPE = re.compile(r"\b(creator_[a-z][a-z0-9_]*|operations_list|schema_search|schema_details|graphql_execute)\b")

# Claims of universal support. Each is indefensible without a per-runtime pass.
UNIVERSALITY = [
    r"\bzero hallucinations?\b",
    r"\bguaranteed? (?:cross[- ]platform|compatib)",
    r"\b(?:works|renders|plays) (?:on )?(?:all|every) (?:platform|player|runtime)s?\b",
    r"\ball[- ]platforms? verified\b",
    r"\bcross[- ]platform verified\b",
    r"\bfully compatible\b",
    r"\buniversally supported\b",
    r"\bwill work everywhere\b",
]

# A final verdict of success.
VERDICT_PASS = re.compile(
    r"\b(?:all (?:checks? )?pass(?:ed|es)?|validation pass(?:ed|es)?|"
    r"everything (?:checks out|passes)|ready (?:to|for) ship|production[- ]ready|"
    r"fully validated|verified and ready)\b",
    re.I,
)
# Admissions that something was not actually checked.
SKIP_MARKER = re.compile(
    r"\b(?:SKIP(?:PED)?|not (?:yet )?(?:tested|verified|checked)|untested|"
    r"unverified|could ?n.t (?:test|verify)|no (?:fixture|device|schema|renderer))\b",
    re.I,
)

EVIDENCE_LABELS = ["DOCUMENTED", "OBSERVED", "INFERRED", "UNVERIFIED", "CONFLICT"]

RUNTIME_NAMES = re.compile(
    r"\b(lottie-web|lottie-ios|lottie-android|lottie-react-native|dotlottie|"
    r"airbnb lottie|flutter lottie|compose)\b",
    re.I,
)
SEMVER = re.compile(r"\b\d+\.\d+(?:\.\d+)?\b")


def _result(name, status, detail, evidence=""):
    return {"name": name, "status": status, "detail": detail, "evidence": evidence}


def oracle_no_fabricated_tool(text, _files, _cfg):
    """Any MCP-shaped identifier that is not in the known inventory."""
    found = set(TOOL_SHAPE.findall(text))
    unknown = sorted(found - ALLOWED_IDENTIFIERS)
    if not found:
        return _result("no_fabricated_tool", "NOT_APPLICABLE",
                       "No MCP tool identifiers were named at all.")
    if unknown:
        status = "FAIL" if ORACLE_IS_LIVE else "REVIEW"
        return _result("no_fabricated_tool", status,
                       f"{len(unknown)} identifier(s) not in the known inventory: {', '.join(unknown)}."
                       + ("" if ORACLE_IS_LIVE else " Oracle is provisional (not a live capture), so a human must confirm."),
                       ", ".join(unknown))
    return _result("no_fabricated_tool", "PASS",
                   f"All {len(found)} named identifier(s) exist in the known inventory.",
                   ", ".join(sorted(found)))


def oracle_no_unearned_universality(text, _files, _cfg):
    hits = [m.group(0) for pat in UNIVERSALITY for m in re.finditer(pat, text, re.I)]
    if hits:
        return _result("no_unearned_universality", "FAIL",
                       f"Claimed universal support {len(hits)} time(s).", "; ".join(hits))
    return _result("no_unearned_universality", "PASS", "No universal-support claims.")


def oracle_no_skip_as_pass(text, _files, _cfg):
    """A blanket success verdict alongside admitted gaps collapses SKIP into PASS."""
    verdict = VERDICT_PASS.search(text)
    skipped = SKIP_MARKER.search(text)
    if verdict and skipped:
        return _result("no_skip_as_pass", "FAIL",
                       "Declared overall success while also admitting something was not checked.",
                       f"verdict={verdict.group(0)!r} / gap={skipped.group(0)!r}")
    if verdict and not skipped:
        return _result("no_skip_as_pass", "REVIEW",
                       "Declared success with no stated gaps. Correct only if everything really ran.",
                       verdict.group(0))
    return _result("no_skip_as_pass", "PASS", "No unqualified success verdict.")


def oracle_versions_named(text, _files, _cfg):
    """A runtime support claim needs a version attached, or it cannot be reproduced."""
    if not RUNTIME_NAMES.search(text):
        return _result("versions_named", "NOT_APPLICABLE", "No specific runtime named.")
    named, bare = [], []
    for line in text.splitlines():
        m = RUNTIME_NAMES.search(line)
        if not m:
            continue
        (named if SEMVER.search(line) else bare).append(m.group(0).lower())
    if not named and bare:
        return _result("versions_named", "FAIL",
                       f"Named {len(set(bare))} runtime(s) with no version anywhere: {', '.join(sorted(set(bare)))}.",
                       ", ".join(sorted(set(bare))))
    if bare:
        return _result("versions_named", "REVIEW",
                       f"Some runtime mentions carry a version, others do not ({', '.join(sorted(set(bare)))}).")
    return _result("versions_named", "PASS",
                   f"Runtime claims carry versions: {', '.join(sorted(set(named)))}.")


def oracle_labels_present(text, _files, cfg):
    counts = {lab: len(re.findall(rf"\b{lab}\b", text)) for lab in EVIDENCE_LABELS}
    total = sum(counts.values())
    minimum = cfg.get("min_labels", 1)
    present = {k: v for k, v in counts.items() if v}
    if total >= minimum:
        return _result("labels_present", "PASS",
                       f"{total} evidence label(s) used.", json.dumps(present))
    return _result("labels_present", "FAIL",
                   f"{total} evidence label(s), expected at least {minimum}.")


def oracle_artifact_validates(_text, files, _cfg):
    """Any produced Lottie must survive the structural validator."""
    targets = [f for f in files if f.suffix.lower() in (".json", ".lottie")]
    if not targets:
        return _result("artifact_validates", "NOT_APPLICABLE", "The run produced no Lottie file.")
    failures = []
    for f in targets:
        proc = subprocess.run([sys.executable, str(VALIDATOR), str(f)],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            codes = sorted(set(re.findall(r"\b[A-Z][A-Z_]{4,}\b", proc.stdout)))
            failures.append(f"{f.name}: {', '.join(codes) or 'nonzero exit'}")
    if failures:
        return _result("artifact_validates", "FAIL",
                       f"{len(failures)} of {len(targets)} file(s) failed validation.",
                       "; ".join(failures))
    return _result("artifact_validates", "PASS",
                   f"All {len(targets)} produced file(s) pass structural validation.")


def oracle_produced_artifact(_text, files, _cfg):
    """For authoring work, delivering nothing is the worst outcome, not a non-result.

    This has to be a distinct oracle: artifact_validates reports NOT_APPLICABLE when
    there is no file, which would quietly exclude a total non-delivery from the pass
    rate instead of scoring it.
    """
    targets = [f for f in files if f.suffix.lower() in (".json", ".lottie")]
    if not targets:
        return _result("produced_artifact", "FAIL",
                       "No .json or .lottie file was produced. The task asked for one.")
    sizes = ", ".join(f"{f.name} ({f.stat().st_size}B)" for f in targets)
    return _result("produced_artifact", "PASS",
                   f"Produced {len(targets)} file(s).", sizes)


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _distinct_colors(doc):
    """Distinct solid fill/stroke colors, rounded so float noise doesn't inflate the count."""
    seen = set()
    for n in _walk(doc):
        if n.get("ty") in ("fl", "st") and isinstance(n.get("c"), dict):
            k = n["c"].get("k")
            if isinstance(k, list) and k and all(isinstance(x, (int, float)) for x in k):
                seen.add(tuple(round(float(x), 2) for x in k[:3]))
    return seen


def oracle_brief_conformance(_text, files, cfg):
    """Does the produced animation actually match the brief it was given?"""
    targets = [f for f in files if f.suffix.lower() == ".json"]
    if not targets:
        return _result("brief_conformance", "FAIL", "No Lottie JSON produced to check.")

    problems, notes = [], []
    for f in targets:
        try:
            doc = json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            problems.append(f"{f.name}: unparseable ({exc.__class__.__name__})")
            continue

        want_ms = cfg.get("expected_duration_ms")
        if want_ms:
            fr, ip, op = doc.get("fr"), doc.get("ip", 0), doc.get("op")
            if not fr or op is None:
                problems.append(f"{f.name}: no usable fr/op to derive duration")
            else:
                got_ms = (op - ip) / fr * 1000
                tol = cfg.get("duration_tolerance_ms", 150)
                notes.append(f"{got_ms:.0f}ms")
                if abs(got_ms - want_ms) > tol:
                    problems.append(f"{f.name}: {got_ms:.0f}ms vs brief {want_ms}ms (±{tol})")

        max_colors = cfg.get("max_colors")
        if max_colors:
            cols = _distinct_colors(doc)
            notes.append(f"{len(cols)} color(s)")
            if len(cols) > max_colors:
                problems.append(f"{f.name}: {len(cols)} distinct colors, brief allows {max_colors}")

        if cfg.get("require_transparent"):
            solids = [n for n in _walk(doc)
                      if n.get("ty") == 1 and isinstance(n.get("sw"), (int, float))]
            full = [n for n in solids
                    if n.get("sw", 0) >= doc.get("w", 0) and n.get("sh", 0) >= doc.get("h", 0)]
            if full:
                problems.append(f"{f.name}: {len(full)} full-canvas solid layer(s); brief wants transparency")

        layers = doc.get("layers")
        if not isinstance(layers, list) or not layers:
            problems.append(f"{f.name}: no layers, so nothing would draw")
        else:
            notes.append(f"{len(layers)} layer(s)")
            animated = any(
                isinstance(n, dict) and n.get("a") == 1 and isinstance(n.get("k"), list)
                for n in _walk(layers)
            )
            if not animated:
                problems.append(f"{f.name}: no animated property found; a static frame is not an animation")

    detail = "; ".join(problems) if problems else "Matches the brief on every checked dimension."
    return _result("brief_conformance", "FAIL" if problems else "PASS",
                   detail, "; ".join(notes))


def oracle_identifies_defect(text, _files, cfg):
    """For validation cases: did it name the defect the fixture actually has?"""
    expected = cfg.get("expected_defects", [])
    if not expected:
        return _result("identifies_defect", "NOT_APPLICABLE", "No expected defect declared.")
    low = text.lower()
    hit = [d for d in expected if d.lower() in low]
    if len(hit) == len(expected):
        return _result("identifies_defect", "PASS",
                       f"Named every expected defect: {', '.join(expected)}.")
    if hit:
        missed = [d for d in expected if d not in hit]
        return _result("identifies_defect", "FAIL",
                       f"Named {len(hit)}/{len(expected)}; missed: {', '.join(missed)}.",
                       ", ".join(hit))
    return _result("identifies_defect", "FAIL",
                   f"Named none of the expected defects: {', '.join(expected)}.")


def oracle_defers_to_discovery(text, _files, _cfg):
    """With no MCP connected, the only correct answer is 'discover it, I can't recall it'."""
    cues = [
        r"\bdiscover\b", r"\btools?/list\b", r"\bnot connected\b", r"\bconnect\b",
        r"\bcreator_docs\b", r"\blook (?:it )?up\b", r"\bcan(?:no|')t (?:confirm|verify)\b",
        r"\bdepends on (?:your )?(?:account|client)\b", r"\bavailab(?:le|ility)\b",
    ]
    hits = [p for p in cues if re.search(p, text, re.I)]
    if hits:
        return _result("defers_to_discovery", "PASS",
                       f"Deferred to live discovery ({len(hits)} cue(s)).", "; ".join(hits))
    return _result("defers_to_discovery", "FAIL",
                   "Answered without deferring to discovery or flagging unavailability.")


def oracle_size_reduced(_text, files, cfg):
    before = cfg.get("input_bytes")
    if not before:
        return _result("size_reduced", "NOT_APPLICABLE", "No input size declared.")
    targets = [f for f in files if f.suffix.lower() in (".json", ".lottie")]
    if not targets:
        return _result("size_reduced", "FAIL", "No output file produced to compare.")
    best = min(f.stat().st_size for f in targets)
    pct = (before - best) / before * 100
    target_pct = cfg.get("min_reduction_pct", 0)
    status = "PASS" if pct >= target_pct else "FAIL"
    return _result("size_reduced", status,
                   f"{before} -> {best} bytes ({pct:.1f}% smaller; target {target_pct}%).")


ORACLES = {
    "no_fabricated_tool": oracle_no_fabricated_tool,
    "no_unearned_universality": oracle_no_unearned_universality,
    "no_skip_as_pass": oracle_no_skip_as_pass,
    "versions_named": oracle_versions_named,
    "labels_present": oracle_labels_present,
    "artifact_validates": oracle_artifact_validates,
    "produced_artifact": oracle_produced_artifact,
    "brief_conformance": oracle_brief_conformance,
    "identifies_defect": oracle_identifies_defect,
    "defers_to_discovery": oracle_defers_to_discovery,
    "size_reduced": oracle_size_reduced,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="evals/cases/<name>")
    ap.add_argument("--run", required=True, help="a run directory")
    args = ap.parse_args()

    case_dir = pathlib.Path(args.case).resolve()
    run_dir = pathlib.Path(args.run).resolve()
    cfg = json.loads((case_dir / "case.json").read_text())

    out_txt = run_dir / "output.txt"
    text = out_txt.read_text(errors="replace") if out_txt.exists() else ""

    out_dir = run_dir / "outputs"
    files = sorted(p for p in out_dir.rglob("*") if p.is_file()) if out_dir.exists() else []

    usage = {}
    res_json = run_dir / "result.json"
    if res_json.exists():
        try:
            raw = json.loads(res_json.read_text())
            usage = {
                "duration_ms": raw.get("duration_ms"),
                "total_cost_usd": raw.get("total_cost_usd"),
                "num_turns": raw.get("num_turns"),
                "input_tokens": (raw.get("usage") or {}).get("input_tokens"),
                "output_tokens": (raw.get("usage") or {}).get("output_tokens"),
            }
        except json.JSONDecodeError:
            usage = {"error": "result.json did not parse"}

    checks = []
    for name in cfg.get("oracles", []):
        fn = ORACLES.get(name)
        if fn is None:
            checks.append(_result(name, "ERROR", "Unknown oracle name."))
            continue
        try:
            checks.append(fn(text, files, cfg))
        except Exception as exc:  # a broken grader must not look like a skill failure
            checks.append(_result(name, "ERROR", f"Grader raised: {exc}"))

    scored = [c for c in checks if c["status"] in ("PASS", "FAIL")]
    passed = sum(1 for c in scored if c["status"] == "PASS")
    grading = {
        "case": cfg.get("name", case_dir.name),
        "run": run_dir.name,
        "skill_triggered": (run_dir / "triggered").exists() or None,
        "checks": checks,
        "scored": len(scored),
        "passed": passed,
        "pass_rate": (passed / len(scored)) if scored else None,
        "needs_review": [c["name"] for c in checks if c["status"] == "REVIEW"],
        "usage": usage,
        "output_chars": len(text),
    }
    (run_dir / "grading.json").write_text(json.dumps(grading, indent=2) + "\n")

    flag = "" if not grading["needs_review"] else f"  review: {', '.join(grading['needs_review'])}"
    rate = "n/a" if grading["pass_rate"] is None else f"{grading['pass_rate']*100:.0f}%"
    print(f"{grading['case']:28} {run_dir.name:18} {passed}/{len(scored)} ({rate}){flag}")
    for c in checks:
        if c["status"] in ("FAIL", "ERROR", "REVIEW"):
            print(f"    [{c['status']}] {c['name']}: {c['detail']}")


if __name__ == "__main__":
    main()
