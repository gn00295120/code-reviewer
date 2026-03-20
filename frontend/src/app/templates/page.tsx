"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface Template {
  id: string;
  name: string;
  description: string | null;
  rules: Record<string, unknown>;
  created_by: string | null;
  created_at: string;
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  useEffect(() => {
    api.templates.list().then(setTemplates).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await api.templates.create({ name: newName.trim() });
      const updated = await api.templates.list();
      setTemplates(updated);
      setNewName("");
    } catch {}
    setCreating(false);
  };

  const handleFork = async (id: string) => {
    try {
      await api.templates.fork(id);
      const updated = await api.templates.list();
      setTemplates(updated);
    } catch {}
  };

  const agentCount = (rules: Record<string, unknown>) => {
    const agents = (rules as { agents?: Record<string, { enabled?: boolean }> }).agents;
    if (!agents) return 0;
    return Object.values(agents).filter((a) => a.enabled !== false).length;
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-zinc-100">Review Templates</h2>
            <p className="mt-1 text-sm text-zinc-400">
              Custom rule sets that control how review agents behave
            </p>
          </div>

          {/* Create new */}
          <div className="flex gap-2">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="New template name..."
              className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
            />
            <Button onClick={handleCreate} disabled={creating || !newName.trim()}>
              {creating ? "Creating..." : "Create"}
            </Button>
          </div>

          {/* Template list */}
          {loading ? (
            <p className="text-sm text-zinc-500">Loading...</p>
          ) : templates.length === 0 ? (
            <p className="text-sm text-zinc-500">No templates yet.</p>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {templates.map((t) => (
                <div key={t.id} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-zinc-100">{t.name}</h3>
                      {t.description && (
                        <p className="text-xs text-zinc-500 mt-0.5">{t.description}</p>
                      )}
                    </div>
                    <Badge variant="outline" className="bg-zinc-800 text-zinc-400">
                      {agentCount(t.rules)} agents
                    </Badge>
                  </div>
                  <div className="flex gap-2 pt-1">
                    <Link href={`/templates/${t.id}`}>
                      <Button variant="outline" size="sm" className="border-zinc-700 text-xs">Edit</Button>
                    </Link>
                    <Button variant="outline" size="sm" className="border-zinc-700 text-xs" onClick={() => handleFork(t.id)}>
                      Fork
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
