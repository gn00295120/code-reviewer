"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { ReviewFlowCanvas } from "@/components/review/ReviewFlowCanvas";
import { FindingsPanel } from "@/components/review/FindingsPanel";
import { CostTracker } from "@/components/review/CostTracker";
import { ReviewSummaryCard } from "@/components/review/ReviewSummaryCard";
import { PostToGithubButton } from "@/components/review/PostToGithubButton";
import { QueueStatus } from "@/components/review/QueueStatus";
import { ReplayTimeline } from "@/components/review/ReplayTimeline";
import { useReviewWebSocket } from "@/hooks/use-review-websocket";
import { useReviewStore } from "@/stores/review-store";
import { api } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ReviewDetailPage() {
  const params = useParams();
  const reviewId = params.id as string;
  const {
    setCurrentReview,
    setReviewStatus,
    updateCost,
    reviewStatus,
    setReplayMode,
    setReplayEvents,
    setReplayIndex,
    replayMode,
  } = useReviewStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timelineLoading, setTimelineLoading] = useState(false);

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
      setReplayMode(false);
    };
  }, [reviewId, setCurrentReview, setReviewStatus, updateCost, setReplayMode]);

  const handleReplayTabSelect = useCallback(
    async (value: string) => {
      if (value !== "replay") return;
      if (timelineLoading) return;
      setTimelineLoading(true);
      try {
        const events = await api.reviews.timeline(reviewId);
        setReplayEvents(events);
        setReplayIndex(0);
        setReplayMode(true);
      } catch {
        // silently ignore — ReplayTimeline handles empty state
      } finally {
        setTimelineLoading(false);
      }
    },
    [reviewId, timelineLoading, setReplayEvents, setReplayIndex, setReplayMode],
  );

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

          {/* Tabs: Findings / Summary / Replay */}
          <Tabs defaultValue="findings" className="w-full" onValueChange={handleReplayTabSelect}>
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="findings">Findings</TabsTrigger>
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="replay" disabled={reviewStatus !== "completed"}>
                {timelineLoading ? "Loading..." : "Replay"}
              </TabsTrigger>
            </TabsList>
            <TabsContent value="findings" className="mt-4">
              <FindingsPanel />
            </TabsContent>
            <TabsContent value="summary" className="mt-4">
              <ReviewSummaryCard />
            </TabsContent>
            <TabsContent value="replay" className="mt-4">
              {replayMode ? (
                <ReplayTimeline />
              ) : (
                <div className="flex items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950 p-8 text-zinc-500">
                  {timelineLoading ? "Loading timeline..." : "Select this tab on a completed review to start replay."}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
