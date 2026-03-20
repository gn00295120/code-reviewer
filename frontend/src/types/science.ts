export interface Experiment {
  id: string;
  title: string;
  hypothesis: string;
  methodology: string;
  status: "draft" | "running" | "analyzing" | "completed" | "published";
  variables: Record<string, unknown>;
  results: Record<string, unknown> | null;
  analysis: string | null;
  conclusion: string | null;
  confidence: number | null;
  total_runs: number;
  total_cost_usd: number;
  created_at: string;
}

export interface ExperimentRun {
  id: string;
  experiment_id: string;
  run_number: number;
  parameters: Record<string, unknown>;
  results: Record<string, unknown> | null;
  metrics: Record<string, unknown> | null;
  status: "pending" | "running" | "completed" | "failed";
  duration_seconds: number | null;
  cost_usd: number;
}
