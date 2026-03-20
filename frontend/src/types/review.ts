export type ReviewStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type Severity = "high" | "medium" | "low" | "info";
export type AgentRole = "logic" | "security" | "edge_case" | "convention" | "performance";

export interface Review {
  id: string;
  pr_url: string;
  repo_name: string;
  pr_number: number | null;
  status: ReviewStatus;
  total_issues: number;
  total_cost_usd: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ReviewDetail extends Review {
  findings: Finding[];
  config: Record<string, unknown>;
}

export interface Finding {
  id: string;
  agent_role: AgentRole;
  severity: Severity;
  file_path: string;
  line_number: number | null;
  title: string;
  description: string;
  suggested_fix: string | null;
  confidence: number;
  cost_usd: number;
  created_at: string;
}

export interface ReviewListResponse {
  items: Review[];
  total: number;
}

// WebSocket event types
export interface WSEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface AgentState {
  role: AgentRole;
  status: "idle" | "running" | "completed" | "error";
  findings_count: number;
  tokens: number;
  cost_usd: number;
}

export interface ReviewEvent {
  id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  timestamp: string;
}
