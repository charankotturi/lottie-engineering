# Research

Goal: a versioned, evidence-backed knowledge base about what LottieFiles tools and the Lottie format actually do — not a plausible summary. The output is facts with sources attached, and explicitly listed unknowns.

The failure mode this guards against is specific: an agent asked "can Creator MCP animate a trim path?" produces a confident, well-formatted, entirely invented answer, because the shape of the question invites one. The antidote is to only ever report what a source said or a tool returned.

## Order of work

### 1. Discover live surfaces first

Before reading documentation, list the tools the active client actually exposes. Availability is account-, client-, and workspace-dependent, so the live list is the ground truth and the docs are the explanation.

Record per tool: exact identifier, description, full JSON input schema, which fields are optional, enum values, annotations, and any availability condition. Keep Creator MCP, Platform MCP, and WebMCP separate — see `surfaces.md` for why conflating them is the most common error here.

Archive the exported list:

```bash
python scripts/record_tool_inventory.py exported-tools.json --surface creator-mcp
```

A tool that isn't exposed is recorded as `NOT_AVAILABLE` with the client context, not omitted and not assumed absent in general.

### 2. Read the official docs

The source registry is in `surfaces.md`. Snapshot them with hashes so later changes are visible as diffs rather than silent rewrites:

```bash
python scripts/fetch_lottiefiles_docs.py --out knowledge/raw/docs
```

Check the machine-readable indexes listed in `surfaces.md` too. A 404 means unavailable — record that and move on.

### 3. Query the in-tool documentation

For Creator MCP, use the documentation tool for every exposed tool and every API method you intend to use, and capture the returned signatures and examples verbatim. For Platform MCP, walk the read-only operation catalog, schema search, and schema details, then capture GraphQL query/mutation input and output contracts plus required permissions.

Record, per Platform operation: risk classification, permissions, argument shape, result shape, and whether it mutates account or workspace state.

### 4. Run controlled experiments

One capability per experiment, in a dedicated scratch document — never a production document. Start with read-only inspection, then a minimal new document.

Capture the exact call, its input, the raw output, warnings, errors, the exported file with its SHA-256, and rendered frames. Then repeat on a clean document to rule out state leakage: a result that depended on leftover state is a trap for whoever reads the record later.

Test negative cases one at a time, and keep them safe and reversible: missing required argument, wrong primitive type, invalid enum value, nonexistent layer or document ID, unsupported property name, out-of-range frame value, export before the document is ready, unavailable media reference. Record the real error response and the recovery that worked.

Do not fuzz the service, attempt to bypass access controls, or run destructive operations. Mutations that create, update, delete, publish, or share workspace resources need explicit user approval first.

### 5. Curate

Normalize and redact raw observations before committing:

```bash
python scripts/normalize_observation.py raw-call.json \
  --out knowledge/raw/experiments/ex-001.json --surface creator-mcp
```

Raw material stays immutable in `knowledge/raw/`; reviewed findings go in `knowledge/verified/`. Formats and labels are in `evidence.md`. Where docs and observation disagree, mark `CONFLICT` and keep both — the disagreement is itself a finding, and averaging it away loses the only useful signal.

## Capability matrix

Build coverage by family, one family per session rather than all at once — a single sprawling context produces shallow records for everything:

- document lifecycle, scenes and compositions
- layer create/delete/duplicate/order/parent/transform
- vector primitives: rectangle, ellipse, star, path, fill, stroke
- groups, trim paths, repeaters, merge paths, modifiers
- keyframes: position, scale, rotation, opacity, path, color
- easing, holds, interpolation, markers, segments, looping
- text, fonts, glyphs, fallback behaviour
- gradients, masks, mattes, blend modes, shadows, blur, effects
- images, imported and external media, embedded assets
- precompositions, time remapping, 3D, expressions, audio
- preview, render, export, download, workspace save/load, versioning
- Platform workspace operations and GraphQL read/write
- WebMCP operations against the open document

## Outputs

- `knowledge/raw/docs/` — hashed documentation snapshots
- `knowledge/raw/*-tool-inventory.json` — live tool lists per surface
- `knowledge/raw/experiments/` — normalized raw observations
- `knowledge/verified/tool-inventory.md` — curated, per-surface
- `knowledge/verified/capability-matrix.csv` — capability × evidence status
- `knowledge/verified/errors-and-recovery.md` — real error examples and fixes
- `knowledge/verified/runtime-compatibility.csv` — see `runtimes.md`
- `knowledge/verified/open-questions.md` — what remains unknown

## Done means

- Every currently exposed tool has its exact schema captured.
- Availability conditions are recorded per tool.
- Creator, Platform, and WebMCP records are separate.
- Documented capabilities are distinguishable from observed ones.
- Error behaviour includes real, redacted raw examples.
- Unresolved items are listed explicitly rather than quietly dropped.

The open-questions list is a deliverable, not an admission of failure. An empty one after a short session is a sign the research invented answers.
