# Schemas and provenance

Do not label a hand-written or partial schema as the official Lottie schema.

To add a schema:
1. Download the schema from the current authoritative Lottie format/specification repository.
2. Preserve its license and attribution.
3. Record source URL, git commit/tag, download date, and SHA-256 in `schema-provenance.json`.
4. Run schema validation against known-good fixtures and real exported files.
5. Keep schema checks optional until the schema version is pinned and tested.

The validator includes conservative baseline checks even when no schema is configured.
