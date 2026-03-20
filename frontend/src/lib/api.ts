import type { Review, ReviewDetail, ReviewListResponse } from "@/types/review";
import type { WorldModel, WorldModelDetail, PhysicsEvent } from "@/types/world-model";
import type { AgentOrg, AgentPost } from "@/types/community";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  reviews: {
    create: (prUrl: string, config?: Record<string, unknown>) =>
      fetchAPI<Review>("/api/reviews", {
        method: "POST",
        body: JSON.stringify({ pr_url: prUrl, config: config || {} }),
      }),

    list: (params?: { status?: string; repo?: string; limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set("status", params.status);
      if (params?.repo) searchParams.set("repo", params.repo);
      if (params?.limit != null) searchParams.set("limit", String(params.limit));
      if (params?.offset != null) searchParams.set("offset", String(params.offset));
      const query = searchParams.toString();
      return fetchAPI<ReviewListResponse>(`/api/reviews${query ? `?${query}` : ""}`);
    },

    get: (id: string) => fetchAPI<ReviewDetail>(`/api/reviews/${id}`),

    cancel: (id: string) =>
      fetchAPI<void>(`/api/reviews/${id}`, { method: "DELETE" }),

    postToGithub: (id: string, severityThreshold: string = "low") =>
      fetchAPI<{ posted: number; message: string }>(
        `/api/reviews/${id}/post-to-github?severity_threshold=${severityThreshold}`,
        { method: "POST" }
      ),
  },

  stats: {
    queue: () => fetchAPI<{ active: number; max_concurrent: number; available: number }>("/api/stats/queue"),
    overview: () => fetchAPI<{
      reviews_by_status: Record<string, number>;
      total_cost_usd: number;
      findings_by_severity: Record<string, number>;
      avg_issues_per_review: number;
      queue: { active: number; max_concurrent: number };
    }>("/api/stats/overview"),
  },

  worldModels: {
    create: (data: { name: string; description?: string; model_type?: string; mujoco_xml?: string }) =>
      fetchAPI<WorldModel>("/api/world-models", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    list: () => fetchAPI<{ items: WorldModel[]; total: number }>("/api/world-models").then(r => r.items),

    get: (id: string) => fetchAPI<WorldModelDetail>(`/api/world-models/${id}`),

    start: (id: string, maxSteps = 100) =>
      fetchAPI<{ status: string }>(`/api/world-models/${id}/start?max_steps=${maxSteps}`, {
        method: "POST",
      }),

    pause: (id: string) =>
      fetchAPI<{ status: string }>(`/api/world-models/${id}/pause`, { method: "POST" }),

    step: (id: string) =>
      fetchAPI<PhysicsEvent>(`/api/world-models/${id}/step`, { method: "POST" }),

    reset: (id: string) =>
      fetchAPI<{ status: string }>(`/api/world-models/${id}/reset`, { method: "POST" }),

    events: (id: string, limit = 50) =>
      fetchAPI<PhysicsEvent[]>(`/api/world-models/${id}/events?limit=${limit}`),

    delete: (id: string) =>
      fetchAPI<void>(`/api/world-models/${id}`, { method: "DELETE" }),
  },

  community: {
    orgs: {
      create: (data: { name: string; description?: string; topology?: Record<string, unknown> }) =>
        fetchAPI<AgentOrg>("/api/orgs", {
          method: "POST",
          body: JSON.stringify(data),
        }),

      list: (params?: { is_template?: boolean }) => {
        const q = params?.is_template != null ? `?is_template=${params.is_template}` : "";
        return fetchAPI<{ items: AgentOrg[]; total: number }>(`/api/orgs${q}`).then(r => r.items);
      },

      get: (id: string) => fetchAPI<AgentOrg>(`/api/orgs/${id}`),

      fork: (id: string) =>
        fetchAPI<AgentOrg>(`/api/orgs/${id}/fork`, { method: "POST" }),

      follow: (id: string) =>
        fetchAPI<void>(`/api/orgs/${id}/follow`, { method: "POST" }),

      unfollow: (id: string) =>
        fetchAPI<void>(`/api/orgs/${id}/follow`, { method: "DELETE" }),
    },

    feed: {
      list: (limit = 50) => fetchAPI<{ items: AgentPost[]; total: number }>(`/api/feed?limit=${limit}`).then(r => r.items),

      orgFeed: (orgId: string) => fetchAPI<{ items: AgentPost[]; total: number }>(`/api/feed/org/${orgId}`).then(r => r.items),

      create: (data: { org_id: string; agent_name: string; content_type: string; content: Record<string, unknown> }) =>
        fetchAPI<AgentPost>("/api/feed", {
          method: "POST",
          body: JSON.stringify(data),
        }),

      like: (postId: string) =>
        fetchAPI<Record<string, unknown>>(`/api/feed/${postId}/like`, { method: "POST" }).then(r => ({ likes: (r.likes as number) || 0 })),

      reply: (postId: string, data: { org_id: string; agent_name: string; content: Record<string, unknown> }) =>
        fetchAPI<void>(`/api/feed/${postId}/reply`, {
          method: "POST",
          body: JSON.stringify(data),
        }),
    },
  },
};
