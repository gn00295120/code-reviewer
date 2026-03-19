"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { ReviewFlowCanvas } from "@/components/review/ReviewFlowCanvas";
import { FindingsPanel } from "@/components/review/FindingsPanel";
import { CostTracker } from "@/components/review/CostTracker";
import { ReviewSummaryCard } from "@/components/review/ReviewSummaryCard";
import { PostToGithubButton } from "@/components/review/PostToGithubButton";
import { QueueStatus } from "@/components/review/QueueStatus";
import { useReviewWebSocket } from "@/hooks/use-review-websocket";
import { useReviewStore } from "@/stores/review-store";
import { api } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ReviewDetailPage() {
  const params = useParams();
  const reviewId = params.id as string;
  const { setCurrentReview, setReviewStatus, updateCost, reviewStatus } = useReviewStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Connect WebSocket for live updates
  useReviewWebSocket(reviewId);

  // Fetch initial review data
  useEffect(() => {
    if (!reviewId) return;
    api.reviews.get(reviewId).then((review) => {
      setCurrentReview(review);
      setReviewStatus(review.status);
      // Seed cost from loaded review
      if (review.total_cost_usd) {
        updateCost(Number(review.total_cost_usd));
      }
      setLoading(false);
    }).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load review");
      setLoading(false);
    });

    return () => {
      setCurrentReview(null);
      setReviewStatus("idle");
    };
  }, [reviewId, setCurrentReview, setReviewStatus, updateCost]);

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-zinc-500">Loading review...</p>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-red-400">{error}</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-6xl space-y-4">
          {/* Status bar */}
          <div className="flex items-center justify-between">
            <CostTracker />
            <div className="flex items-center gap-4">
              <QueueStatus />
              <PostToGithubButton
                reviewId={reviewId}
                disabled={reviewStatus !== "completed"}
              />
            </div>
          </div>

          {/* React Flow Canvas */}
          <ReviewFlowCanvas />

          {/* Tabs: Findings / Summary */}
          <Tabs defaultValue="findings" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="findings">Findings</TabsTrigger>
              <TabsTrigger value="summary">Summary</TabsTrigger>
            </TabsList>
            <TabsContent value="findings" className="mt-4">
              <FindingsPanel />
            </TabsContent>
            <TabsContent value="summary" className="mt-4">
              <ReviewSummaryCard />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
