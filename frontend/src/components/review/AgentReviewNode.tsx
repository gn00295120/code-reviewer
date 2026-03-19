"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { useReviewStore } from "@/stores/review-store";
import type { AgentRole } from "@/types/review";

interface AgentNodeData {
  label: string;
  role: string;
  status: string;
  color: string;
  findings_count: number;
  cost_usd: number;
}

const STATUS_STYLES: Record<string, string> = {
  idle: "border-zinc-700 bg-zinc-900",
  running: "border-blue-500 bg-zinc-900 shadow-lg shadow-blue-500/20",
  completed: "border-green-500 bg-zinc-900",
  error: "border-red-500 bg-zinc-900",
};

const STATUS_DOT: Record<string, string> = {
  idle: "bg-zinc-600",
  running: "bg-blue-500 animate-pulse",
  completed: "bg-green-500",
  error: "bg-red-500",
};

export function AgentReviewNode({ data }: NodeProps) {
  const d = data as unknown as AgentNodeData;
  const { setSelectedAgent, setTerminalOpen } = useReviewStore();

  return (
    <div
      className={`rounded-lg border-2 px-4 py-3 min-w-[160px] cursor-pointer transition-all ${STATUS_STYLES[d.status] || STATUS_STYLES.idle}`}
      onClick={() => {
        setSelectedAgent(d.role as AgentRole);
        setTerminalOpen(true);
      }}
    >
      <Handle type="target" position={Position.Left} className="!bg-zinc-600" />
      <Handle type="source" position={Position.Right} className="!bg-zinc-600" />

      <div className="flex items-center gap-2">
        <div className={`h-2.5 w-2.5 rounded-full ${STATUS_DOT[d.status] || STATUS_DOT.idle}`} />
        <span className="text-sm font-medium text-zinc-100">{d.label}</span>
      </div>

      {d.status === "completed" && (
        <div className="mt-1.5 flex items-center gap-3 text-xs text-zinc-400">
          <span>{d.findings_count} issues</span>
          <span>${d.cost_usd.toFixed(4)}</span>
        </div>
      )}

      {d.status === "running" && (
        <div className="mt-1.5 text-xs text-blue-400">Analyzing...</div>
      )}
    </div>
  );
}
