export interface AgentOrg {
  id: string;
  name: string;
  description: string | null;
  topology: Record<string, unknown>;
  config: Record<string, unknown>;
  is_template: boolean;
  fork_count: number;
  forked_from_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentPost {
  id: string;
  org_id: string;
  agent_name: string;
  content_type: string;
  content: Record<string, unknown>;
  pheromone_state: Record<string, unknown>;
  likes: number;
  is_public: boolean;
  created_at: string;
  replies?: AgentPostReply[];
}

export interface AgentPostReply {
  id: string;
  post_id: string;
  org_id: string;
  agent_name: string;
  content: Record<string, unknown>;
  created_at: string;
}

export interface PheromoneTrail {
  id: string;
  org_id: string;
  shared_state: Record<string, unknown>;
  updated_by: string | null;
  updated_at: string;
}
