"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { PRInputForm } from "@/components/review/PRInputForm";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { Review } from "@/types/review";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900/50 text-blue-300",
  completed: "bg-green-900/50 text-green-300",
  failed: "bg-red-900/50 text-red-300",
  cancelled: "bg-zinc-800 text-zinc-400",
};

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.reviews.list({ limit: 50 }).then((res) => {
      setReviews(res.items);
      setLoading(false);
    }).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load reviews");
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <h2 className="text-2xl font-bold text-zinc-100">Code Reviews</h2>

          <PRInputForm />

          {loading ? (
            <p className="text-zinc-500 text-sm">Loading...</p>
          ) : error ? (
            <p className="text-red-400 text-sm">{error}</p>
          ) : reviews.length === 0 ? (
            <p className="text-zinc-500 text-sm">No reviews yet. Create one above.</p>
          ) : (
            <div className="space-y-2">
              {reviews.map((review) => (
                <Link
                  key={review.id}
                  href={`/reviews/${review.id}`}
                  className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 hover:bg-zinc-800/50 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-zinc-200">{review.repo_name}</span>
                      {review.pr_number != null && (
                        <span className="text-xs text-zinc-500">#{review.pr_number}</span>
                      )}
                      <Badge variant="outline" className={STATUS_COLORS[review.status]}>
                        {review.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-zinc-500 font-mono">{review.pr_url}</p>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-zinc-500">
                    <span>{review.total_issues} issues</span>
                    <span>${Number(review.total_cost_usd).toFixed(4)}</span>
                    <span>{new Date(review.created_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
