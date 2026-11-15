# AGENTS.md

This repository ships one agent skill: **`lottie`**, at [`skills/lottie/SKILL.md`](skills/lottie/SKILL.md).

If you are an agent working in this repository, or in a project that has installed this skill, read that file before doing Lottie work. It routes to detailed references for research, authoring, validation, runtime verification, and evidence recording.

The format is plain Markdown with YAML frontmatter and plain Python 3 scripts — no dependency on any particular model or agent harness. Claude Code can install it as a plugin (see README); any other agent can read `skills/lottie/SKILL.md` directly.

## The short version of the rules

1. Never invent LottieFiles MCP tool names, arguments, methods, return fields, error codes, or capability limits. Discover tools from the live client at task time; availability is account- and client-dependent.
2. Look up unfamiliar Creator methods in the live documentation tool before calling them.
3. Creator MCP authors and exports. Platform MCP reads workspace metadata via GraphQL. WebMCP edits the open browser document. The Creator Plugin API is a separate surface. Their method names do not transfer.
4. Inspect before editing. Preserve scene content the user did not ask you to change. Name important layers descriptively.
5. Prefer native vector shapes and simple paths. Treat fonts, expressions, effects, audio, raster assets, masks, mattes, blend modes, and advanced path operations as runtime-sensitive until tested.
6. A successful editor preview or export is not evidence of cross-platform support. Validate the exported artifact, not the in-editor scene.
7. Label every capability claim `DOCUMENTED`, `OBSERVED`, `INFERRED`, `UNVERIFIED`, or `CONFLICT`, with a source URL or experiment ID and the date checked.
8. `SKIP` is never reported as `PASS`. Untested is never reported as unsupported. Never claim "zero hallucinations" or "guaranteed cross-platform".
9. Do not delete workspace assets, reset documents, or overwrite versions without explicit user approval.
10. Keep secrets, personal data, and private workspace content out of committed fixtures and knowledge records.
