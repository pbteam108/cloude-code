import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { FacebookClient } from "../client/facebook.js";
import type { FacebookUser } from "../types/facebook.js";

export function registerUserTools(
  server: McpServer,
  client: FacebookClient,
): void {
  // Get the authenticated user's profile
  server.tool(
    "get_me",
    "Get the authenticated Facebook user's profile",
    {},
    async () => {
      const result = await client.get<FacebookUser>("/me", {
        fields: "id,name,email,picture",
      });
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    },
  );

  // Get any user's public profile
  server.tool(
    "get_user",
    "Get a Facebook user's public profile by ID",
    { user_id: z.string().describe("The user ID") },
    async ({ user_id }) => {
      const result = await client.get<FacebookUser>(`/${user_id}`, {
        fields: "id,name,picture",
      });
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    },
  );
}
