# Lottie Engineering System — Implementation Plan

This plan is the project roadmap. It distinguishes work already scaffolded from work that still requires a connected LottieFiles account, live MCP tools, or platform runtimes.

## Project objective

Build an evidence-backed Lottie engineering system that can research LottieFiles, create maintainable animations, and independently validate exported Lottie/dotLottie files across Web, iOS, Android, React Native, and Flutter.

The system must reduce unsupported assumptions by grounding rules in official documentation, live tool schemas, recorded experiments, exported artifacts, and runtime tests. It must never claim zero hallucinations or universal compatibility.

## Operating principles

1. **Evidence before rules:** every capability or limitation must be labelled `DOCUMENTED`, `OBSERVED`, `INFERRED`, `UNVERIFIED`, or `CONFLICT`.
2. **Separate product surfaces:** Creator MCP, Platform MCP, WebMCP, Creator Plugin API, Lottie JSON, and dotLottie are distinct surfaces. Never conflate their APIs.
3. **Capture raw outputs:** preserve redacted raw tool inputs, outputs, warnings, errors, export files, checksums, and renderer/runtime versions.
4. **Safe experimentation:** use a dedicated scratch workspace/document. Read first; mutate only the scratch asset. Require user approval for destructive or externally visible actions.
5. **Independent validation:** Creator preview is not proof of successful export or cross-player compatibility.
6. **Reproducibility:** pin schemas, player versions, renderer versions, operating systems, and test fixtures wherever practical.
7. **Honest reporting:** `SKIP` and `UNVERIFIED` are never silently treated as `PASS`.

## Current baseline

The repository currently includes:
- One consolidated agent skill, `lottie` (v0.0.0), routing to six references: surfaces, research, authoring, validation, runtimes, evidence. It replaces the earlier researcher/engineer/validator split, which had overlapping descriptions and ambiguous triggering.
- A Claude Code plugin manifest and single-plugin marketplace, plus `AGENTS.md` as the harness-agnostic entry point. The skill carries no model- or agent-specific dependency.
- Public documentation snapshot helper.
- MCP tool-inventory recorder for tool lists exported by a connected client.
- Tool observation normalizer with basic secret redaction.
- Conservative Lottie JSON and dotLottie structural validator.
- Optional frame-render and PNG comparison helpers.
- Brief, runtime-matrix and delivery-manifest templates, a known-good fixture, and five passing validator tests.

Scripts and assets live inside `skills/lottie/` so the skill is self-contained and installable on its own.

Also not yet completed — and the reason the version is 0.0.0:
- Evidence that this technique works. The premise is that forcing live tool discovery, evidence labelling and separated validation levels produces better Lottie outcomes than an agent answering from memory. That premise is `UNVERIFIED` by the skill's own standard.

Not yet completed:
- Authenticated live discovery of all Creator MCP, Platform MCP, and WebMCP tools.
- Complete capture of live input schemas and output/error contracts.
- Full Creator API and Platform GraphQL documentation extraction.
- Controlled capability experiments against a real LottieFiles account.
- A pinned, provenance-tracked official schema bundle.
- End-to-end exports and playback tests on every target runtime.
- CI workflow and a versioned compatibility database.

## Roadmap

### Phase A — Internal review round (current)

**Goal:** gather real usage evidence for the skill itself before investing in Phases 1-7.

This runs before, and partly in place of, synthetic evaluation. Teammates using the skill on work they would have done anyway produce more honest signal than test prompts written by its author, because they have no stake in it passing.

Tasks:
- [x] Publish v0.0.0 as an installable plugin.
- [ ] Get it installed by teammates doing real Lottie work.
- [ ] Collect per-use reports: did it trigger unprompted; did routing stay to roughly one reference; what did it state that proved false; where was it pointlessly cautious; what wasted time; did the deliverable ship.
- [ ] Keep raw transcripts, not just summaries — the interesting failures are usually mid-session, not in the final answer.
- [ ] Log every fabricated tool name, method or limit as a defect against the discovery rules in `references/surfaces.md`.
- [ ] Log every case of over-hedging as a defect against the labelling rules in `SKILL.md`.
- [ ] Record which of the three jobs (research / authoring / validation) people actually reach for; deprioritize the rest.

