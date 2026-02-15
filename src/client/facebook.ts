import type { GraphApiError } from "../types/facebook.js";

const DEFAULT_API_VERSION = "v21.0";
const BASE_URL = "https://graph.facebook.com";

export class FacebookClient {
  private accessToken: string;
  private apiVersion: string;

  constructor(accessToken: string, apiVersion?: string) {
    this.accessToken = accessToken;
    this.apiVersion = apiVersion ?? DEFAULT_API_VERSION;
  }

  private get baseUrl(): string {
    return `${BASE_URL}/${this.apiVersion}`;
  }

  /**
   * Make a GET request to the Graph API.
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    url.searchParams.set("access_token", this.accessToken);
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        url.searchParams.set(key, value);
      }
    }

    const res = await fetch(url.toString());
    const body = await res.json();

    if (!res.ok) {
      const error = body as GraphApiError;
      throw new Error(
        `Graph API error (${error.error.code}): ${error.error.message}`,
      );
    }
    return body as T;
  }

  /**
   * Make a POST request to the Graph API.
   */
  async post<T>(
    endpoint: string,
    data: Record<string, string>,
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    url.searchParams.set("access_token", this.accessToken);

    const res = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const body = await res.json();

    if (!res.ok) {
      const error = body as GraphApiError;
      throw new Error(
        `Graph API error (${error.error.code}): ${error.error.message}`,
      );
    }
    return body as T;
  }

  /**
   * Make a DELETE request to the Graph API.
   */
  async delete<T>(endpoint: string): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    url.searchParams.set("access_token", this.accessToken);

    const res = await fetch(url.toString(), { method: "DELETE" });
    const body = await res.json();

    if (!res.ok) {
      const error = body as GraphApiError;
      throw new Error(
        `Graph API error (${error.error.code}): ${error.error.message}`,
      );
    }
    return body as T;
  }
}
