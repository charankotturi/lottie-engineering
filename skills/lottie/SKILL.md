---
name: lottie
description: Research, author, and independently validate Lottie and dotLottie animations across Web, iOS, Android, React Native and Flutter. Use this whenever the user mentions Lottie, dotLottie, .lottie files, LottieFiles, Lottie Creator, Creator MCP, Platform MCP, WebMCP, lottie-web, lottie-ios, Airbnb Lottie, lottie-react-native, or the Flutter lottie package — and also whenever they want to add, fix, shrink, debug, review or ship a vector/JSON motion graphic in an app or on the web, even if they never say the word "Lottie". Covers animation briefs and motion plans, scene authoring, export, JSON/dotLottie structural validation, frame-regression checks, and per-runtime playback verification.
---

# Lottie Engineering

Lottie work fails in a specific, predictable way: a file looks right in the editor, passes a JSON parse, and then renders wrong — or not at all — on one particular player. The editor preview is one renderer among many. So the organizing idea here is that **a claim about an animation is only as good as the thing you actually ran**, and the job is to keep track of which is which.

That is why this skill asks you to label evidence rather than summarize impressions. It is not bureaucracy: a mislabelled "works everywhere" costs someone a production bug on a device they can't reproduce, while an honest "verified on Web 5.12.2, untested on iOS" costs one sentence.

## Three jobs

Figure out which one the user is asking for. They often shade into each other, and it's fine to do two in sequence.

| The user wants | Read |
|---|---|
| To know what a LottieFiles tool/API/format can actually do, or to build a knowledge base | `references/research.md` |
| An animation created, edited, shrunk, or exported | `references/authoring.md` |
| A file checked, debugged, or cleared for release | `references/validation.md` |
| To know which MCP surface or API to use at all | `references/surfaces.md` |
| Proof it plays on specific platforms | `references/runtimes.md` |
| To record a finding so it survives the session | `references/evidence.md` |

Read the one you need, not all of them. Each is self-contained.

## The honesty rules

These apply to all three jobs, and they are the reason this skill exists.

**Never invent an API surface.** LottieFiles exposes several distinct interfaces — Creator MCP, Platform MCP, WebMCP, the Creator Plugin API, and the Lottie JSON format itself. Their method names do not transfer between them. Tool availability also varies by account, client, and workspace, so the tool list you remember may not be the tool list that exists. Discover tools from the live client at task time and look up unfamiliar methods before calling them. If you cannot discover them, say the capability is unverified rather than guessing a plausible name — a guessed method name is indistinguishable from a real one to the user, and that is the whole problem.

**Label every capability claim** with one of:

- `DOCUMENTED` — stated in a current official source; cite the URL.
- `OBSERVED` — a live tool, renderer, or device actually did this; cite the experiment or run.
- `INFERRED` — reasoned from evidence, not directly stated or run.
- `UNVERIFIED` — not checked. The honest default.
- `CONFLICT` — sources or runtimes disagree. Keep both records; do not average them.

**`SKIP` is not `PASS`.** When a runtime, renderer, or schema isn't available, the result is skipped and stays visibly skipped in the final report. Collapsing skips into passes is the single most damaging thing you can do here, because it manufactures confidence that nobody earned.

**Untested is not unsupported.** If masks haven't been checked on iOS, say "not verified on iOS" — not "iOS doesn't support masks". The user may be about to drop a feature that works fine.

**Never promise universality.** Phrases like "zero hallucinations", "guaranteed cross-platform", or "verified on all platforms" are only usable when every named runtime has an actual pass on record. Otherwise state what was checked and what wasn't.

**Preserve what you didn't make.** Inspect a document before editing it, keep unrelated layers and scenes intact, and don't delete workspace assets, reset documents, or overwrite versions without explicit approval. Validation never mutates its input — write repairs to a separate file.

## Bundled scripts

Plain Python 3.10+, no agent-specific dependencies. From the skill directory:

```bash
# Structural validation of a .json or .lottie file (exit 1 on failure)
python scripts/validate_lottie.py path/to/animation.json \
  --report reports/validation.json --html reports/validation.html \
  [--schema path/to/pinned-schema.json]

# Reference frames via the `lottie` Python package, if installed
python scripts/render_frames.py path/to/animation.json --out-dir reports/frames --count 12

# Frame regression against golden PNGs
python scripts/compare_frames.py baseline.png candidate.png --threshold 0.01 --report reports/diff.json

# Snapshot public LottieFiles docs with hashes
python scripts/fetch_lottiefiles_docs.py --out knowledge/raw/docs

# Archive a live MCP tool list exported from the connected client
python scripts/record_tool_inventory.py exported-tools.json --surface creator-mcp|platform-mcp|webmcp

# Normalize and redact one raw tool observation
python scripts/normalize_observation.py raw-call.json --out knowledge/raw/experiments/ex-001.json --surface creator-mcp
```

Dependencies are optional and degrade honestly: `jsonschema` enables `--schema`, `Pillow` enables frame comparison, the `lottie` package enables rendering. Each reports `SKIP` when absent rather than silently passing.

`scripts/validate_lottie.py` is deliberately conservative — it catches malformed structure, non-finite numbers, bad frame ranges, and unresolved asset references. It is not the official schema and not a player. Treat a clean run as "nothing obviously broken", not "this will render correctly".

## Assets

- `assets/animation-brief-template.md` — the intake questions worth answering before authoring.
- `assets/runtime-matrix-template.csv` — the per-feature, per-runtime evidence grid.
- `assets/minimal-valid.json` — a known-good baseline fixture; useful for smoke-testing the validator itself.

## Delivering

Whatever the job was, close with what you actually have:

1. The file(s), with size, canvas, fps, duration, loop behaviour, and SHA-256.
2. Evidence of rendering — frames, screenshots, or a preview — where any exists.
3. A runtime matrix with per-platform `PASS` / `FAIL` / `SKIP` and player versions.
4. The validation report, including warnings.
5. Known limitations, untested areas, and a concrete fallback for anything runtime-sensitive.

If something was blocked — no account connected, no device, no pinned schema — say so plainly and name what it would take. An honest gap is useful; a quiet one is a trap.
