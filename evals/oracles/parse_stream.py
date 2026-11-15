#!/usr/bin/env python3
"""Turn a stream-json transcript into the three artifacts the graders read.

Writes, into the run directory:
  output.txt   the model's final text
  result.json  usage, duration, cost, turn count
  triggered    present only if the lottie skill actually fired

The trigger marker is the only honest way to measure activation: the treatment
arm is handed the skill via --plugin-dir but never told to use it, so whether it
fired is a real signal rather than a given.
"""
import argparse
import json
import pathlib

SKILL_MARKERS = ("lottie-engineering:lottie", "lottie-engineering", "skills/lottie/SKILL.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--exit-code", type=int, default=0)
    args = ap.parse_args()

    run = pathlib.Path(args.run)
    stream = run / "stream.jsonl"
    events = []
    if stream.exists():
        for line in stream.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    final_text, result_meta = "", {}
    triggered = False
    skill_reads = 0

    for ev in events:
        if ev.get("type") == "result":
            final_text = ev.get("result") or final_text
            result_meta = {
                "exit_code": args.exit_code,
                "is_error": ev.get("is_error"),
                "subtype": ev.get("subtype"),
                "duration_ms": ev.get("duration_ms"),
                "num_turns": ev.get("num_turns"),
                "total_cost_usd": ev.get("total_cost_usd"),
                "usage": ev.get("usage") or {},
            }
        # Tool uses appear as content blocks on assistant messages.
        msg = ev.get("message") or {}
        for block in (msg.get("content") or []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                blob = json.dumps({"name": block.get("name"), "input": block.get("input")})
                if block.get("name") == "Skill" and any(m in blob for m in SKILL_MARKERS):
                    triggered = True
                if any(m in blob for m in SKILL_MARKERS):
                    skill_reads += 1
            elif block.get("type") == "text" and not final_text:
                final_text = block.get("text", "")

    if not result_meta:
        result_meta = {"exit_code": args.exit_code, "note": "no result event in stream"}
    result_meta["skill_triggered"] = triggered
    result_meta["skill_file_touches"] = skill_reads
    result_meta["events"] = len(events)

    (run / "output.txt").write_text(final_text or "")
    (run / "result.json").write_text(json.dumps(result_meta, indent=2) + "\n")
    marker = run / "triggered"
    if triggered:
        marker.write_text("1\n")
    elif marker.exists():
        marker.unlink()


if __name__ == "__main__":
    main()
