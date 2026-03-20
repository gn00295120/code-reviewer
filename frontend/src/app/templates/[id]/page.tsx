"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

const AGENT_ROLES = ["logic", "security", "edge_case", "convention", "performance"];

interface AgentRule {
  enabled: boolean;
  severity_threshold: string;
  custom_instructions: string;
  max_findings: number;
}

interface TemplateRules {
  agents: Record<string, AgentRule>;
  global: {
    max_total_findings: number;
    min_confidence: number;
    language_hints: string[];
    ignore_patterns: string[];
  };
}

const DEFAULT_AGENT: AgentRule = {
  enabled: true,
  severity_threshold: "low",
  custom_instructions: "",
  max_findings: 10,
};

const DEFAULT_RULES: TemplateRules = {
  agents: Object.fromEntries(AGENT_ROLES.map((r) => [r, { ...DEFAULT_AGENT }])),
  global: {
    max_total_findings: 30,
    min_confidence: 0.6,
    language_hints: [],
    ignore_patterns: [],
  },
};

export default function TemplateEditPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [rules, setRules] = useState<TemplateRules>(DEFAULT_RULES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.templates.get(templateId).then((t) => {
      setName(t.name);
      setDescription(t.description || "");
      setRules({ ...DEFAULT_RULES, ...(t.rules as unknown as TemplateRules) });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [templateId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.templates.update(templateId, { name, description, rules: rules as unknown as Record<string, unknown> });
    } catch {}
    setSaving(false);
  };

  const handleDelete = async () => {
    await api.templates.delete(templateId);
    router.push("/templates");
  };

  const updateAgent = (role: string, update: Partial<AgentRule>) => {
    setRules((prev) => ({
      ...prev,
      agents: {
        ...prev.agents,
        [role]: { ...prev.agents[role], ...update },
      },
    }));
  };

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-zinc-500">Loading...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-zinc-100">Edit Template</h2>
            <div className="flex gap-2">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </Button>
              <Button variant="outline" className="border-zinc-700 text-red-400" onClick={handleDelete}>
                Delete
              </Button>
            </div>
          </div>

          {/* Name + Description */}
          <div className="space-y-3">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 focus:border-blue-500 focus:outline-none"
              placeholder="Template name"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 focus:border-blue-500 focus:outline-none h-20 resize-none"
              placeholder="Description..."
            />
          </div>

          {/* Agent Rules */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-zinc-200">Agent Configuration</h3>
            {AGENT_ROLES.map((role) => {
              const agent = rules.agents[role] || DEFAULT_AGENT;
              return (
                <div key={role} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-200 capitalize">{role.replace("_", " ")}</span>
                    <label className="flex items-center gap-2 text-xs text-zinc-400">
                      <input
                        type="checkbox"
                        checked={agent.enabled}
                        onChange={(e) => updateAgent(role, { enabled: e.target.checked })}
                        className="rounded"
                      />
                      Enabled
                    </label>
                  </div>
                  {agent.enabled && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-zinc-500">Severity threshold</label>
                        <select
                          value={agent.severity_threshold}
                          onChange={(e) => updateAgent(role, { severity_threshold: e.target.value })}
                          className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300"
                        >
                          <option value="high">High only</option>
                          <option value="medium">Medium+</option>
                          <option value="low">Low+</option>
                          <option value="info">All</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-zinc-500">Max findings</label>
                        <input
                          type="number"
                          value={agent.max_findings}
                          onChange={(e) => updateAgent(role, { max_findings: parseInt(e.target.value) || 10 })}
                          className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300"
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="text-xs text-zinc-500">Custom instructions</label>
                        <textarea
                          value={agent.custom_instructions}
                          onChange={(e) => updateAgent(role, { custom_instructions: e.target.value })}
                          className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300 h-16 resize-none"
                          placeholder="Additional instructions for this agent..."
                        />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Global Settings */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-zinc-200">Global Settings</h3>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-zinc-500">Max total findings</label>
                <input
                  type="number"
                  value={rules.global.max_total_findings}
                  onChange={(e) => setRules((prev) => ({ ...prev, global: { ...prev.global, max_total_findings: parseInt(e.target.value) || 30 } }))}
                  className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300"
                />
              </div>
              <div>
                <label className="text-xs text-zinc-500">Min confidence</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={rules.global.min_confidence}
                  onChange={(e) => setRules((prev) => ({ ...prev, global: { ...prev.global, min_confidence: parseFloat(e.target.value) || 0.6 } }))}
                  className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300"
                />
              </div>
              <div className="col-span-2">
                <label className="text-xs text-zinc-500">Ignore patterns (comma-separated)</label>
                <input
                  type="text"
                  value={rules.global.ignore_patterns.join(", ")}
                  onChange={(e) => setRules((prev) => ({ ...prev, global: { ...prev.global, ignore_patterns: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) } }))}
                  className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300"
                  placeholder="*.test.*, migrations/*, ..."
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
