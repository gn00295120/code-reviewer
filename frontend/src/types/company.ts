export interface AgentCompany {
  id: string;
  name: string;
  description: string | null;
  owner: string;
  org_chart: Record<string, unknown>;
  processes: Record<string, unknown>;
  shared_state: Record<string, unknown>;
  budget_usd: number;
  spent_usd: number;
  status: "active" | "paused" | "archived";
  agent_count: number;
  created_at: string;
}

export interface CompanyAgent {
  id: string;
  company_id: string;
  role: string;
  title: string;
  model: string;
  system_prompt: string;
  capabilities: string[];
  reports_to: string | null;
  status: "active" | "idle" | "paused";
  total_tasks: number;
  total_cost_usd: number;
}
