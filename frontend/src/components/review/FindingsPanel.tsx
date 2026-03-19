"use client";

import { useReviewStore } from "@/stores/review-store";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Finding, Severity } from "@/types/review";

const SEVERITY_COLORS: Record<Severity, string> = {
  high: "bg-red-900/50 text-red-300 border-red-700",
  medium: "bg-yellow-900/50 text-yellow-300 border-yellow-700",
  low: "bg-blue-900/50 text-blue-300 border-blue-700",
  info: "bg-zinc-800 text-zinc-300 border-zinc-600",
};

const AGENT_LABELS: Record<string, string> = {
  logic: "Logic",
  security: "Security",
  edge_case: "Edge Cases",
  convention: "Convention",
  performance: "Performance",
};

function FindingCard({ finding }: { finding: Finding }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-zinc-100">{finding.title}</h4>
        <Badge variant="outline" className={SEVERITY_COLORS[finding.severity]}>
          {finding.severity.toUpperCase()}
        </Badge>
      </div>
      <p className="text-xs text-zinc-400">{finding.description}</p>
      <div className="flex items-center gap-3 text-xs text-zinc-500">
        <span className="font-mono">{finding.file_path}{finding.line_number ? `:${finding.line_number}` : ""}</span>
        <span>{AGENT_LABELS[finding.agent_role] || finding.agent_role}</span>
        <span>{Math.round(finding.confidence * 100)}%</span>
      </div>
      {finding.suggested_fix && (
        <pre className="mt-2 rounded bg-zinc-950 p-2 text-xs text-green-400 overflow-x-auto">
          {finding.suggested_fix}
        </pre>
      )}
    </div>
  );
}

export function FindingsPanel() {
  const { liveFindings, currentReview, severityFilter, setSeverityFilter } = useReviewStore();

  const findings = currentReview?.findings?.length ? currentReview.findings : liveFindings;

  const filtered = severityFilter
    ? findings.filter((f) => f.severity === severityFilter)
    : findings;

  const severityCounts = findings.reduce(
    (acc, f) => {
      acc[f.severity] = (acc[f.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="flex flex-col gap-3">
      {/* Severity filter pills */}
      <div className="flex gap-2">
        <button
          onClick={() => setSeverityFilter(null)}
          className={`rounded-full px-3 py-1 text-xs ${!severityFilter ? "bg-zinc-700 text-white" : "bg-zinc-900 text-zinc-400"}`}
        >
          All ({findings.length})
        </button>
        {(["high", "medium", "low", "info"] as Severity[]).map((sev) => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(severityFilter === sev ? null : sev)}
            className={`rounded-full px-3 py-1 text-xs ${severityFilter === sev ? "bg-zinc-700 text-white" : "bg-zinc-900 text-zinc-400"}`}
          >
            {sev.toUpperCase()} ({severityCounts[sev] || 0})
          </button>
        ))}
      </div>

      {/* Findings list */}
      <ScrollArea className="h-[400px]">
        <div className="space-y-2 pr-4">
          {filtered.length === 0 ? (
            <p className="text-center text-sm text-zinc-500 py-8">
              No findings yet. Start a review to see results.
            </p>
          ) : (
            filtered.map((finding, i) => <FindingCard key={finding.id || i} finding={finding} />)
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
