import React, { useState } from "react";

interface Props {
  onSubmit: (prUrl: string) => void;
  isLoading: boolean;
}

export default function PRInputForm({ onSubmit, isLoading }: Props) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const isGitHub = /^https?:\/\/github\.com\/[^/]+\/[^/]+\/pull\/\d+/.test(url);
    const isGitLab = /^https?:\/\/[^/]+\/.+\/-\/merge_requests\/\d+/.test(url);
    if (!isGitHub && !isGitLab) {
      setError("Please enter a valid GitHub PR or GitLab MR URL");
      return;
    }
    setError("");
    onSubmit(url);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl space-y-3">
      <div className="flex gap-2">
        <input type="url" value={url} onChange={e => setUrl(e.target.value)}
          placeholder="GitHub PR or GitLab MR URL"
          className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500" />
        <button type="submit" disabled={isLoading || !url}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors">
          {isLoading ? "Reviewing..." : "Review"}
        </button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
    </form>
  );
}