Deliverables:
- Issues or notes per reported use, with transcripts.
- A revised `SKILL.md` description if triggering misses.
- A pruned skill: anything that consistently wasted reviewers' time gets cut rather than kept for completeness.

Exit criteria:
- At least a handful of independent real uses recorded.
- The over-trigger and under-trigger cases are both known, not assumed.
- Version moves off 0.0.0 only when feedback supports the premise, and the changelog says what the evidence was.

Risks to watch:
- Reviewers may report that the honesty discipline slows them down on simple tasks. That is real signal, not noise — the fix is likely a shorter path for small requests, not more insistence.
- Author-run evaluation after this point should use the reviewers' actual prompts, not invented ones.

### Phase 0 — Environment and access

**Goal:** make the research environment reproducible and safe.

Tasks:
- [ ] Install Node.js 20+, Python 3.10+, Git, and project dependencies.
- [ ] Connect Creator MCP and Platform MCP in the chosen agent client.
- [ ] Open Lottie Creator in a supported browser and enable WebMCP if available.
- [ ] Confirm account/workspace permissions and conditional tool availability.
- [ ] Create a dedicated scratch project/document and a separate test workspace if possible.
- [ ] Record agent client, MCP server, browser, OS, and date/version information.
- [ ] Confirm no production assets or private data are used in fixtures.

Deliverables:
- `knowledge/verified/environment.md`
- Redacted MCP connection/tool availability record.
- Scratch workspace/document identifier (store privately; do not commit secrets).

Exit criteria:
- All three surfaces have been checked for availability.
- Read-only inspection works.
- Scratch document can be created and safely reset.

### Phase 1 — Documentation and tool-contract extraction

**Goal:** capture what the official docs say and what the connected tools actually expose.

Tasks:
- [ ] Fetch public docs and machine-readable catalogs with `scripts/fetch_lottiefiles_docs.py`.
- [ ] Export and record Creator MCP `tools/list`.
- [ ] Export and record Platform MCP `tools/list`.
- [ ] Export and record WebMCP tool list from the live Creator page.
- [ ] Capture exact JSON input schemas, descriptions, annotations, optional fields, enums, and availability conditions.
- [ ] Query Creator documentation for every exposed tool and relevant API method.
- [ ] Inspect Platform MCP operation catalog, schema search, and schema details.
- [ ] Capture GraphQL query/mutation input/output contracts and permission requirements.
- [ ] Record differences between Creator MCP JavaScript API and Creator Plugin API.
- [ ] Record undocumented or ambiguous areas as open questions rather than guessing.

Deliverables:
- `knowledge/raw/docs/`
- `knowledge/raw/*-tool-inventory.json`
- `knowledge/verified/tool-inventory.md`
- `knowledge/verified/api-contracts/`
- `knowledge/verified/open-questions.md`

Exit criteria:
- Every tool currently exposed by the user's connected client has a schema record.
- Conditional/unavailable tools are explicitly recorded.
- Creator, Platform, and WebMCP are separated.
- Every extracted rule has a source URL or a recorded observation.

### Phase 2 — Capability matrix and controlled experiments

**Goal:** establish real tool behaviour, constraints, errors, and export fidelity.

Create a test matrix covering, where supported:
- Document lifecycle and scene/composition management.
- Layer creation, deletion, duplication, ordering, parenting, and transforms.
- Vector primitives: rectangles, ellipses, stars, paths, fills, strokes.
- Shape groups, trim paths, repeaters, merge paths, and modifiers.
- Position, scale, rotation, opacity, path, and color keyframes.
- Easing, holds, interpolation, markers, segments, and looping.
- Text, fonts, glyphs, and fallback behaviour.
- Gradients, masks, mattes, blend modes, shadows, blur, and effects.
- Images, imported media, external assets, and embedded assets.
- Precompositions, time remapping, 3D, expressions, and audio where exposed.
- Preview, rendering, export, download, workspace save/load, and versioning.
- Platform workspace operations and GraphQL read/write behaviours.
- WebMCP operations against the open Creator document.

