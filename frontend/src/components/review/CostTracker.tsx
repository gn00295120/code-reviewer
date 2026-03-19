"use client";

import { useReviewStore } from "@/stores/review-store";

export function CostTracker() {
  const { totalCost, agentStates, reviewStatus } = useReviewStore();

  const totalTokens = Object.values(agentStates).reduce((sum, a) => sum + a.tokens, 0);
  const completedAgents = Object.values(agentStates).filter((a) => a.status === "completed").length;
  const totalAgents = Object.values(agentStates).length;

  return (
    <div className="flex items-center gap-4 rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-xs">
      <div className="flex items-center gap-1.5">
        <span className="text-zinc-500">Status:</span>
        <span
          className={
            reviewStatus === "running"
              ? "text-blue-400"
              : reviewStatus === "completed"
                ? "text-green-400"
                : reviewStatus === "failed"
                  ? "text-red-400"
                  : "text-zinc-400"
          }
        >
          {reviewStatus === "running"
            ? `Running (${completedAgents}/${totalAgents})`
            : reviewStatus.charAt(0).toUpperCase() + reviewStatus.slice(1)}
        </span>
      </div>
      <div className="h-3 w-px bg-zinc-700" />
      <div className="flex items-center gap-1.5">
        <span className="text-zinc-500">Tokens:</span>
        <span className="text-zinc-300">{totalTokens.toLocaleString()}</span>
      </div>
      <div className="h-3 w-px bg-zinc-700" />
      <div className="flex items-center gap-1.5">
        <span className="text-zinc-500">Cost:</span>
        <span className="text-emerald-400">${totalCost.toFixed(4)}</span>
      </div>
    </div>
  );
}
