# CLAUDE.md — Facebook Graph MCP Server

## Project Overview

MCP (Model Context Protocol) server that exposes Facebook Graph API operations as tools for AI assistants. Built with TypeScript and the official MCP SDK.

## Tech Stack

- **Runtime:** Node.js (ES2022, ESM)
- **Language:** TypeScript 5.x (strict mode)
- **MCP SDK:** `@modelcontextprotocol/sdk`
- **Validation:** Zod
- **Transport:** stdio (standard MCP transport)

## Project Structure

```
src/
├── index.ts              # Entry point — starts stdio transport
├── server.ts             # Creates McpServer, registers all tools
├── client/
│   └── facebook.ts       # FacebookClient — thin wrapper around Graph API (GET/POST/DELETE)
├── tools/
│   ├── pages.ts          # get_pages, get_page
│   ├── posts.ts          # get_posts, create_post, delete_post
│   ├── insights.ts       # get_page_insights, get_post_insights
│   └── users.ts          # get_me, get_user
└── types/
    └── facebook.ts       # Shared TypeScript interfaces for Graph API responses
```

## Commands

```bash
npm install          # Install dependencies
npm run build        # Compile TypeScript → dist/
npm run dev          # Run with tsx (no build needed)
npm start            # Run compiled output (requires build first)
npm run lint         # Type-check without emitting
npm run clean        # Remove dist/
```

## Architecture & Conventions

- **Tool registration pattern:** Each file in `src/tools/` exports a `register*Tools(server, client)` function that binds tools to the MCP server. Add new tools by creating a new file and calling the register function in `server.ts`.
- **FacebookClient:** All Graph API calls go through `src/client/facebook.ts`. It handles URL construction, auth token injection, and error mapping. Do not call `fetch()` directly from tool files.
- **Error handling:** Graph API errors are thrown as `Error` with the API error message. The MCP SDK surfaces these to the caller.
- **Environment variables:**
  - `FACEBOOK_ACCESS_TOKEN` (required) — Graph API access token
  - `GRAPH_API_VERSION` (optional) — defaults to `v21.0`

## Adding a New Tool

1. Create or edit a file in `src/tools/`.
2. Define the tool with `server.tool(name, description, zodSchema, handler)`.
3. Use `client.get()` / `client.post()` / `client.delete()` for API calls.
4. Register in `src/server.ts` if it's a new file.

## MCP Client Configuration

Add to your Claude Desktop or MCP client config:

```json
{
  "mcpServers": {
    "facebook-graph": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/path/to/this/repo",
      "env": {
        "FACEBOOK_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```

## Important Notes

- Never commit `.env` or real access tokens.
- The server uses stdio transport — it reads/writes JSON-RPC on stdin/stdout. Diagnostic logs go to stderr.
- All imports use `.js` extensions (required for Node16 module resolution with ESM).
