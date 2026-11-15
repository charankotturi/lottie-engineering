# Knowledge store

Create these directories as extraction runs:
- `raw/`: immutable MCP tool inventories, schemas, raw requests/responses, docs snapshots, export artifacts, logs.
- `verified/`: reviewed summaries, capability matrix, validation rules, runtime results.
- `experiments/`: one JSON record per controlled experiment.

Do not commit OAuth tokens, signed download URLs, personal workspace data, private assets, or credentials. Redact them before committing.
