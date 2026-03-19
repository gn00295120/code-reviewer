"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useWorldModelStore } from "@/stores/world-model-store";
import { api } from "@/lib/api";

interface Props {
  modelId: string;
}

export function SimulationControls({ modelId }: Props) {
  const { status, setStatus, currentStep, totalCost } = useWorldModelStore();
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      await api.worldModels.start(modelId);
      setStatus("running");
    } catch {}
    setLoading(false);
  };

  const handlePause = async () => {
    try {
      await api.worldModels.pause(modelId);
      setStatus("paused");
    } catch {}
  };

  const handleStep = async () => {
    setLoading(true);
    try {
      await api.worldModels.step(modelId);
    } catch {}
    setLoading(false);
  };

  const handleReset = async () => {
    try {
      await api.worldModels.reset(modelId);
      setStatus("idle");
    } catch {}
  };

  return (
    <div className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3">
      <div className="flex items-center gap-2">
        {status === "running" ? (
          <Button onClick={handlePause} variant="outline" size="sm" className="border-zinc-700">
            Pause
          </Button>
        ) : (
          <Button onClick={handleStart} disabled={loading} size="sm">
            {loading ? "Starting..." : status === "paused" ? "Resume" : "Start"}
          </Button>
        )}
        <Button onClick={handleStep} disabled={status === "running" || loading} variant="outline" size="sm" className="border-zinc-700">
          Step
        </Button>
        <Button onClick={handleReset} variant="outline" size="sm" className="border-zinc-700 text-zinc-400">
          Reset
        </Button>
      </div>

      <div className="flex items-center gap-4 text-xs">
        <div>
          <span className="text-zinc-500">Status: </span>
          <span className={
            status === "running" ? "text-blue-400" :
            status === "paused" ? "text-yellow-400" :
            status === "completed" ? "text-green-400" :
            status === "error" ? "text-red-400" : "text-zinc-400"
          }>
            {status}
          </span>
        </div>
        <div className="h-3 w-px bg-zinc-700" />
        <div>
          <span className="text-zinc-500">Step: </span>
          <span className="text-zinc-300">{currentStep}</span>
        </div>
        <div className="h-3 w-px bg-zinc-700" />
        <div>
          <span className="text-zinc-500">Cost: </span>
          <span className="text-emerald-400">${totalCost.toFixed(4)}</span>
        </div>
      </div>
    </div>
  );
}
