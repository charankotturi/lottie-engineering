# LottieFiles surfaces and official sources

The most common source of fabricated Lottie advice is treating these as one API. They are not. A method that exists on one surface usually does not exist on the others, and the Creator Plugin API in particular is frequently mistaken for the Creator MCP JavaScript API because both are "the Creator API".

## Which surface does what

| Surface | Purpose | Acts on |
|---|---|---|
| **Creator MCP** | Author, inspect, preview, render and export scenes conversationally | A document on the hosted service |
| **Platform MCP** | Workspace/project/animation metadata via a GraphQL workbench | Account and workspace data |
| **WebMCP** | Edit the document currently open in Lottie Creator | The live browser editor session |
| **Creator Plugin API** | Build plugins that run inside Creator | A separate, independently documented surface |
| **Lottie JSON / dotLottie** | The portable file format and its ZIP packaging | Exported artifacts |

Endpoints, when the user is connecting a client:

- Creator MCP: `https://creator.mcp.lottiefiles.com/mcp`
- Platform MCP: `https://mcp.lottiefiles.com/mcp`
- WebMCP: runs in a supported browser on the Lottie Creator page. It is not a substitute for hosted Creator MCP.

Choosing between them: authoring and export go through Creator MCP; finding and organizing existing workspace content goes through Platform MCP; nudging a document the user already has open goes through WebMCP. Do not claim one surface can do another's job without evidence that it can.

## Tool families to expect

These are the documented families, useful for orientation — **not** a substitute for discovering the live list, since availability depends on account, client, storage, upload permissions, workspace connection, and MCP Apps support.

Creator MCP: `creator_exec`, `creator_docs`, `creator_document`, `creator_download_file`, `creator_delete_file`, `creator_import_media`, `creator_generate_media`, `creator_account`, `creator_save_to_workspace`, `creator_open_in_creator`, `creator_load_from_workspace`, `creator_preview`.

`creator_exec` runs against a JavaScript API whose current shape you discover via `creator_docs`. Look up a method's signature and examples there before calling it; do not substitute Plugin API documentation.

Platform MCP: `operations_list`, `schema_search`, `schema_details` (all read-only discovery) and `graphql_execute` (live, potentially mutating). Use read-only discovery first. Require explicit user approval before any mutation that creates, updates, deletes, publishes, or shares workspace resources.

## Official sources

Checked 2026-11-15. Online docs change — re-check before relying on specifics, and record the date you checked.

- Creator MCP overview: https://docs.lottiefiles.com/en/creator-mcp
- Creator MCP reference: https://docs.lottiefiles.com/en/creator-mcp/reference
- Creator MCP features, limitations and tools: https://help.lottiefiles.com/creator-mcp/creator-mcp-features-limitations-and-tools
- Creator MCP connection guide: https://help.lottiefiles.com/creator-mcp/connect-your-mcp-client
- Platform MCP: https://docs.lottiefiles.com/en/platform/mcp
- Platform MCP tools: https://docs.lottiefiles.com/en/platform/mcp/tools
- Which MCP to use: https://docs.lottiefiles.com/en/developers/which-mcp
- WebMCP: https://docs.lottiefiles.com/en/creator/13_ai-tools/lottie-creator-webmcp
- Creator Plugin API: https://docs.lottiefiles.com/en/creator-api
- Lottie format specification: https://github.com/lottie/lottie-spec
- Airbnb Lottie: https://github.com/airbnb/lottie
- dotLottie: https://dotlottie.io/

Machine-readable indexes worth checking (treat a 404 as "unavailable", never as grounds to invent contents):

- `https://docs.lottiefiles.com/llms.txt`
- `https://docs.lottiefiles.com/openapi.json`
- `https://docs.lottiefiles.com/.well-known/mcp/server-card.json`
- `https://docs.lottiefiles.com/.well-known/agent-skills/index.json`
