"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Experiment } from "@/types/science";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900/50 text-blue-300 border-blue-800",
  analyzing: "bg-purple-900/50 text-purple-300 border-purple-800",
  completed: "bg-green-900/50 text-green-300 border-green-800",
  published: "bg-yellow-900/50 text-yellow-300 border-yellow-800",
};

function CreateExperimentForm({ onCreated }: { onCreated: (e: Experiment) => void }) {
  const [title, setTitle] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [methodology, setMethodology] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (evt: React.FormEvent) => {
    evt.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const exp = await api.science.experiments.create({ title, hypothesis, methodology });
      onCreated(exp);
      setTitle("");
      setHypothesis("");
      setMethodology("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create experiment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-4 space-y-3">
      <h3 className="text-sm font-medium text-zinc-200">New Experiment</h3>
      <div>
        <label className="block text-xs text-zinc-400 mb-1">Title</label>
        <input
          type="text"
          value={title}
          onChange={e => setTitle(e.target.value)}
          required
          placeholder="Experiment title"
          className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
        />
      </div>
      <div>
        <label className="block text-xs text-zinc-400 mb-1">Hypothesis</label>
        <textarea
          value={hypothesis}
          onChange={e => setHypothesis(e.target.value)}
          required
          rows={2}
          placeholder="If X, then Y because Z..."
          className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none resize-none"
        />
      </div>
      <div>
        <label className="block text-xs text-zinc-400 mb-1">Methodology</label>
        <textarea
          value={methodology}
          onChange={e => setMethodology(e.target.value)}
          rows={2}
          placeholder="Describe your experimental approach"
          className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none resize-none"
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <Button type="submit" size="sm" disabled={submitting}>
        {submitting ? "Creating..." : "Create Experiment"}
      </Button>
    </form>
  );
}

export default function SciencePage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    api.science.experiments.list().then(setExperiments).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleCreated = (exp: Experiment) => {
    setExperiments(prev => [exp, ...prev]);
    setShowForm(false);
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-zinc-100">AI Science Engine</h2>
              <p className="mt-1 text-sm text-zinc-400">
                Hypothesis-driven experiments with AI-powered analysis and publication
              </p>
            </div>
            <Button size="sm" onClick={() => setShowForm(v => !v)}>
              {showForm ? "Cancel" : "+ New Experiment"}
            </Button>
          </div>

          {showForm && <CreateExperimentForm onCreated={handleCreated} />}

          {loading ? (
            <p className="text-sm text-zinc-500">Loading...</p>
          ) : experiments.length === 0 ? (
            <p className="text-sm text-zinc-500">No experiments yet. Create one to begin.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {experiments.map(exp => {
                const confidence = exp.confidence ?? 0;
                return (
                  <Link
                    key={exp.id}
                    href={`/science/${exp.id}`}
                    className="block rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 hover:bg-zinc-800/50 transition-colors space-y-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-semibold text-zinc-100 line-clamp-2 flex-1">{exp.title}</span>
                      <Badge variant="outline" className={STATUS_COLORS[exp.status]}>
                        {exp.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-zinc-400 line-clamp-2">{exp.hypothesis}</p>
                    <div className="flex items-center justify-between text-xs text-zinc-500">
                      <span>{exp.total_runs} runs</span>
                      <span>${exp.total_cost_usd.toFixed(4)}</span>
                    </div>
                    {/* Confidence meter */}
                    {exp.confidence !== null && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-[10px] text-zinc-500">
                          <span>Confidence</span>
                          <span>{Math.round(confidence * 100)}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${confidence >= 0.8 ? "bg-green-500" : confidence >= 0.5 ? "bg-yellow-500" : "bg-red-500"}`}
                            style={{ width: `${confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
