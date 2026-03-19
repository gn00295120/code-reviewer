"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface Props {
  reviewId: string;
  disabled?: boolean;
}

export function PostToGithubButton({ reviewId, disabled }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ posted: number; message: string } | null>(null);
  const [error, setError] = useState("");

  const handlePost = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.reviews.postToGithub(reviewId);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to post");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-3">
      <Button
        onClick={handlePost}
        disabled={disabled || loading}
        variant="outline"
        className="border-zinc-700 text-zinc-200 hover:bg-zinc-800"
      >
        {loading ? "Posting..." : "Post to GitHub"}
      </Button>
      {result && (
        <span className="text-xs text-green-400">{result.message}</span>
      )}
      {error && (
        <span className="text-xs text-red-400">{error}</span>
      )}
    </div>
  );
}
