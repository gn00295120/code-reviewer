"use client";

import { useEffect, useState, useCallback } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface MemoryEntry {
  id: string;
  agent_role: string;
  memory_type: string;
  content: string;
  relevance_score: number;
  access_count: number;
  created_at: string;
}

const AGENT_ROLES = ["", "logic", "security", "edge_case", "convention", "performance"];
const MEMORY_TYPES = ["", "pattern", "learning", "preference"];

const ROLE_COLORS: Record<string, string> = {
  logic: "bg-blue-900/50 text-blue-300 border-blue-700",
  security: "bg-red-900/50 text-red-300 border-red-700",
  edge_case: "bg-yellow-900/50 text-yellow-300 border-yellow-700",
  convention: "bg-green-900/50 text-green-300 border-green-700",
  performance: "bg-purple-900/50 text-purple-300 border-purple-700",
};

const TYPE_COLORS: Record<string, string> = {
  pattern: "bg-zinc-800 text-zinc-300",
  learning: "bg-zinc-800 text-teal-300",
  preference: "bg-zinc-800 text-orange-300",
};

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [consolidating, setConsolidating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterType, setFilterType] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      let result: { items: Record<string, unknown>[]; total: number };
      if (searchQuery.trim()) {
        result = await api.memory.search(searchQuery.trim());
      } else {
        result = await api.memory.list({
          agent_role: filterRole || undefined,
          memory_type: filterType || undefined,
          limit: 50,
        });
      }
      setMemories(result.items as unknown as MemoryEntry[]);
      setTotal(result.total);
    } catch {
      setMemories([]);
      setTotal(0);
    }
    setLoading(false);
  }, [searchQuery, filterRole, filterType]);

  useEffect(() => {
    load();
  }, [load]);

  const handleConsolidate = async () => {
    setConsolidating(true);
    try {
      await api.memory.consolidate();
      await load();
    } catch {}
    setConsolidating(false);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.memory.delete(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      setTotal((prev) => prev - 1);
    } catch {}
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-zinc-100">Memory Palace</h2>
              <p className="mt-1 text-sm text-zinc-400">
                Agent memory entries — patterns, learnings, and preferences across roles
              </p>
            </div>
            <Button
              onClick={handleConsolidate}
              disabled={consolidating}
              className="bg-violet-700 hover:bg-violet-600 text-white"
            >
              {consolidating ? "Consolidating..." : "Consolidate"}
            </Button>
          </div>

          {/* Search + Filters */}
          <div className="flex gap-3">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memories..."
              className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
            />
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
            >
              {AGENT_ROLES.map((r) => (
                <option key={r} value={r}>{r || "All roles"}</option>
              ))}
            </select>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
            >
              {MEMORY_TYPES.map((t) => (
                <option key={t} value={t}>{t || "All types"}</option>
              ))}
            </select>
          </div>

          {/* Stats bar */}
          <p className="text-xs text-zinc-500">{total} memories total</p>

          {/* Memory cards */}
          {loading ? (
            <p className="text-sm text-zinc-500">Loading...</p>
          ) : memories.length === 0 ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-8 text-center">
              <p className="text-sm text-zinc-500">No memories found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {memories.map((m) => (
                <div key={m.id} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        variant="outline"
                        className={ROLE_COLORS[m.agent_role] ?? "bg-zinc-800 text-zinc-300"}
                      >
                        {m.agent_role}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={TYPE_COLORS[m.memory_type] ?? "bg-zinc-800 text-zinc-300"}
                      >
                        {m.memory_type}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-zinc-500 shrink-0">
                      <span>relevance {(m.relevance_score * 100).toFixed(0)}%</span>
                      <span>{m.access_count} accesses</span>
                      <button
                        onClick={() => handleDelete(m.id)}
                        className="text-red-500 hover:text-red-400 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-200 leading-relaxed line-clamp-3">{m.content}</p>
                  <p className="text-xs text-zinc-600">
                    {new Date(m.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
