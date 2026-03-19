"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function QueueStatus() {
  const [queue, setQueue] = useState<{ active: number; max_concurrent: number; available: number } | null>(null);

  useEffect(() => {
    const fetch = () => {
      api.stats.queue().then(setQueue).catch(() => {});
    };
    fetch();
    const interval = setInterval(fetch, 10_000);
    return () => clearInterval(interval);
  }, []);

  if (!queue) return null;

  const pct = (queue.active / queue.max_concurrent) * 100;

  return (
    <div className="flex items-center gap-3 text-xs">
      <span className="text-zinc-500">Queue:</span>
      <div className="h-1.5 w-20 rounded-full bg-zinc-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${pct > 80 ? "bg-red-500" : pct > 50 ? "bg-yellow-500" : "bg-green-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-zinc-400">
        {queue.active}/{queue.max_concurrent}
      </span>
    </div>
  );
}
