"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { FeedTimeline } from "@/components/community/FeedTimeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { AgentOrg, AgentPost } from "@/types/community";

export default function OrgDetailPage() {
  const params = useParams();
  const orgId = params.id as string;
  const [org, setOrg] = useState<AgentOrg | null>(null);
  const [feed, setFeed] = useState<AgentPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [following, setFollowing] = useState(false);

  useEffect(() => {
    if (!orgId) return;
    Promise.all([
      api.community.orgs.get(orgId),
      api.community.feed.orgFeed(orgId).catch(() => []),
    ]).then(([orgData, feedData]) => {
      setOrg(orgData);
      setFeed(feedData);
      setLoading(false);
    }).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load org");
      setLoading(false);
    });
  }, [orgId]);

  const handleFollow = async () => {
    try {
      if (following) {
        await api.community.orgs.unfollow(orgId);
      } else {
        await api.community.orgs.follow(orgId);
      }
      setFollowing(!following);
    } catch {}
  };

  const handleFork = async () => {
    try {
      const newOrg = await api.community.orgs.fork(orgId);
      window.location.href = `/community/${newOrg.id}`;
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-zinc-500">Loading org...</p>
        </main>
      </div>
    );
  }

  if (error || !org) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-red-400">{error || "Org not found"}</p>
        </main>
      </div>
    );
  }

  const topology = org.topology as { agents?: { role: string; description?: string }[] };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-4xl space-y-6">
          {/* Org header */}
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-bold text-zinc-100">{org.name}</h2>
                {org.is_template && (
                  <Badge variant="outline" className="bg-purple-900/50 text-purple-300 border-purple-700">
                    Template
                  </Badge>
                )}
              </div>
              {org.description && (
                <p className="mt-1 text-sm text-zinc-400">{org.description}</p>
              )}
              <div className="flex items-center gap-3 mt-2 text-xs text-zinc-500">
                <span>{org.fork_count} forks</span>
                <span>Created {new Date(org.created_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleFollow} variant="outline" size="sm" className="border-zinc-700">
                {following ? "Unfollow" : "Follow"}
              </Button>
              <Button onClick={handleFork} size="sm">
                Fork Org
              </Button>
            </div>
          </div>

          {/* Agent topology */}
          {topology?.agents && topology.agents.length > 0 && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
              <h3 className="text-sm font-medium text-zinc-200">Agent Team</h3>
              <div className="grid grid-cols-2 gap-2">
                {topology.agents.map((agent) => (
                  <div key={agent.role} className="flex items-center gap-2 rounded bg-zinc-800/50 px-3 py-2">
                    <div className="h-2 w-2 rounded-full bg-blue-500" />
                    <span className="text-xs text-zinc-300">{agent.role}</span>
                    {agent.description && (
                      <span className="text-xs text-zinc-600 truncate">{agent.description}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Org feed */}
          <div>
            <h3 className="text-sm font-medium text-zinc-200 mb-3">Activity</h3>
            <FeedTimeline posts={feed} />
          </div>
        </div>
      </main>
    </div>
  );
}
