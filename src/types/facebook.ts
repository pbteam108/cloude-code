/** Facebook Graph API common types */

export interface GraphApiResponse<T> {
  data: T[];
  paging?: {
    cursors?: {
      before: string;
      after: string;
    };
    next?: string;
    previous?: string;
  };
}

export interface FacebookPage {
  id: string;
  name: string;
  category?: string;
  fan_count?: number;
  about?: string;
  website?: string;
  link?: string;
  access_token?: string;
}

export interface FacebookPost {
  id: string;
  message?: string;
  created_time: string;
  story?: string;
  full_picture?: string;
  permalink_url?: string;
  type?: string;
  shares?: { count: number };
  likes?: { summary: { total_count: number } };
  comments?: { summary: { total_count: number } };
}

export interface FacebookInsight {
  id: string;
  name: string;
  period: string;
  title: string;
  description: string;
  values: Array<{
    value: number | Record<string, number>;
    end_time: string;
  }>;
}

export interface FacebookUser {
  id: string;
  name: string;
  email?: string;
  picture?: {
    data: {
      url: string;
      width: number;
      height: number;
    };
  };
}

export interface GraphApiError {
  error: {
    message: string;
    type: string;
    code: number;
    fbtrace_id: string;
  };
}
