"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function PRInputForm() {
  const [prUrl, setPrUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const isGitHub = /^https?:\/\/github\.com\/[^/]+\/[^/]+\/pull\/\d+([/?#]|$)/.test(prUrl);
    const isGitLab = !isGitHub && /^https?:\/\/[^/]+\/.+\/-\/merge_requests\/\d+([/?#]|$)/.test(prUrl);
    if (!isGitHub && !isGitLab) {
      setError("Please enter a valid GitHub PR or GitLab MR URL");
      return;
    }

    setLoading(true);
    try {
      const review = await api.reviews.create(prUrl);
      router.push(`/reviews/${review.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create review");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex gap-2">
        <input
          type="url"
          value={prUrl}
          onChange={(e) => setPrUrl(e.target.value)}
          placeholder="GitHub PR or GitLab MR URL"
          className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <Button type="submit" disabled={loading || !prUrl} className="px-6">
          {loading ? "Starting..." : "Review"}
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
    </form>
  );
}
