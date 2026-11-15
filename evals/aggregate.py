#!/usr/bin/env python3
"""Aggregate a run matrix into per-arm numbers, with honest error bars.

Prints a table and writes benchmark.json / benchmark.md into the run directory.

The statistics are deliberately plain: mean, sample standard deviation, and a
delta. With the handful of repetitions this harness is meant for, anything
fancier would imply a precision the sample size cannot support - so the report
says outright when a delta is inside the noise instead of ranking it.
"""
import json
import pathlib
import statistics
import sys

ARMS = ["with_skill", "without_skill"]


def mean_sd(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None, None, 0
    if len(vals) == 1:
        return vals[0], 0.0, 1
    return statistics.mean(vals), statistics.stdev(vals), len(vals)


def fmt(mean, sd, unit="", digits=1):
    if mean is None:
        return "n/a"
    if sd is None or sd == 0:
        return f"{mean:.{digits}f}{unit}"
    return f"{mean:.{digits}f}{unit} ± {sd:.{digits}f}"


def collect(run_root):
    data = {}
    for case_dir in sorted(p for p in run_root.iterdir() if p.is_dir()):
        for arm in ARMS:
            arm_dir = case_dir / arm
            if not arm_dir.is_dir():
                continue
            for rep in sorted(arm_dir.iterdir()):
                g = rep / "grading.json"
                if not g.exists():
                    continue
                try:
                    grading = json.loads(g.read_text())
                except json.JSONDecodeError:
                    continue
                res = {}
                rj = rep / "result.json"
                if rj.exists():
                    try:
                        res = json.loads(rj.read_text())
                    except json.JSONDecodeError:
                        pass
                data.setdefault(case_dir.name, {}).setdefault(arm, []).append(
                    {"grading": grading, "result": res}
                )
    return data


def arm_stats(runs):
    rates = [r["grading"].get("pass_rate") for r in runs]
    durations = [(r["result"].get("duration_ms") or 0) / 1000 or None for r in runs]
    costs = [r["result"].get("total_cost_usd") for r in runs]
    out_toks = [(r["result"].get("usage") or {}).get("output_tokens") for r in runs]
    triggered = [bool(r["result"].get("skill_triggered")) for r in runs]
    reviews = sum(len(r["grading"].get("needs_review") or []) for r in runs)

    # Per-oracle outcome, so a single check that always passes is visible as
    # non-discriminating rather than hidden inside an average.
    per_check = {}
    for r in runs:
        for c in r["grading"].get("checks", []):
            per_check.setdefault(c["name"], []).append(c["status"])

    return {
        "n": len(runs),
        "pass_rate": mean_sd(rates),
        "duration_s": mean_sd(durations),
        "cost_usd": mean_sd(costs),
        "output_tokens": mean_sd(out_toks),
        "trigger_rate": (sum(triggered) / len(triggered)) if triggered else None,
        "needs_review": reviews,
        "per_check": per_check,
    }


def main():
    if len(sys.argv) < 2:
        print("usage: aggregate.py <results/run-dir>", file=sys.stderr)
        sys.exit(2)
    run_root = pathlib.Path(sys.argv[1]).resolve()
    data = collect(run_root)
    if not data:
        print(f"no graded runs under {run_root}", file=sys.stderr)
        sys.exit(1)

    report = {"run": run_root.name, "cases": {}, "notes": []}
    lines = [f"# Benchmark — {run_root.name}", ""]

    print(f"{'case':26} {'arm':14} {'n':>2}  {'pass rate':>14}  {'secs':>13}  {'trigger':>7}")
    print("-" * 86)

    all_deltas = []
    for case, arms in data.items():
        report["cases"][case] = {}
        lines += [f"## {case}", "", "| arm | n | pass rate | seconds | output tokens | trigger |",
                  "|---|---|---|---|---|---|"]
        for arm in ARMS:
            runs = arms.get(arm) or []
            if not runs:
                continue
            s = arm_stats(runs)
            report["cases"][case][arm] = {
                "n": s["n"],
                "pass_rate_mean": s["pass_rate"][0],
                "pass_rate_sd": s["pass_rate"][1],
                "duration_s_mean": s["duration_s"][0],
                "cost_usd_mean": s["cost_usd"][0],
                "output_tokens_mean": s["output_tokens"][0],
                "trigger_rate": s["trigger_rate"],
                "needs_review": s["needs_review"],
                "per_check": s["per_check"],
            }
            pr = s["pass_rate"]
            rate_txt = "n/a" if pr[0] is None else fmt(pr[0] * 100, (pr[1] or 0) * 100, "%", 0)
            trig = "n/a" if s["trigger_rate"] is None else f"{s['trigger_rate']*100:.0f}%"
            print(f"{case:26} {arm:14} {s['n']:>2}  {rate_txt:>14}  "
                  f"{fmt(s['duration_s'][0], s['duration_s'][1], 's'):>13}  {trig:>7}")
            lines.append(
                f"| {arm} | {s['n']} | {rate_txt} | {fmt(s['duration_s'][0], s['duration_s'][1], 's')} "
                f"| {fmt(s['output_tokens'][0], s['output_tokens'][1], '', 0)} | {trig} |"
            )

        w = report["cases"][case].get("with_skill")
        o = report["cases"][case].get("without_skill")
        if w and o and w["pass_rate_mean"] is not None and o["pass_rate_mean"] is not None:
            delta = (w["pass_rate_mean"] - o["pass_rate_mean"]) * 100
            noise = ((w["pass_rate_sd"] or 0) + (o["pass_rate_sd"] or 0)) * 100
            verdict = "inside the noise" if abs(delta) <= noise else "exceeds spread"
            report["cases"][case]["delta_pp"] = round(delta, 1)
            report["cases"][case]["delta_verdict"] = verdict
            all_deltas.append(delta)
            print(f"{'':26} {'delta':14}    {delta:+.0f}pp  ({verdict})")
            lines += ["", f"**Delta: {delta:+.1f} percentage points** — {verdict}.", ""]
        else:
            lines.append("")

    # Non-discriminating checks: identical outcome in both arms everywhere.
    flat = {}
    for case, arms in report["cases"].items():
        for arm in ARMS:
            for name, statuses in (arms.get(arm) or {}).get("per_check", {}).items():
                flat.setdefault(name, {}).setdefault(arm, []).extend(statuses)
    for name, arms in flat.items():
        w, o = set(arms.get("with_skill", [])), set(arms.get("without_skill", []))
        if w and o and w == o and len(w) == 1:
            report["notes"].append(
                f"'{name}' returned {next(iter(w))} in both arms everywhere — it is not "
                f"discriminating, so it measures neither arm. Tighten it or drop it."
            )

    if all_deltas:
        report["notes"].append(
            f"Mean delta across cases: {statistics.mean(all_deltas):+.1f}pp over "
            f"{len(all_deltas)} case(s). With this few repetitions, treat any delta "
            f"inside the combined spread as unproven rather than small."
        )
    total_reviews = sum((arms.get(a) or {}).get("needs_review", 0)
                        for arms in report["cases"].values() for a in ARMS)
    if total_reviews:
        report["notes"].append(
            f"{total_reviews} check(s) returned REVIEW and are excluded from pass rates. "
            f"They need human adjudication before the numbers are complete."
        )

    (run_root / "benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
    lines += ["## Notes", ""] + [f"- {n}" for n in report["notes"]] + [""]
    (run_root / "benchmark.md").write_text("\n".join(lines))

    print()
    for n in report["notes"]:
        print(f"note: {n}")
    print(f"\nwrote {run_root/'benchmark.json'} and benchmark.md")


if __name__ == "__main__":
    main()
