import type { Review, ReviewDetail, ReviewEvent, ReviewListResponse } from "@/types/review";
import type { WorldModel, WorldModelDetail, PhysicsEvent } from "@/types/world-model";
import type { AgentOrg, AgentPost } from "@/types/community";
import type { AuditLog, SecurityPolicy } from "@/types/enterprise";
import type { MarketplaceListing } from "@/types/marketplace";
import type { AgentCompany, CompanyAgent } from "@/types/company";
import type { Proposal, Vote } from "@/types/governance";
import type { Experiment, ExperimentRun } from "@/types/science";

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

    timeline: (id: string) =>
      fetchAPI<ReviewEvent[]>(`/api/reviews/${id}/timeline`),
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

  templates: {
    list: () =>
      fetchAPI<{ id: string; name: string; description: string | null; rules: Record<string, unknown>; created_by: string | null; created_at: string; updated_at: string | null }[]>("/api/templates"),

    get: (id: string) =>
      fetchAPI<{ id: string; name: string; description: string | null; rules: Record<string, unknown>; created_by: string | null; created_at: string; updated_at: string | null }>(`/api/templates/${id}`),

    create: (data: { name: string; description?: string; rules?: Record<string, unknown> }) =>
      fetchAPI<{ id: string; name: string }>("/api/templates", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (id: string, data: { name?: string; description?: string; rules?: Record<string, unknown> }) =>
      fetchAPI<{ id: string; name: string }>(`/api/templates/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),

    delete: (id: string) =>
      fetchAPI<void>(`/api/templates/${id}`, { method: "DELETE" }),

    fork: (id: string) =>
      fetchAPI<{ id: string; name: string }>(`/api/templates/${id}/fork`, { method: "POST" }),
  },

  memory: {
    list: (params?: { agent_role?: string; memory_type?: string; limit?: number; offset?: number }) => {
      const sp = new URLSearchParams();
      if (params?.agent_role) sp.set("agent_role", params.agent_role);
      if (params?.memory_type) sp.set("memory_type", params.memory_type);
      if (params?.limit != null) sp.set("limit", String(params.limit));
      if (params?.offset != null) sp.set("offset", String(params.offset));
      const q = sp.toString();
      return fetchAPI<{ items: Record<string, unknown>[]; total: number }>(`/api/memory${q ? `?${q}` : ""}`);
    },

    get: (id: string) =>
      fetchAPI<Record<string, unknown>>(`/api/memory/${id}`),

    create: (data: Record<string, unknown>) =>
      fetchAPI<Record<string, unknown>>("/api/memory", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    delete: (id: string) =>
      fetchAPI<void>(`/api/memory/${id}`, { method: "DELETE" }),

    search: (q: string) =>
      fetchAPI<{ items: Record<string, unknown>[]; total: number }>(`/api/memory/search?q=${encodeURIComponent(q)}`),

    consolidate: () =>
      fetchAPI<{ consolidated: number }>("/api/memory/consolidate", { method: "POST" }),
  },

  enterprise: {
    auditLogs: (params?: { action?: string; from?: string; to?: string; limit?: number; offset?: number }) => {
      const sp = new URLSearchParams();
      if (params?.action) sp.set("action", params.action);
      if (params?.from) sp.set("from", params.from);
      if (params?.to) sp.set("to", params.to);
      if (params?.limit != null) sp.set("limit", String(params.limit));
      if (params?.offset != null) sp.set("offset", String(params.offset));
      const q = sp.toString();
      return fetchAPI<{ items: AuditLog[]; total: number }>(`/api/enterprise/audit-logs${q ? `?${q}` : ""}`);
    },

    policies: {
      list: () =>
        fetchAPI<SecurityPolicy[]>("/api/enterprise/policies"),

      create: (data: { name: string; policy_type: string; config: Record<string, unknown> }) =>
        fetchAPI<SecurityPolicy>("/api/enterprise/policies", {
          method: "POST",
          body: JSON.stringify(data),
        }),

      update: (id: string, data: Partial<{ name: string; config: Record<string, unknown> }>) =>
        fetchAPI<SecurityPolicy>(`/api/enterprise/policies/${id}`, {
          method: "PUT",
          body: JSON.stringify(data),
        }),

      toggle: (id: string, is_active: boolean) =>
        fetchAPI<SecurityPolicy>(`/api/enterprise/policies/${id}/toggle`, {
          method: "POST",
          body: JSON.stringify({ is_active }),
        }),
    },
  },

  marketplace: {
    browse: (params?: { type?: string; sort?: string; q?: string; limit?: number; offset?: number }) => {
      const sp = new URLSearchParams();
      if (params?.type) sp.set("type", params.type);
      if (params?.sort) sp.set("sort", params.sort);
      if (params?.q) sp.set("q", params.q);
      if (params?.limit != null) sp.set("limit", String(params.limit));
      if (params?.offset != null) sp.set("offset", String(params.offset));
      const q = sp.toString();
      return fetchAPI<{ items: MarketplaceListing[]; total: number }>(`/api/marketplace${q ? `?${q}` : ""}`);
    },

    get: (id: string) =>
      fetchAPI<MarketplaceListing>(`/api/marketplace/${id}`),

    publish: (data: { listing_type: string; title: string; description: string; version: string; tags: string[]; config: Record<string, unknown> }) =>
      fetchAPI<MarketplaceListing>("/api/marketplace", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    install: (id: string) =>
      fetchAPI<{ installed: boolean; local_id: string }>(`/api/marketplace/${id}/install`, { method: "POST" }),

    rate: (id: string, stars: number) =>
      fetchAPI<{ rating: number; rating_count: number }>(`/api/marketplace/${id}/rate`, {
        method: "POST",
        body: JSON.stringify({ stars }),
      }),
  },

  companies: {
    create: (data: { name: string; description?: string; budget_usd?: number }) =>
      fetchAPI<AgentCompany>("/api/companies", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    list: () =>
      fetchAPI<{ items: AgentCompany[]; total: number }>("/api/companies").then(r => r.items),

    get: (id: string) => fetchAPI<AgentCompany>(`/api/companies/${id}`),

    activate: (id: string) =>
      fetchAPI<AgentCompany>(`/api/companies/${id}/activate`, { method: "POST" }),

    pause: (id: string) =>
      fetchAPI<AgentCompany>(`/api/companies/${id}/pause`, { method: "POST" }),

    agents: {
      list: (companyId: string) =>
        fetchAPI<{ items: CompanyAgent[]; total: number }>(`/api/companies/${companyId}/agents`).then(r => r.items),

      add: (companyId: string, data: Partial<CompanyAgent>) =>
        fetchAPI<CompanyAgent>(`/api/companies/${companyId}/agents`, {
          method: "POST",
          body: JSON.stringify(data),
        }),

      remove: (companyId: string, agentId: string) =>
        fetchAPI<void>(`/api/companies/${companyId}/agents/${agentId}`, { method: "DELETE" }),
    },

    budget: (id: string) =>
      fetchAPI<{ budget_usd: number; spent_usd: number; remaining_usd: number; per_agent: Record<string, number> }>(`/api/companies/${id}/budget`),
  },

  governance: {
    proposals: {
      list: (companyId: string) =>
        fetchAPI<{ items: Proposal[]; total: number }>(`/api/companies/${companyId}/proposals`).then(r => r.items),

      create: (companyId: string, data: Partial<Proposal>) =>
        fetchAPI<Proposal>(`/api/companies/${companyId}/proposals`, {
          method: "POST",
          body: JSON.stringify(data),
        }),

      get: (id: string) => fetchAPI<Proposal>(`/api/proposals/${id}`),
    },

    vote: (proposalId: string, data: { vote: "for" | "against" | "abstain"; reason?: string }) =>
      fetchAPI<Vote>(`/api/proposals/${proposalId}/vote`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    execute: (proposalId: string) =>
      fetchAPI<Proposal>(`/api/proposals/${proposalId}/execute`, { method: "POST" }),
  },

  science: {
    experiments: {
      list: () =>
        fetchAPI<{ items: Experiment[]; total: number }>("/api/science/experiments").then(r => r.items),

      create: (data: Partial<Experiment>) =>
        fetchAPI<Experiment>("/api/science/experiments", {
          method: "POST",
          body: JSON.stringify(data),
        }),

      get: (id: string) => fetchAPI<Experiment>(`/api/science/experiments/${id}`),
    },

    run: (experimentId: string) =>
      fetchAPI<ExperimentRun>(`/api/science/experiments/${experimentId}/run`, { method: "POST" }),

    analyze: (experimentId: string) =>
      fetchAPI<Experiment>(`/api/science/experiments/${experimentId}/analyze`, { method: "POST" }),

    publish: (experimentId: string) =>
      fetchAPI<Experiment>(`/api/science/experiments/${experimentId}/publish`, { method: "POST" }),

    runs: (experimentId: string) =>
      fetchAPI<{ items: ExperimentRun[]; total: number }>(`/api/science/experiments/${experimentId}/runs`).then(r => r.items),
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
