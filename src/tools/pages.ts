import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { FacebookClient } from "../client/facebook.js";
import type {
  FacebookPage,
  GraphApiResponse,
} from "../types/facebook.js";

export function registerPageTools(
  server: McpServer,
  client: FacebookClient,
): void {
  // Get pages managed by the authenticated user
  server.tool(
    "get_pages",
    "Get Facebook pages managed by the authenticated user",
    {},
    async () => {
      const result = await client.get<GraphApiResponse<FacebookPage>>(
        "/me/accounts",
        { fields: "id,name,category,fan_count,about,website,link,access_token" },
      );
      return {
        content: [{ type: "text", text: JSON.stringify(result.data, null, 2) }],
      };
    },
  );

  // Get details of a specific page
  server.tool(
    "get_page",
    "Get details of a specific Facebook page",
    { page_id: z.string().describe("The Facebook page ID") },
    async ({ page_id }) => {
      const result = await client.get<FacebookPage>(
        `/${page_id}`,
        { fields: "id,name,category,fan_count,about,website,link" },
      );
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    },
  );
}
