"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { AgentOrg } from "@/types/community";

interface Props {
  org: AgentOrg;
  onFork?: (newOrg: AgentOrg) => void;
}

export function OrgCard({ org, onFork }: Props) {
  const [forking, setForking] = useState(false);
  const [forkCount, setForkCount] = useState(org.fork_count);

  const handleFork = async () => {
    setForking(true);
    try {
      const newOrg = await api.community.orgs.fork(org.id);
      setForkCount((c) => c + 1);
      onFork?.(newOrg);
    } catch {}
    setForking(false);
  };

  const topology = org.topology as { agents?: { role: string }[] };
  const agentCount = topology?.agents?.length || 0;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-zinc-100">{org.name}</h3>
          {org.description && (
            <p className="text-xs text-zinc-500 mt-0.5">{org.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {org.is_template && (
            <Badge variant="outline" className="bg-purple-900/50 text-purple-300 border-purple-700">
              Template
            </Badge>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs text-zinc-500">
        <span>{agentCount} agents</span>
        <span>{forkCount} forks</span>
        {org.forked_from_id && <span>forked</span>}
        <span>{new Date(org.created_at).toLocaleDateString()}</span>
      </div>

      {/* Agent roles preview */}
      {topology?.agents && (
        <div className="flex flex-wrap gap-1">
          {topology.agents.slice(0, 5).map((agent) => (
            <span key={agent.role} className="rounded bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-400">
              {agent.role}
            </span>
          ))}
          {topology.agents.length > 5 && (
            <span className="text-[10px] text-zinc-600">+{topology.agents.length - 5} more</span>
          )}
        </div>
      )}

      <div className="flex items-center gap-2 pt-1">
        <Button onClick={handleFork} disabled={forking} variant="outline" size="sm" className="border-zinc-700 text-xs">
          {forking ? "Forking..." : "Fork"}
        </Button>
        <Link href={`/community/${org.id}`}>
          <Button variant="outline" size="sm" className="border-zinc-700 text-xs">
            View
          </Button>
        </Link>
      </div>
    </div>
  );
}
