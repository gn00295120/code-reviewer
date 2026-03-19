"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { ModelSelector } from "@/components/world-model/ModelSelector";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { WorldModel } from "@/types/world-model";

const STATUS_COLORS: Record<string, string> = {
  idle: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900/50 text-blue-300",
  paused: "bg-yellow-900/50 text-yellow-300",
  completed: "bg-green-900/50 text-green-300",
  error: "bg-red-900/50 text-red-300",
};

export default function WorldModelPage() {
  const [models, setModels] = useState<WorldModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.worldModels.list().then(setModels).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-zinc-100">World Model Sandbox</h2>
            <p className="mt-1 text-sm text-zinc-400">
              LLM-driven physics simulation with MuJoCo + Three.js
            </p>
          </div>

          <ModelSelector />

          <div className="space-y-2">
            <h3 className="text-sm font-medium text-zinc-300">Your Sandboxes</h3>
            {loading ? (
              <p className="text-xs text-zinc-500">Loading...</p>
            ) : models.length === 0 ? (
              <p className="text-xs text-zinc-500">No sandboxes yet. Create one above.</p>
            ) : (
              models.map((model) => (
                <Link
                  key={model.id}
                  href={`/world-model/${model.id}`}
                  className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 hover:bg-zinc-800/50 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-zinc-200">{model.name}</span>
                      <span className="text-xs text-zinc-500">{model.model_type}</span>
                      <Badge variant="outline" className={STATUS_COLORS[model.status]}>
                        {model.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-zinc-500">
                    <span>{model.total_steps} steps</span>
                    <span>${Number(model.total_cost_usd).toFixed(4)}</span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
