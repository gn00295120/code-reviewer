"use client";

import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useReviewStore } from "@/stores/review-store";
import { AgentReviewNode } from "./AgentReviewNode";
import type { AgentRole } from "@/types/review";

const nodeTypes: NodeTypes = {
  agentNode: AgentReviewNode,
};

const AGENT_ROLES: { role: AgentRole; label: string; color: string }[] = [
  { role: "logic", label: "Logic", color: "#3b82f6" },
  { role: "security", label: "Security", color: "#ef4444" },
  { role: "edge_case", label: "Edge Cases", color: "#f59e0b" },
  { role: "convention", label: "Convention", color: "#8b5cf6" },
  { role: "performance", label: "Performance", color: "#10b981" },
];

export function ReviewFlowCanvas() {
  const { agentStates, reviewStatus } = useReviewStore();

  const nodes: Node[] = [
    // Source: Fetch Diff
    {
      id: "fetch_diff",
      type: "agentNode",
      position: { x: 50, y: 200 },
      data: {
        label: "Fetch Diff",
        role: "fetch_diff",
        status: reviewStatus === "idle" ? "idle" : "completed",
        color: "#6b7280",
        findings_count: 0,
        cost_usd: 0,
      },
    },
    // 5 Agent nodes
    ...AGENT_ROLES.map((agent, i) => ({
      id: agent.role,
      type: "agentNode",
      position: { x: 300, y: 40 + i * 90 },
      data: {
        label: agent.label,
        role: agent.role,
        status: agentStates[agent.role]?.status || "idle",
        color: agent.color,
        findings_count: agentStates[agent.role]?.findings_count || 0,
        cost_usd: agentStates[agent.role]?.cost_usd || 0,
      },
    })),
    // Supervisor
    {
      id: "supervisor",
      type: "agentNode",
      position: { x: 580, y: 200 },
      data: {
        label: "Supervisor",
        role: "supervisor",
        status: reviewStatus === "completed" ? "completed" : reviewStatus === "running" ? "running" : "idle",
        color: "#f97316",
        findings_count: 0,
        cost_usd: 0,
      },
    },
  ];

  const edges: Edge[] = [
    // Fetch → all agents
    ...AGENT_ROLES.map((agent) => ({
      id: `fetch-${agent.role}`,
      source: "fetch_diff",
      target: agent.role,
      animated: agentStates[agent.role]?.status === "running",
      style: { stroke: agent.color },
    })),
    // All agents → supervisor
    ...AGENT_ROLES.map((agent) => ({
      id: `${agent.role}-supervisor`,
      source: agent.role,
      target: "supervisor",
      animated: agentStates[agent.role]?.status === "completed" && reviewStatus === "running",
      style: { stroke: agent.color },
    })),
  ];

  return (
    <div className="h-[500px] w-full rounded-lg border border-zinc-800 bg-zinc-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
      >
        <Background color="#27272a" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