For each supported capability:
- [ ] Record preconditions and the exact tool/method call.
- [ ] Capture successful input and raw output.
- [ ] Capture warnings and export diagnostics.
- [ ] Export the artifact and record SHA-256.
- [ ] Render representative frames.
- [ ] Test safe negative cases: missing argument, wrong type, invalid enum, nonexistent ID, unsupported property, invalid frame range, missing media reference.
- [ ] Record actual error response and recovery steps.
- [ ] Repeat with a clean document to rule out state leakage.
- [ ] Mark evidence status and confidence.

Deliverables:
- `knowledge/experiments/*.json`
- `knowledge/raw/experiments/`
- `knowledge/verified/capability-matrix.csv`
- `knowledge/verified/errors-and-recovery.md`
- `knowledge/verified/validation-rules.json`

Exit criteria:
- Every claimed capability has documentation or a reproducible observation.
- Every tested error has a raw redacted example.
- Unavailable and untested capabilities remain `UNVERIFIED`.
- No destructive or production actions were performed.

### Phase 3 — Specification and format knowledge

**Goal:** establish a versioned format reference and portability rules.

Tasks:
- [ ] Identify the authoritative Lottie specification revision.
- [ ] Pin the exact repository tag/commit used.
- [ ] Import relevant schemas/spec documents with license and attribution.
- [ ] Record schema URL, commit/tag, retrieval date, and SHA-256.
- [ ] Test schema against real Creator exports and known-good fixtures.
- [ ] Document Lottie JSON versus dotLottie packaging and manifest rules.
- [ ] Build a feature/property matrix for the format and each player.
- [ ] Separate format-level support from player implementation support.
- [ ] Add explicit compatibility notes for assets, fonts, effects, masks, mattes, expressions, and advanced shape features.

Deliverables:
- `schemas/` pinned schema/spec material and provenance.
- `knowledge/verified/lottie-format.md`
- `knowledge/verified/dotlottie-format.md`
- `knowledge/verified/feature-compatibility.csv`

Exit criteria:
- No partial or hand-written schema is mislabelled as the complete official schema.
- Every compatibility statement identifies the format/player/version and evidence.

### Phase 4 — Engineering workflow and reusable patterns

**Goal:** make animation creation consistent and maintainable.

Tasks:
- [ ] Define animation brief template and acceptance criteria.
- [ ] Create reusable patterns for common UI motion (success, error, loading, progress, toggle, notification, empty state).
- [ ] Store source scene/project when possible alongside exported Lottie.
- [ ] Add naming conventions, layer hygiene, timing/easing guidance, and size budgets.
- [ ] Document safe fallbacks for runtime-sensitive effects.
- [ ] Build prompt-to-motion-plan workflow before authoring.
- [ ] Require inspect-before-edit and preview-before-export.
- [ ] Require a delivery manifest with file checksum and runtime status.

Deliverables:
- `examples/patterns/`
- `knowledge/verified/authoring-guidelines.md`
- `knowledge/verified/fallback-catalog.md`
- `templates/delivery-manifest.json`

Exit criteria:
- Each reusable pattern has a source, exported file, preview, validation report, and tested runtime list.
- Engineer skill uses only verified methods or explicitly flags unknowns.

### Phase 5 — Independent validation and renderer adapters

**Goal:** turn validation into a repeatable release gate.

Tasks:
- [ ] Pin and test the official schema validator.
- [ ] Improve JSON checks for keyframes, layer types, transforms, assets, and nested compositions.
- [ ] Complete dotLottie manifest validation against the pinned specification.
- [ ] Add asset extraction/reference checks.
- [ ] Choose and pin at least one independent renderer.
- [ ] Implement deterministic frame extraction for representative timestamps.
- [ ] Save golden frames for selected fixtures.
- [ ] Add configurable pixel/perceptual diff thresholds.
- [ ] Add report generation with PASS/FAIL/WARN/SKIP.
- [ ] Keep source files immutable during validation; write repairs to a separate output.

