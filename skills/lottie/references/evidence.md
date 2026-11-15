# Recording evidence

Knowledge that lives only in a chat transcript evaporates. These formats exist so a finding survives into the next session and can be re-checked when LottieFiles changes something upstream.

## Labels

- `DOCUMENTED` — stated in a current official source. Needs a URL.
- `OBSERVED` — a live tool, renderer, or device did this. Needs an experiment ID or run reference.
- `INFERRED` — reasoned from evidence, not directly stated or run.
- `UNVERIFIED` — not checked. The correct default for anything you haven't run.
- `CONFLICT` — sources or runtimes disagree. Keep both records; don't resolve by preference.

Every record carries `checked_at`, a source URL or experiment ID, client/server/runtime versions where known, and a confidence note. A promotion from `UNVERIFIED` to `OBSERVED` happens only when a real observation is attached — never because a claim has been repeated often enough.

## Where things go

- `knowledge/raw/` — immutable: tool inventories, raw requests and responses, docs snapshots, export artifacts, logs. Append, never overwrite, so upstream changes show up as reviewable diffs.
- `knowledge/verified/` — curated, reviewed summaries: capability matrix, validation rules, runtime results, open questions.
- `knowledge/experiments/` — one JSON record per controlled experiment.

Never commit OAuth tokens, signed download URLs, personal workspace content, private assets, or credentials. `scripts/normalize_observation.py` redacts common secret shapes, but it is a safety net, not a substitute for looking before you commit.

## Experiment record

```json
{
  "id": "creator-path-keyframes-001",
  "title": "Animate a Bézier path",
  "surface": "creator-mcp",
  "status": "OBSERVED",
  "checked_at": "YYYY-MM-DD",
  "client": "name/version",
  "server": "reported version or unknown",
  "preconditions": ["dedicated scratch document"],
  "tool_calls": [],
  "outputs": [],
  "warnings": [],
  "errors": [],
  "export": { "format": "json", "sha256": "…" },
  "render_checks": [],
  "conclusion": "…",
  "limitations": ["…"]
}
```

Never place a fabricated response in an observation record — a plausible invented payload contaminates the knowledge base permanently, because later readers cannot tell it apart from a real one. If a tool wasn't available, record `NOT_AVAILABLE` with the client context.

## Evidence record

For a single capability claim, matching `knowledge/evidence-record.schema.json`:

```json
{
  "id": "mask-support-ios",
  "status": "UNVERIFIED",
  "checked_at": "YYYY-MM-DD",
  "surface": "lottie-ios",
  "claim": "Alpha masks render correctly on lottie-ios 4.x",
  "source_url": null,
  "experiment_id": null,
  "runtime_versions": {},
  "notes": ["No iOS fixture project available yet."]
}
```

## Delivery manifest

Ship alongside a deliverable so the receiving developer knows what was actually checked:

```json
{
  "artifact": "success-check.json",
  "sha256": "…",
  "bytes": 0,
  "canvas": { "w": 512, "h": 512 },
  "fps": 30,
  "duration_frames": 60,
  "loop": false,
  "assets": [],
  "validation_report": "reports/validation.json",
  "runtimes": [
    { "platform": "web", "player": "lottie-web", "version": "…", "result": "PASS" },
    { "platform": "ios", "player": "lottie-ios", "version": null, "result": "SKIP" }
  ],
  "portability_tier": "RUNTIME_SPECIFIC",
  "limitations": ["…"]
}
```
