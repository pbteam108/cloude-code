import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { FacebookClient } from "../client/facebook.js";
import type {
  FacebookInsight,
  GraphApiResponse,
} from "../types/facebook.js";

export function registerInsightTools(
  server: McpServer,
  client: FacebookClient,
): void {
  // Get page insights / analytics
  server.tool(
    "get_page_insights",
    "Get analytics insights for a Facebook page",
    {
      page_id: z.string().describe("The Facebook page ID"),
      metric: z
        .string()
        .optional()
        .describe(
          "Comma-separated metrics (e.g. page_impressions,page_engaged_users). Defaults to common metrics",
        ),
      period: z
        .enum(["day", "week", "days_28"])
        .optional()
        .describe("Aggregation period (default: day)"),
    },
    async ({ page_id, metric, period }) => {
      const params: Record<string, string> = {
        metric:
          metric ??
          "page_impressions,page_engaged_users,page_fan_adds,page_views_total",
        period: period ?? "day",
      };

      const result = await client.get<GraphApiResponse<FacebookInsight>>(
        `/${page_id}/insights`,
        params,
      );
      return {
        content: [{ type: "text", text: JSON.stringify(result.data, null, 2) }],
      };
    },
  );

  // Get post-level insights
  server.tool(
    "get_post_insights",
    "Get analytics insights for a specific post",
    {
      post_id: z.string().describe("The post ID"),
      metric: z
        .string()
        .optional()
        .describe(
          "Comma-separated metrics. Defaults to post_impressions,post_engaged_users,post_clicks",
        ),
    },
    async ({ post_id, metric }) => {
      const params: Record<string, string> = {
        metric:
          metric ??
          "post_impressions,post_engaged_users,post_clicks",
      };

      const result = await client.get<GraphApiResponse<FacebookInsight>>(
        `/${post_id}/insights`,
        params,
      );
      return {
        content: [{ type: "text", text: JSON.stringify(result.data, null, 2) }],
      };
    },
  );
}
