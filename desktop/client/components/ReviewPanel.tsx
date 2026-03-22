import React from "react";
import AgentProgress from "./AgentProgress";
import FindingsPanel from "./FindingsPanel";

interface Finding {
  id: string;
  agent_role: string;
  severity: string;
  file_path: string;
  line_number: number | null;
  title: string;
  description: string;
  suggested_fix: string | null;
  confidence: number;
}

interface Props {
  reviewId: string;
  findings: Finding[];
  agentStates: Record<string, string>;
  isReviewing: boolean;
  error: string;
}

export default function ReviewPanel({ reviewId, findings, agentStates, isReviewing, error }: Props) {
  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Agent Progress */}
      <AgentProgress agentStates={agentStates} isReviewing={isReviewing} />

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm">{error}</div>
      )}

      {/* Findings */}
      <FindingsPanel findings={findings} />
    </div>
  );
}
