# Lottie Engineering

A portable agent skill for researching LottieFiles, authoring Lottie/dotLottie animations, and independently validating them across Web, iOS, Android, React Native and Flutter.

The skill is plain Markdown plus plain Python 3 — no dependency on any specific model or agent harness. Claude Code installs it as a plugin; other agents can read [`skills/lottie/SKILL.md`](skills/lottie/SKILL.md) directly, or pick it up via [`AGENTS.md`](AGENTS.md).

## Status: v0.0.0 — internal review round

This is a first internal release, published for teammates to install and use on real Lottie work. Nothing here has been validated at scale yet.

The thing under review is **the technique**, not just the text: does making an agent discover tools live, label evidence, and report validation levels separately actually produce better Lottie outcomes than letting it answer from memory? That claim is currently `UNVERIFIED` by the skill's own standard, and the version number says so deliberately. It moves off 0.0.0 when team feedback and recorded runs support it.

### What reviewers should report

Install it, use it on a task you'd have done anyway, and note:

1. **Did it trigger?** Did the skill activate on its own, or did you have to ask for it by name? Paste the prompt you used either way — triggering is controlled solely by the description in `SKILL.md`, so real phrasings are the only way to tune it.
2. **Did the routing hold?** It should read `SKILL.md` plus roughly one reference file. If it pulled in several, or read the wrong one, say which task caused it.
3. **Where was it wrong or invented?** Especially any LottieFiles tool name, method, argument or limit it stated that turned out not to exist. These are the highest-value reports — the whole design targets exactly this failure.
4. **Where was it pointlessly cautious?** Labelling everything `UNVERIFIED` and refusing to commit is its own failure mode. If it hedged where a plain answer was warranted, that is a bug.
5. **What did it make you do that wasted time?** Steps that produced nothing useful should be cut, not kept for completeness.
6. **The outcome.** Did the animation ship? Did validation catch something real, or miss something that broke on a device?

File these as issues on this repository, or send them to me directly. Raw transcripts are more useful than summaries.

## Why it exists

Lottie breaks in a specific way: a file looks right in the editor, parses as valid JSON, and then renders wrong — or not at all — on one particular player. The editor preview is one renderer among many, and each runtime is a separate implementation with its own coverage and bugs.

So this skill is organized around one idea: **a claim about an animation is only as good as the thing you actually ran.** It makes an agent label every capability claim as `DOCUMENTED`, `OBSERVED`, `INFERRED`, `UNVERIFIED` or `CONFLICT`, report each validation level separately, and keep `SKIP` visibly distinct from `PASS`. An honest "verified on lottie-web 5.12.2, untested on iOS" costs one sentence; a mislabelled "works everywhere" costs someone a production bug on a device they can't reproduce.

It also refuses to invent API surfaces. LottieFiles exposes Creator MCP, Platform MCP, WebMCP, the Creator Plugin API and the Lottie format as distinct interfaces whose method names don't transfer, and tool availability varies by account and client — so tools get discovered live rather than recalled.

## Install

### Claude Code (plugin)

From a shell:

```bash
claude plugin marketplace add charankotturi/lottie-engineering
claude plugin install lottie-engineering@lottie-engineering
```

Or, from inside Claude Code's own prompt (not a shell — `/plugin` is a slash command, and a shell will just report `no such file or directory`):

```
/plugin marketplace add charankotturi/lottie-engineering
```

Restart your session afterwards for the skill to load. To confirm it's there and see what it costs you:

```bash
claude plugin details lottie-engineering
```

It adds roughly 180 tokens to every session and about 1.5k when the skill actually fires; reference files load only when a task needs them.

Teammates: install it and use it normally. See **Status** above for what to report back.

### Any agent (manual)

Copy `skills/lottie/` into wherever your tool reads skills or instruction files — for Claude Code that's `~/.claude/skills/lottie/`; for other harnesses, point your rules/context file at `skills/lottie/SKILL.md`.

## What's in the skill

```text
skills/lottie/
├── SKILL.md                  # router + the honesty rules
├── references/
│   ├── surfaces.md           # Creator MCP vs Platform MCP vs WebMCP vs Plugin API; official sources
│   ├── research.md           # live tool discovery, docs capture, controlled experiments
│   ├── authoring.md          # intake, motion plan, portability tiers, export
│   ├── validation.md         # 7 validation levels, checks, dotLottie, regression
│   ├── runtimes.md           # per-platform verification and fallbacks
│   └── evidence.md           # labels, experiment/evidence/manifest formats
├── scripts/                  # validation, rendering, docs capture, observation recording
└── assets/                   # brief template, runtime matrix, delivery manifest, known-good fixture
```

The agent reads `SKILL.md` and then only the one reference it needs, which keeps context cost low.

## Scripts

Python 3.10+. Optional dependencies degrade honestly — each reports `SKIP` when absent rather than silently passing.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # jsonschema (schema validation), Pillow (frame diffs)
```

```bash
# Structural validation of .json or .lottie — exits non-zero on failure, so it works as a CI gate
python skills/lottie/scripts/validate_lottie.py skills/lottie/assets/minimal-valid.json \
  --report reports/validation.json --html reports/validation.html

# Reference frames (needs the `lottie` Python package)
python skills/lottie/scripts/render_frames.py animation.json --out-dir reports/frames --count 12

# Frame regression against golden PNGs
python skills/lottie/scripts/compare_frames.py golden.png candidate.png --threshold 0.01

# Snapshot public LottieFiles docs with hashes
python skills/lottie/scripts/fetch_lottiefiles_docs.py --out knowledge/raw/docs

# Archive a live MCP tool list exported from your connected client
python skills/lottie/scripts/record_tool_inventory.py exported-tools.json --surface creator-mcp

# Normalize and redact one raw tool observation
python skills/lottie/scripts/normalize_observation.py raw-call.json \
  --out knowledge/raw/experiments/ex-001.json --surface creator-mcp
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## Honesty boundary

This repository has **not** queried an authenticated LottieFiles account or run live Creator MCP experiments. The scripts are built to capture that evidence once you connect the MCP servers yourself:

- Creator MCP: `https://creator.mcp.lottiefiles.com/mcp`
- Platform MCP: `https://mcp.lottiefiles.com/mcp`
- WebMCP: runs in a supported browser on the Lottie Creator page

`record_tool_inventory.py` archives a tool list you export from your own client; it does not bypass OAuth or call private endpoints. The bundled validator is deliberately conservative — it is not the official schema and not a player. `schemas/schema-provenance.json` records that no official schema is pinned yet, by design, rather than shipping a hand-written one labelled as official.

See [`PLAN.md`](PLAN.md) for the phased roadmap from this baseline to a fully evidence-backed system.

## License

MIT — see [LICENSE](LICENSE).

## Updating

Re-run documentation and tool-inventory capture after LottieFiles API changes, or monthly. Keep `knowledge/raw/` immutable and append — upstream changes should surface as reviewable diffs, never silent rewrites. Promote a claim from `UNVERIFIED` only when a real observation is attached.
