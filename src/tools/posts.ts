import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { FacebookClient } from "../client/facebook.js";
import type {
  FacebookPost,
  GraphApiResponse,
} from "../types/facebook.js";

export function registerPostTools(
  server: McpServer,
  client: FacebookClient,
): void {
  // Get posts from a page or user feed
  server.tool(
    "get_posts",
    "Get posts from a Facebook page or user feed",
    {
      page_id: z
        .string()
        .optional()
        .describe("Page ID. Omit to use the authenticated user's feed"),
      limit: z
        .number()
        .min(1)
        .max(100)
        .optional()
        .describe("Number of posts to retrieve (default 25, max 100)"),
    },
    async ({ page_id, limit }) => {
      const target = page_id ?? "me";
      const params: Record<string, string> = {
        fields:
          "id,message,created_time,story,full_picture,permalink_url,type,shares,likes.summary(true),comments.summary(true)",
      };
      if (limit) params.limit = String(limit);

      const result = await client.get<GraphApiResponse<FacebookPost>>(
        `/${target}/feed`,
        params,
      );
      return {
        content: [{ type: "text", text: JSON.stringify(result.data, null, 2) }],
      };
    },
  );

  // Create a post on a page
  server.tool(
    "create_post",
    "Create a new post on a Facebook page",
    {
      page_id: z.string().describe("The Facebook page ID"),
      message: z.string().describe("The post message text"),
      link: z.string().optional().describe("An optional URL to attach"),
    },
    async ({ page_id, message, link }) => {
      const data: Record<string, string> = { message };
      if (link) data.link = link;

      const result = await client.post<{ id: string }>(
        `/${page_id}/feed`,
        data,
      );
      return {
        content: [
          { type: "text", text: `Post created successfully. ID: ${result.id}` },
        ],
      };
    },
  );

  // Delete a post
  server.tool(
    "delete_post",
    "Delete a Facebook post",
    { post_id: z.string().describe("The post ID to delete") },
    async ({ post_id }) => {
      await client.delete<{ success: boolean }>(`/${post_id}`);
      return {
        content: [
          { type: "text", text: `Post ${post_id} deleted successfully.` },
        ],
      };
    },
  );
}
