# Runtime verification

A Lottie file does not have one behaviour — it has one per player. Each runtime is a separate implementation with its own feature coverage and its own bugs, so "it works" is only meaningful with a platform and a version attached.

Record for every target: platform, OS version, player library, exact player version, device or browser, and the result. Without the version, a pass is unreproducible and expires silently when someone upgrades.

## Players by platform

| Platform | Common players |
|---|---|
| Web | `lottie-web`, `@dotlottie/player-component`, `dotlottie-web` |
| iOS | `lottie-ios`, dotLottie iOS |
| Android | Airbnb `lottie-android` (View or Compose integration), dotLottie Android |
| React Native | `lottie-react-native`, dotLottie React Native |
| Flutter | `lottie` package, dotLottie Flutter |

For Android specifically, record which integration is in use — plain View, Compose, or dotLottie — because their coverage and APIs differ, and a Compose-only issue is a real and common class of bug.

## What to test

Per runtime, load the exact exported artifact — not the editor document, and not a re-export.

**Frames:** initial, middle, final, and the loop seam. The seam is where most looping animations visibly break.

**Playback**, where the brief requires it: play, pause, speed, segment/marker playback, repeat behaviour.

**Rendering:** fonts and glyph fallback, image assets, transparency, scaling behaviour, clipping at bounds, and device pixel density. Text and raster assets are the most frequent source of per-platform divergence, so check them first when something looks wrong on exactly one platform.

## Recording results

Use `assets/runtime-matrix-template.csv`:

```
feature,format,creator_preview,web,ios,android,react_native,flutter,evidence_status,player_version,os_version,notes
```

One row per feature, one `PASS` / `FAIL` / `SKIP` per platform. A platform with no fixture app is `SKIP`, never blank and never assumed.

Keep format-level support distinct from player-level support. "The Lottie format supports this" and "lottie-ios 4.5 renders this" are different claims, and conflating them is how users end up shipping a feature that's spec-legal and visually broken.

## Minimum honest answer

If no fixture app exists for a platform, the correct output is: every in-scope runtime listed, the ones you actually ran marked with results and versions, and the rest marked `SKIP` with one line on what would unblock them — usually "needs a minimal fixture project on that platform".

Only use "verified on all target platforms" when every named platform has a recorded pass. Until then, name the gap.

## Fallbacks

When a feature is unsupported or unverified on a target, offer a concrete substitute rather than just flagging the risk:

- Text layer → pre-converted outlines/shapes, or native platform text composited over the animation.
- Expressions → baked keyframes.
- Complex gradient → stepped gradient, or a flat fill at the same perceived value.
- Mask or matte → pre-trimmed geometry, or a shape-based clip.
- Blur / shadow → baked raster at the needed densities, or drop the effect and compensate with contrast.
- Blend mode → a flattened equivalent at the authored opacity.
- Time remapping → an explicitly keyframed timeline.
- Raster asset → native vector shapes, when the artwork allows.
