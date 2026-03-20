"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { MarketplaceListing } from "@/types/marketplace";

function StarRating({
  rating,
  count,
  interactive,
  onRate,
}: {
  rating: number;
  count: number;
  interactive?: boolean;
  onRate?: (stars: number) => void;
}) {
  const [hover, setHover] = useState(0);
  const display = hover || rating;

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 5 }).map((_, i) => (
        <button
          key={i}
          disabled={!interactive}
          onClick={() => onRate?.(i + 1)}
          onMouseEnter={() => interactive && setHover(i + 1)}
          onMouseLeave={() => interactive && setHover(0)}
          className={`focus:outline-none ${interactive ? "cursor-pointer" : "cursor-default"}`}
        >
          <svg
            className={`h-5 w-5 transition-colors ${
              i < display ? "text-yellow-400 fill-yellow-400" : "text-zinc-600 fill-zinc-600"
            }`}
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </button>
      ))}
      <span className="text-sm text-zinc-400 ml-1">{rating.toFixed(1)} ({count} ratings)</span>
    </div>
  );
}

function TypeBadge({ type }: { type: string }) {
  const styles: Record<string, string> = {
    template: "bg-blue-900/50 text-blue-300 border-blue-700",
    org: "bg-purple-900/50 text-purple-300 border-purple-700",
    agent: "bg-green-900/50 text-green-300 border-green-700",
  };
  return (
    <Badge variant="outline" className={styles[type] ?? "bg-zinc-800 text-zinc-300"}>
      {type}
    </Badge>
  );
}

export default function MarketplaceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [listing, setListing] = useState<MarketplaceListing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [installing, setInstalling] = useState(false);
  const [rating, setRating] = useState(false);
  const [showRater, setShowRater] = useState(false);

  useEffect(() => {
    api.marketplace.get(id).then((l) => {
      setListing(l);
      setLoading(false);
    }).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load listing");
      setLoading(false);
    });
  }, [id]);

  const handleInstall = async () => {
    if (!listing) return;
    setInstalling(true);
    try {
      await api.marketplace.install(listing.id);
    } catch {}
    setInstalling(false);
  };

  const handleRate = async (stars: number) => {
    if (!listing) return;
    setRating(true);
    try {
      const result = await api.marketplace.rate(listing.id, stars);
      setListing((prev) =>
        prev ? { ...prev, rating: result.rating, rating_count: result.rating_count } : prev
      );
      setShowRater(false);
    } catch {}
    setRating(false);
  };

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-zinc-500">Loading listing...</p>
        </main>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-red-400">{error || "Listing not found"}</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {/* Back */}
          <button
            onClick={() => router.back()}
            className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition-colors"
          >
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to Marketplace
          </button>

          {/* Header */}
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <TypeBadge type={listing.listing_type} />
                  <span className="text-xs text-zinc-500">v{listing.version}</span>
                </div>
                <h2 className="text-2xl font-bold text-zinc-100">{listing.title}</h2>
                <p className="text-sm text-zinc-400">by {listing.author}</p>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-zinc-700"
                  onClick={() => setShowRater(!showRater)}
                  disabled={rating}
                >
                  Rate
                </Button>
                <Button
                  onClick={handleInstall}
                  disabled={installing}
                  className="bg-blue-600 hover:bg-blue-500 text-white"
                >
                  {installing ? "Installing..." : "Install"}
                </Button>
              </div>
            </div>

            {/* Rating */}
            <div className="space-y-2">
              <StarRating rating={listing.rating} count={listing.rating_count} />
              {showRater && (
                <div className="p-3 rounded-lg border border-zinc-700 bg-zinc-900 space-y-2">
                  <p className="text-xs text-zinc-400">Select your rating:</p>
                  <StarRating
                    rating={0}
                    count={0}
                    interactive
                    onRate={handleRate}
                  />
                </div>
              )}
            </div>

            <div className="flex items-center gap-4 text-xs text-zinc-500">
              <span>{listing.downloads.toLocaleString()} downloads</span>
              <span>Published {new Date(listing.created_at).toLocaleDateString()}</span>
            </div>
          </div>

          {/* Tags */}
          {listing.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {listing.tags.map((tag) => (
                <span key={tag} className="rounded px-2 py-1 text-xs bg-zinc-800 text-zinc-400">
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Description */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
            <h3 className="text-sm font-medium text-zinc-200">Description</h3>
            <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
              {listing.description}
            </p>
          </div>

          {/* Config preview */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
            <h3 className="text-sm font-medium text-zinc-200">Configuration Preview</h3>
            <pre className="text-xs text-zinc-400 overflow-auto max-h-64 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-zinc-700 bg-zinc-950 rounded p-3">
              {JSON.stringify(listing.config, null, 2)}
            </pre>
          </div>
        </div>
      </main>
    </div>
  );
}
