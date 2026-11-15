# Authoring and exporting

Goal: an animation that is maintainable, legible at its real display size, light enough for the budget, and portable to the runtimes the user actually ships on. Prefer fidelity and portability over cleverness — a clever construction that only renders in one player is a liability someone else will inherit.

## 1. Intake

Establish these before authoring. `assets/animation-brief-template.md` is the fill-in version.

- Purpose, and a visual reference if one exists.
- Canvas dimensions and aspect ratio.
- Frame rate and duration.
- Loop or one-shot.
- Background: transparent or filled.
- Target platforms, with exact player versions if known.
- Interaction needs: play, pause, speed, segments, markers.
- Asset and font licensing/availability.
- Size and performance budget.
- Whether an existing document must be preserved.

Ask only about gaps that would materially change the result. If the brief is workable, pick sensible defaults and state them — stalling on questions the user doesn't care about wastes their turn.

## 2. Inspect before editing

Read the document's structure first: scenes, compositions, layers, assets, fonts, markers, current duration. Then preserve everything unrelated to the request. Users rarely expect "add a checkmark" to restructure their file, and an unexpected overwrite is much more expensive than a slightly slower edit.

Give new layers stable, role-describing names — `icon-check`, `ring-progress`, `label-success`. Names are the only handle a developer has when wiring up segments or debugging a layer that won't show.

## 3. Write a motion plan first

A few sentences, before touching the scene:

- initial state
- anticipation, if it earns its place
- primary action
- settle or overshoot
- final state
- loop transition, if looping
- timing and easing per beat

This exists because keyframe-by-keyframe improvisation produces animations that are hard to adjust later. A small number of intentional keyframes beats a dense pile of them; use holds for deliberate pauses, not as padding.

## 4. Author with verified methods

- Look up unfamiliar methods in the live documentation tool before calling them (see `surfaces.md`).
- Use documented signatures and argument types exactly.
- Prefer native vector primitives and simple paths.
- Reuse an existing verified pattern where one fits.
- Keep geometry and transforms logically separated.
- Use explicit scene dimensions and a consistent coordinate system.
- Avoid unnecessary nested compositions and high path-point counts — they cost size and render time on mobile.

## 5. Portability tiers

Classify each feature you use, and tell the user which tier the deliverable sits in:

- `PORTABLE_BASELINE` — verified in the format and in every requested runtime.
- `RUNTIME_SPECIFIC` — supported only on named runtimes.
- `CREATOR_ONLY` — works in the editor but not confirmed in exported Lottie.
- `UNVERIFIED` — insufficient evidence.

Treat these as runtime-sensitive until tested, because they are where cross-player divergence concentrates: text and font/glyph fallback; expressions and procedural effects; complex gradients; masks, mattes and blend modes; blur, shadows, filters and layer effects; time remapping; animated paths and shape modifiers (trim paths, repeaters, merge paths); embedded or raster assets; audio; 3D layers and cameras; vendor extensions.

Being cautious is not the same as declaring them broken. "Not verified for your target" is the accurate phrasing.

## 6. Preview and refine

Preview the whole animation, then look specifically at the start, midpoint, end, and any transition or loop-seam frame. Check clipping, alignment, layer order, visual hierarchy, easing feel, and contrast. Read editor and export warnings rather than dismissing them.

Fix locally. Rewriting a whole document to correct one layer loses work and introduces new risk.

## 7. Export

- Export the format actually requested: Lottie JSON, or dotLottie when assets/packaging warrant it.
- Video or GIF export says nothing about Lottie compatibility — don't let one stand in for the other.
- Confirm the export job completed and the file is genuinely retrievable. Never state that a save succeeded, or produce a download URL, without a real tool result; a fabricated link is worse than an error message.
- Record size, dimensions, frame rate, duration, asset dependencies, and SHA-256.

## 8. Hand off to validation

Export is not verification. Run `references/validation.md` on the artifact, and `references/runtimes.md` for the platforms in scope.

## Defaults worth having

Unless the brief says otherwise: transparent background for UI assets; short, purposeful timing; eased rather than linear motion for UI transitions; seamless loops only when asked for or clearly useful; simple geometry and a limited palette; readable at actual display size. 30fps is a reasonable general-purpose UI default where it suits the target.

These are conventions, not format requirements — say so if a user asks why.
