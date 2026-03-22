import React from "react";

const AGENTS = ["logic", "security", "edge_case", "convention", "performance"];

const AGENT_LABELS: Record<string, string> = {
  logic: "Logic",
  security: "Security",
  edge_case: "Edge Cases",
  convention: "Conventions",
  performance: "Performance",
};

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  idle: { bg: "bg-zinc-800/50", text: "text-zinc-500", dot: "bg-zinc-600" },
  running: { bg: "bg-blue-900/30", text: "text-blue-300", dot: "bg-blue-500 animate-pulse" },
  completed: { bg: "bg-green-900/20", text: "text-green-300", dot: "bg-green-500" },
  error: { bg: "bg-red-900/20", text: "text-red-300", dot: "bg-red-500" },
};

interface Props {
  agentStates: Record<string, string>;
  isReviewing: boolean;
}

export default function AgentProgress({ agentStates, isReviewing }: Props) {
  if (!isReviewing && Object.keys(agentStates).length === 0) return null;

  return (
    <div className="grid grid-cols-5 gap-2">
      {AGENTS.map(agent => {
        const status = agentStates[agent] || "idle";
        const style = STATUS_STYLES[status] || STATUS_STYLES.idle;
        return (
          <div key={agent} className={`${style.bg} rounded-lg p-3 border border-zinc-800`}>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${style.dot}`} />
              <span className={`text-xs font-medium ${style.text}`}>{AGENT_LABELS[agent]}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
