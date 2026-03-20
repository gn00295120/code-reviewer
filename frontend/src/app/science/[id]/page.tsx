"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { Experiment, ExperimentRun } from "@/types/science";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900/50 text-blue-300 border-blue-800",
  analyzing: "bg-purple-900/50 text-purple-300 border-purple-800",
  completed: "bg-green-900/50 text-green-300 border-green-800",
  published: "bg-yellow-900/50 text-yellow-300 border-yellow-800",
};

const RUN_STATUS_COLORS: Record<string, string> = {
  pending: "bg-zinc-700 text-zinc-400",
  running: "bg-blue-900/50 text-blue-300",
  completed: "bg-green-900/50 text-green-300",
  failed: "bg-red-900/50 text-red-300",
};

function DesignTab({ experiment }: { experiment: Experiment }) {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
        <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide">Hypothesis</h3>
        <p className="text-sm text-zinc-200">{experiment.hypothesis}</p>
      </div>
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
        <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide">Methodology</h3>
        <p className="text-sm text-zinc-200 whitespace-pre-wrap">{experiment.methodology || "—"}</p>
      </div>
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
        <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide">Variables</h3>
        <pre className="text-xs text-zinc-300 font-mono overflow-auto">
          {JSON.stringify(experiment.variables, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function RunsTab({ experiment, runs, onNewRun, onAnalyze }: {
  experiment: Experiment;
  runs: ExperimentRun[];
  onNewRun: (run: ExperimentRun) => void;
  onAnalyze: (updated: Experiment) => void;
}) {
  const [running, setRunning] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const handleRun = async () => {
    setRunning(true);
    try {
      const run = await api.science.run(experiment.id);
      onNewRun(run);
    } catch (err) {
      console.error("Run failed:", err);
    } finally {
      setRunning(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const updated = await api.science.analyze(experiment.id);
      onAnalyze(updated);
    } catch (err) {
      console.error("Analyze failed:", err);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={handleRun}
          disabled={running || experiment.status === "published"}
        >
          {running ? "Running..." : "New Run"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={handleAnalyze}
          disabled={analyzing || runs.length === 0 || experiment.status === "published"}
        >
          {analyzing ? "Analyzing..." : "Analyze"}
        </Button>
      </div>

      {runs.length === 0 ? (
        <p className="text-xs text-zinc-500">No runs yet. Start a run above.</p>
      ) : (
        <div className="rounded-lg border border-zinc-800 overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-zinc-900 border-b border-zinc-800">
              <tr>
                <th className="text-left px-3 py-2 text-zinc-400 font-medium">Run #</th>
                <th className="text-left px-3 py-2 text-zinc-400 font-medium">Status</th>
                <th className="text-left px-3 py-2 text-zinc-400 font-medium">Duration</th>
                <th className="text-left px-3 py-2 text-zinc-400 font-medium">Cost</th>
                <th className="text-left px-3 py-2 text-zinc-400 font-medium">Parameters</th>
                <th className="text-left px-3 py-2 text-zinc-400 font-medium">Metrics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {runs.map(run => (
                <tr key={run.id} className="hover:bg-zinc-800/30">
                  <td className="px-3 py-2 text-zinc-300 font-medium">#{run.run_number}</td>
                  <td className="px-3 py-2">
                    <Badge variant="outline" className={RUN_STATUS_COLORS[run.status]}>
                      {run.status}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-zinc-400">
                    {run.duration_seconds != null ? `${run.duration_seconds}s` : "—"}
                  </td>
                  <td className="px-3 py-2 text-zinc-400">${run.cost_usd.toFixed(4)}</td>
                  <td className="px-3 py-2 text-zinc-500 font-mono max-w-xs truncate">
                    {JSON.stringify(run.parameters)}
                  </td>
                  <td className="px-3 py-2 text-zinc-500 font-mono max-w-xs truncate">
                    {run.metrics ? JSON.stringify(run.metrics) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AnalysisTab({ experiment, onPublish }: {
  experiment: Experiment;
  onPublish: (updated: Experiment) => void;
}) {
  const [publishing, setPublishing] = useState(false);

  const handlePublish = async () => {
    setPublishing(true);
    try {
      const updated = await api.science.publish(experiment.id);
      onPublish(updated);
    } catch (err) {
      console.error("Publish failed:", err);
    } finally {
      setPublishing(false);
    }
  };

  const confidence = experiment.confidence ?? 0;

  return (
    <div className="space-y-4">
      {!experiment.analysis ? (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6 text-center">
          <p className="text-sm text-zinc-500">No analysis yet. Run experiments and click "Analyze" in the Runs tab.</p>
        </div>
      ) : (
        <>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
            <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide">AI Analysis</h3>
            <p className="text-sm text-zinc-200 whitespace-pre-wrap">{experiment.analysis}</p>
          </div>

          {experiment.conclusion && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
              <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide">Conclusion</h3>
              <p className="text-sm text-zinc-200">{experiment.conclusion}</p>
            </div>
          )}

          {experiment.confidence !== null && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide">Confidence Score</h3>
                <span className={`text-sm font-bold ${confidence >= 0.8 ? "text-green-400" : confidence >= 0.5 ? "text-yellow-400" : "text-red-400"}`}>
                  {Math.round(confidence * 100)}%
                </span>
              </div>
              <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${confidence >= 0.8 ? "bg-green-500" : confidence >= 0.5 ? "bg-yellow-500" : "bg-red-500"}`}
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
            </div>
          )}

          {experiment.status !== "published" && (
            <Button
              size="sm"
              onClick={handlePublish}
              disabled={publishing}
            >
              {publishing ? "Publishing..." : "Publish Experiment"}
            </Button>
          )}

          {experiment.status === "published" && (
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-yellow-900/50 text-yellow-300 border-yellow-800">
                Published
              </Badge>
              <span className="text-xs text-zinc-500">This experiment has been published.</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function ScienceDetailPage() {
  const params = useParams();
  const experimentId = params.id as string;

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    try {
      const [exp, expRuns] = await Promise.all([
        api.science.experiments.get(experimentId),
        api.science.runs(experimentId).catch(() => []),
      ]);
      setExperiment(exp);
      setRuns(expRuns);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load experiment");
    } finally {
      setLoading(false);
    }
  }, [experimentId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-zinc-500">Loading experiment...</p>
        </main>
      </div>
    );
  }

  if (error || !experiment) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-red-400">{error || "Experiment not found"}</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Header */}
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-zinc-100">{experiment.title}</h2>
              <Badge variant="outline" className={STATUS_COLORS[experiment.status]}>
                {experiment.status}
              </Badge>
            </div>
            <div className="flex items-center gap-4 mt-1 text-xs text-zinc-500">
              <span>{experiment.total_runs} runs</span>
              <span>${experiment.total_cost_usd.toFixed(4)} total cost</span>
              <span>created {new Date(experiment.created_at).toLocaleDateString()}</span>
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="design" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="design">Design</TabsTrigger>
              <TabsTrigger value="runs">Runs ({runs.length})</TabsTrigger>
              <TabsTrigger value="analysis">Analysis</TabsTrigger>
            </TabsList>

            <TabsContent value="design" className="mt-4">
              <DesignTab experiment={experiment} />
            </TabsContent>

            <TabsContent value="runs" className="mt-4">
              <RunsTab
                experiment={experiment}
                runs={runs}
                onNewRun={run => setRuns(prev => [run, ...prev])}
                onAnalyze={updated => setExperiment(updated)}
              />
            </TabsContent>

            <TabsContent value="analysis" className="mt-4">
              <AnalysisTab
                experiment={experiment}
                onPublish={updated => setExperiment(updated)}
              />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
