import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { FacebookClient } from "./client/facebook.js";
import { registerPageTools } from "./tools/pages.js";
import { registerPostTools } from "./tools/posts.js";
import { registerInsightTools } from "./tools/insights.js";
import { registerUserTools } from "./tools/users.js";

export function createServer(): McpServer {
  const accessToken = process.env.FACEBOOK_ACCESS_TOKEN;
  if (!accessToken) {
    throw new Error(
      "FACEBOOK_ACCESS_TOKEN environment variable is required. " +
        "Set it in your MCP client config or in a .env file.",
    );
  }

  const apiVersion = process.env.GRAPH_API_VERSION;
  const client = new FacebookClient(accessToken, apiVersion);

  const server = new McpServer({
    name: "facebook-graph",
    version: "1.0.0",
  });

  // Register all tool groups
  registerPageTools(server, client);
  registerPostTools(server, client);
  registerInsightTools(server, client);
  registerUserTools(server, client);

  return server;
}
