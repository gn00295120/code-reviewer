import React, { useState } from "react";

interface Finding {
  id: string;
  agent_role: string;
  severity: string;
  file_path: string;
  line_number: number | null;
  title: string;
  description: string;
  suggested_fix: string | null;
  confidence: number;
}

const SEVERITY_COLORS: Record<string, { border: string; badge: string }> = {
  high: { border: "border-red-800", badge: "bg-red-900/50 text-red-300" },
  medium: { border: "border-yellow-800", badge: "bg-yellow-900/50 text-yellow-300" },
  low: { border: "border-cyan-800", badge: "bg-cyan-900/50 text-cyan-300" },
  info: { border: "border-zinc-700", badge: "bg-zinc-800 text-zinc-400" },
};

const SEVERITY_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2, info: 3 };

interface Props {
  findings: Finding[];
}

export default function FindingsPanel({ findings }: Props) {
  const [filter, setFilter] = useState<string | null>(null);

  if (findings.length === 0) return (
    <div className="text-center text-zinc-600 py-12">
      {findings.length === 0 ? "No findings yet — review in progress or no issues found" : "No findings match filter"}
    </div>
  );

  const sorted = [...findings]
    .filter(f => !filter || f.severity === filter)
    .sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3));

  const counts: Record<string, number> = {};
  for (const f of findings) counts[f.severity] = (counts[f.severity] || 0) + 1;

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-zinc-300">{findings.length} findings</span>
        <div className="flex gap-2">
          {["high", "medium", "low", "info"].map(sev => {
            if (!counts[sev]) return null;
            const active = filter === sev;
            return (
              <button key={sev} onClick={() => setFilter(active ? null : sev)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${active ? SEVERITY_COLORS[sev].badge + " ring-1 ring-white/20" : SEVERITY_COLORS[sev].badge + " opacity-70 hover:opacity-100"}`}>
                {sev.toUpperCase()} ({counts[sev]})
              </button>
            );
          })}
        </div>
      </div>

      {/* Finding cards */}
      {sorted.map(f => {
        const colors = SEVERITY_COLORS[f.severity] || SEVERITY_COLORS.info;
        return (
          <div key={f.id} className={`border ${colors.border} rounded-lg p-4 bg-zinc-900/50 space-y-2`}>
            <div className="flex items-center gap-3">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors.badge}`}>{f.severity.toUpperCase()}</span>
              <span className="text-sm font-medium text-zinc-100">{f.title}</span>
            </div>
            <div className="text-xs text-zinc-500">
              {f.file_path}{f.line_number ? `:${f.line_number}` : ""} | {f.agent_role} | {Math.round(f.confidence * 100)}%
            </div>
            <p className="text-sm text-zinc-300">{f.description}</p>
            {f.suggested_fix && (
              <pre className="text-xs bg-zinc-950 border border-zinc-800 rounded p-3 text-green-300 overflow-x-auto">{f.suggested_fix}</pre>
            )}
          </div>
        );
      })}
    </div>
  );
}
