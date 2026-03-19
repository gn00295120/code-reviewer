"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { SandboxViewer } from "@/components/world-model/SandboxViewer";
import { SimulationControls } from "@/components/world-model/SimulationControls";
import { EventTimeline } from "@/components/world-model/EventTimeline";
import { useWorldModelStore } from "@/stores/world-model-store";
import { api } from "@/lib/api";

export default function WorldModelDetailPage() {
  const params = useParams();
  const modelId = params.id as string;
  const { setCurrentModel, setStatus, updateCost } = useWorldModelStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!modelId) return;
    api.worldModels.get(modelId).then((model) => {
      setCurrentModel(model);
      setStatus(model.status);
      if (model.total_cost_usd) updateCost(Number(model.total_cost_usd));
      setLoading(false);
    }).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load model");
      setLoading(false);
    });

    return () => {
      setCurrentModel(null);
      setStatus("idle");
    };
  }, [modelId, setCurrentModel, setStatus, updateCost]);

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-zinc-500">Loading sandbox...</p>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-red-400">{error}</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-6xl space-y-4">
          <SimulationControls modelId={modelId} />
          <SandboxViewer />
          <EventTimeline />
        </div>
      </main>
    </div>
  );
}
