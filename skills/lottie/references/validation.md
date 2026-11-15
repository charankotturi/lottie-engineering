# Validation

Purpose: catch malformed files, unsupported constructs, broken asset references, rendering defects, and runtime-specific incompatibilities before a user ships them.

The core discipline is that these are **separate levels of confidence, reported separately**. A file can be perfectly valid JSON and still render as a blank rectangle on one player. Rolling the levels into a single "valid ✅" destroys exactly the information the user needs.

## Levels

Report each independently. Passing one implies nothing about the next.

1. **Syntax / archive integrity** — JSON parses, or the `.lottie` ZIP opens.
2. **Baseline structural validation** — the conservative checks below.
3. **Official schema validation** — only when a pinned schema is configured. Otherwise `SKIP`.
4. **Asset and reference integrity** — every referenced asset resolves.
5. **Renderer smoke test** — an independent renderer produces frames.
6. **Visual regression** — frames match golden images within threshold.
7. **Target runtime playback** — see `runtimes.md`.

## Statuses

- `PASS` — this check ran and passed.
- `FAIL` — this check ran and found a defect.
- `WARN` — suspicious, or only partly verified.
- `SKIP` — the required tool, schema, or runtime was unavailable.
- `NOT_APPLICABLE` — the check doesn't apply to this file.

The final summary must never collapse `SKIP` into `PASS`. If four of seven levels were skipped, the headline is "3 levels checked, 4 skipped", not "passed".

## Running the bundled validator

```bash
python scripts/validate_lottie.py path/to/animation.json \
  --report reports/validation.json \
  --html reports/validation.html \
  [--schema path/to/pinned-schema.json]
```

Exits non-zero on failure, so it works as a release gate in CI. It accepts both `.json` and `.lottie`.

## Lottie JSON checks

- Root object present with expected metadata (`v`, `fr`, `ip`, `op`, `w`, `h`, `layers`).
- All numbers finite — no `NaN`, no `Infinity`.
- Positive canvas dimensions; frame rate greater than zero.
- Valid in/out frame range (`op` strictly greater than `ip`).
- Layer collection present and layer objects well-shaped.
- Asset identifiers resolve; external asset paths exist on disk.
- Keyframe arrays have sane time/value shapes.
- Flag suspiciously large payloads and excessive layer or keyframe counts — these are the usual cause of mobile jank, and worth a `WARN` even when structurally legal.

Unknown fields are warnings, not failures, unless an authoritative schema says otherwise. The format evolves and players tolerate extras; failing on them produces false alarms.

The bundled script is intentionally conservative and is not the official schema or a player. A clean run means "nothing obviously broken".

## dotLottie checks

- ZIP integrity.
- `manifest.json` exists and parses.
- Every animation file the manifest references exists in the archive.
- Every referenced asset exists.
- Each contained Lottie JSON validates independently.

Don't assume you know every optional manifest field — compare against the current dotLottie specification and mark anything unrecognized as a warning with a note, rather than asserting it's invalid.

## Schema validation

Only claim schema validation when a schema is actually pinned. Record its source URL, git tag or commit, retrieval date, and SHA-256 before using it. A hand-written or partial schema must never be presented as the official one — that misrepresents the strength of the check. With nothing pinned, level 3 is `SKIP`.

## Frame regression

```bash
python scripts/render_frames.py animation.json --out-dir reports/frames --count 12
python scripts/compare_frames.py golden/frame-006.png reports/frames/frame-006.png \
  --threshold 0.01 --report reports/diff-006.json
```

Render the same frame indices with a pinned renderer and version, compare against committed golden PNGs, and record the metric alongside the raw diff. Pixel-tight thresholds are only meaningful inside a pinned environment — across renderers, OS versions, or font stacks, antialiasing and text layout differ legitimately, so a tight threshold produces noise instead of signal.

## Rules

- Never modify the source file. Write any repair to a separate output and show the user the diff.
- Never silently repair. Offer the patch; let them choose.
- Never classify an untested runtime as a pass.
- Always include tool versions, the file's checksum, warnings, and the limitations of what you ran.
- Treat an editor preview as one renderer's opinion, not proof of cross-player behaviour.

## Release checklist

- [ ] Input checksum recorded.
- [ ] Syntax / ZIP integrity passes.
- [ ] Structural validation passes.
- [ ] Schema version and provenance recorded, if a schema was used.
- [ ] External assets resolve.
- [ ] Editor and export warnings reviewed.
- [ ] Export completed and artifact actually downloaded.
- [ ] Renderer smoke test completed.
- [ ] Start / middle / end / loop-seam frames inspected.
- [ ] Each in-scope runtime tested with player version recorded.
- [ ] Regression comparison run in a pinned environment.
- [ ] Known limitations and skipped checks disclosed in the report.
