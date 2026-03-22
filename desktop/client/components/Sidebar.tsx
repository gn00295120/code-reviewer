import React from "react";

interface Review {
  id: string;
  repo_name: string;
  pr_number: number;
  platform: string;
  status: string;
  total_issues: number;
  created_at: string;
}

interface Props {
  reviews: Review[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNewReview: () => void;
  onSettings: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "text-zinc-500",
  running: "text-blue-400",
  completed: "text-green-400",
  failed: "text-red-400",
  cancelled: "text-zinc-600",
};

export default function Sidebar({ reviews, selectedId, onSelect, onNewReview, onSettings }: Props) {
  return (
    <div className="w-72 border-r border-zinc-800 bg-zinc-900 flex flex-col h-full">
      <div className="p-4 border-b border-zinc-800">
        <button onClick={onNewReview} className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors">
          + New Review
        </button>
      </div>
      <div className="flex-1 overflow-auto p-2 space-y-1">
        {reviews.map(r => (
          <button key={r.id} onClick={() => onSelect(r.id)}
            className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${selectedId === r.id ? "bg-zinc-800" : "hover:bg-zinc-800/50"}`}>
            <div className="flex items-center gap-2">
              <span className="text-zinc-500 text-xs">{r.platform === "gitlab" ? "GL" : "GH"}</span>
              <span className="truncate font-medium text-zinc-200">{r.repo_name}</span>
              <span className="text-zinc-500 text-xs">#{r.pr_number}</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-xs ${STATUS_COLORS[r.status] || "text-zinc-500"}`}>{r.status}</span>
              {r.total_issues > 0 && <span className="text-xs text-zinc-500">{r.total_issues} issues</span>}
            </div>
          </button>
        ))}
        {reviews.length === 0 && <p className="text-center text-zinc-600 text-sm p-4">No reviews yet</p>}
      </div>
      <div className="p-4 border-t border-zinc-800">
        <button onClick={onSettings} className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors">Settings</button>
      </div>
    </div>
  );
}
