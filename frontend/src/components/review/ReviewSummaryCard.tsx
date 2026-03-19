"use client";

import { useReviewStore } from "@/stores/review-store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ReviewSummaryCard() {
  const { summary, reviewStatus, liveFindings, currentReview, totalCost } = useReviewStore();

  const findings = currentReview?.findings?.length ? currentReview.findings : liveFindings;

  if (reviewStatus !== "completed" || !currentReview) return null;

  const severityCounts = findings.reduce(
    (acc, f) => {
      acc[f.severity] = (acc[f.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <Card className="border-zinc-800 bg-zinc-900/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg text-zinc-100">Review Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Severity bars */}
        <div className="flex gap-3">
          {[
            { key: "high", color: "bg-red-500", label: "High" },
            { key: "medium", color: "bg-yellow-500", label: "Medium" },
            { key: "low", color: "bg-blue-500", label: "Low" },
          ].map(({ key, color, label }) => (
            <div key={key} className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-sm ${color}`} />
              <span className="text-xs text-zinc-400">
                {label}: <span className="text-zinc-200 font-medium">{severityCounts[key] || 0}</span>
              </span>
            </div>
          ))}
        </div>

        {/* Summary text */}
        {summary && (
          <div className="text-sm text-zinc-300 whitespace-pre-line">{summary}</div>
        )}

        {/* Stats */}
        <div className="flex gap-4 text-xs text-zinc-500 pt-1">
          <span>Total: {findings.length} issues</span>
          <span>Files: {new Set(findings.map((f) => f.file_path)).size}</span>
          <span>Cost: ${totalCost.toFixed(4)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
