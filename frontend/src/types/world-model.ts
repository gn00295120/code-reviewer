export type WorldModelStatus = "idle" | "running" | "paused" | "completed" | "error";

export interface WorldModel {
  id: string;
  name: string;
  description: string | null;
  model_type: string;
  current_state: Record<string, unknown>;
  agent_config: Record<string, unknown>;
  total_steps: number;
  total_cost_usd: number;
  status: WorldModelStatus;
  created_at: string;
  updated_at: string;
}

export interface WorldModelDetail extends WorldModel {
  mujoco_xml: string | null;
  recent_events: PhysicsEvent[];
}

export interface PhysicsEvent {
  id: string;
  model_id: string;
  step: number;
  action: Record<string, unknown>;
  observation: Record<string, unknown>;
  reward: number;
  agent_reasoning: string | null;
  tokens_used: number;
  cost_usd: number;
  timestamp: string;
}

export interface ModelGeometry {
  bodies: { name: string; pos: [number, number, number]; size: [number, number, number]; type: string }[];
  joints: { name: string; pos: [number, number, number]; axis: [number, number, number] }[];
}
