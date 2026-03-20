"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { MarketplaceListing } from "@/types/marketplace";

const LISTING_TYPES = ["", "template", "org", "agent"] as const;
const SORT_OPTIONS = [
  { value: "downloads", label: "Most Downloaded" },
  { value: "rating", label: "Top Rated" },
  { value: "newest", label: "Newest" },
];

function StarRating({ rating, count }: { rating: number; count: number }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 5 }).map((_, i) => (
        <svg
          key={i}
          className={`h-3 w-3 ${
            i < full
              ? "text-yellow-400 fill-yellow-400"
              : i === full && half
              ? "text-yellow-400 fill-yellow-400 opacity-50"
              : "text-zinc-600 fill-zinc-600"
          }`}
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
      <span className="text-xs text-zinc-500 ml-1">({count})</span>
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

export default function MarketplacePage() {
  const [listings, setListings] = useState<MarketplaceListing[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [sort, setSort] = useState("downloads");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.marketplace.browse({
        q: search || undefined,
        type: typeFilter || undefined,
        sort,
        limit: 48,
      });
      setListings(result.items);
      setTotal(result.total);
    } catch {
      setListings([]);
      setTotal(0);
    }
    setLoading(false);
  }, [search, typeFilter, sort]);

  useEffect(() => {
    load();
  }, [load]);

  const handleInstall = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    setInstalling(id);
    try {
      await api.marketplace.install(id);
    } catch {}
    setInstalling(null);
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-zinc-100">Marketplace</h2>
              <p className="mt-1 text-sm text-zinc-400">
                Browse, install, and publish templates, orgs, and agents
              </p>
            </div>
            <Link href="/marketplace/publish">
              <Button className="bg-blue-600 hover:bg-blue-500 text-white">Publish</Button>
            </Link>
          </div>

          {/* Search + Filters */}
          <div className="flex gap-3 flex-wrap">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search marketplace..."
              className="flex-1 min-w-48 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
            />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
            >
              {LISTING_TYPES.map((t) => (
                <option key={t} value={t}>{t || "All types"}</option>
              ))}
            </select>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <p className="text-xs text-zinc-500">{total} listings</p>

          {loading ? (
            <p className="text-sm text-zinc-500">Loading...</p>
          ) : listings.length === 0 ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-12 text-center">
              <p className="text-sm text-zinc-500">No listings found. Be the first to publish!</p>
              <Link href="/marketplace/publish" className="mt-3 inline-block">
                <Button variant="outline" size="sm" className="border-zinc-700 mt-3">Publish Now</Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {listings.map((listing) => (
                <Link key={listing.id} href={`/marketplace/${listing.id}`} className="block group">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-3 hover:border-zinc-600 hover:bg-zinc-800/50 transition-colors h-full">
                    <div className="flex items-start justify-between gap-2">
                      <TypeBadge type={listing.listing_type} />
                      <span className="text-xs text-zinc-500 shrink-0">v{listing.version}</span>
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-zinc-100 group-hover:text-white transition-colors">
                        {listing.title}
                      </h3>
                      <p className="text-xs text-zinc-500 mt-0.5">by {listing.author}</p>
                    </div>

                    <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
                      {listing.description}
                    </p>

                    {listing.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {listing.tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="rounded px-1.5 py-0.5 text-[10px] bg-zinc-800 text-zinc-400"
                          >
                            {tag}
                          </span>
                        ))}
                        {listing.tags.length > 3 && (
                          <span className="text-[10px] text-zinc-600">+{listing.tags.length - 3}</span>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-1">
                      <div className="space-y-1">
                        <StarRating rating={listing.rating} count={listing.rating_count} />
                        <p className="text-[10px] text-zinc-600">
                          {listing.downloads.toLocaleString()} downloads
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-zinc-700 text-xs h-7 hover:border-blue-500 hover:text-blue-400"
                        onClick={(e) => handleInstall(e, listing.id)}
                        disabled={installing === listing.id}
                      >
                        {installing === listing.id ? "Installing..." : "Install"}
                      </Button>
                    </div>
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
