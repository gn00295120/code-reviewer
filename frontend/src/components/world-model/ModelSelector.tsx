"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

const PRESET_MODELS = [
  { type: "ur5", name: "UR5 Robot Arm", desc: "6-DOF industrial robot arm" },
  { type: "crazyflie", name: "Crazyflie Drone", desc: "Micro quadrotor UAV" },
  { type: "jaco", name: "Jaco Arm", desc: "7-DOF assistive robot arm" },
  { type: "custom", name: "Custom Model", desc: "Upload your own MJCF XML" },
];

export function ModelSelector() {
  const [name, setName] = useState("");
  const [selectedType, setSelectedType] = useState("ur5");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleCreate = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const model = await api.worldModels.create({
        name: name.trim(),
        model_type: selectedType,
      });
      router.push(`/world-model/${model.id}`);
    } catch {}
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {PRESET_MODELS.map((preset) => (
          <button
            key={preset.type}
            onClick={() => setSelectedType(preset.type)}
            className={`rounded-lg border p-3 text-left transition-colors ${
              selectedType === preset.type
                ? "border-blue-500 bg-blue-950/20"
                : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
            }`}
          >
            <div className="text-sm font-medium text-zinc-200">{preset.name}</div>
            <div className="text-xs text-zinc-500 mt-0.5">{preset.desc}</div>
          </button>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Sandbox name..."
          className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
        />
        <Button onClick={handleCreate} disabled={loading || !name.trim()}>
          {loading ? "Creating..." : "Create Sandbox"}
        </Button>
      </div>
    </div>
  );
}