Deliverables:
- `scripts/validate_lottie.py`
- `scripts/render_frames.py`
- `scripts/compare_frames.py`
- `reports/`
- Expanded unit and integration tests.

Exit criteria:
- Known-good and known-bad fixtures produce expected results.
- Renderer versions are pinned.
- Skipped runtime checks remain visibly skipped.
- Reports include checksums and tool versions.

### Phase 6 — Cross-platform runtime verification

**Goal:** prove playback on the platforms the user actually targets.

Runtime matrix:
- Web: selected Lottie Web or dotLottie player and pinned version.
- iOS: selected Lottie iOS or dotLottie player and pinned version.
- Android: selected Airbnb Lottie Android / Compose integration or dotLottie Android and pinned version.
- React Native: selected player and pinned version.
- Flutter: selected player and pinned version.

Tasks:
- [ ] Create a minimal fixture app/project for each runtime.
- [ ] Load the same exported artifacts.
- [ ] Test initial, middle, final, and loop-seam frames.
- [ ] Test play, pause, speed, segment, marker, and repeat behaviour where required.
- [ ] Check fonts, image assets, transparency, scaling, clipping, and device density.
- [ ] Record platform, OS, player version, device/browser, and test result.
- [ ] Compare screenshots/frames in a pinned environment.
- [ ] Document runtime-specific fallbacks.

Deliverables:
- `runtime-tests/web/`
- `runtime-tests/ios/`
- `runtime-tests/android/`
- `runtime-tests/react-native/`
- `runtime-tests/flutter/`
- `knowledge/verified/runtime-compatibility.csv`

Exit criteria:
- Every requested target has an explicit PASS/FAIL/SKIP result.
- "All-platforms verified" is only used when all named runtimes pass.

### Phase 7 — Continuous integration and knowledge maintenance

**Goal:** prevent regressions and detect upstream changes.

Tasks:
- [ ] Add CI for unit tests, schema checks, fixture validation, and frame regression.
- [ ] Run docs/tool inventory diff when manually refreshed or on a scheduled cadence.
- [ ] Alert on tool schema changes, removed methods, changed enum values, or new tool availability.
- [ ] Keep old snapshots and compare changes instead of overwriting raw evidence.
- [ ] Re-run relevant experiments after upstream API changes.
- [ ] Version the knowledge base and publish a changelog.
- [ ] Add a review process for evidence status changes.

Deliverables:
- `.github/workflows/lottie-validation.yml`
- `knowledge/changelog.md`
- `knowledge/verified/api-drift-report.md`

Exit criteria:
- CI catches fixture regressions.
- Upstream changes create reviewable diffs.
- No automated process silently upgrades an unverified claim to verified.

## Suggested execution order

Do not attempt all phases in one large agent context. Execute in small batches:

1. Phase A (internal review of the skill itself) — in progress; its feedback reorders everything below.
2. Phase 0 and Phase 1 (access and discovery).
3. Phase 2 by capability family, one family per research session.
4. Phase 3 (pin format/schema knowledge).
5. Phase 5 baseline validator hardening.
6. Phase 6 runtime smoke tests, beginning with the user's primary platform.
7. Phase 4 pattern library using only validated features.
8. Phase 7 CI and drift monitoring.

## Definition of done

The system is ready for production use when:
- all live tool contracts are archived;
- the capability matrix is evidence-backed;
- the official schema/spec revision is pinned;
- the validator has known-good and known-bad fixtures;
- reusable patterns have export and runtime evidence;
- each requested platform has a versioned compatibility report;
- the skills consistently distinguish documented, observed, inferred, conflicting, and unverified claims;
- the delivery process reports limitations rather than guessing.
