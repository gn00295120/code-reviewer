export interface Proposal {
  id: string;
  company_id: string;
  title: string;
  description: string;
  proposal_type: "budget" | "role_change" | "process" | "policy";
  proposed_changes: Record<string, unknown>;
  proposed_by: string;
  status: "open" | "passed" | "rejected" | "executed";
  votes_for: number;
  votes_against: number;
  quorum_required: number;
  deadline: string;
  created_at: string;
}

export interface Vote {
  id: string;
  proposal_id: string;
  voter_id: string;
  vote: "for" | "against" | "abstain";
  reason: string | null;
  created_at: string;
}
