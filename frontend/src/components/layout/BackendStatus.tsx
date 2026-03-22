"use client";

import { useEffect, useState } from "react";

export function BackendStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("http://localhost:8000/health", { signal: AbortSignal.timeout(3000) });
        setStatus(res.ok ? "online" : "offline");
      } catch {
        setStatus("offline");
      }
    };

    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  const colors = {
    checking: "bg-zinc-500",
    online: "bg-green-500",
    offline: "bg-red-500",
  };

  const labels = {
    checking: "Checking...",
    online: "Backend Online",
    offline: "Backend Offline",
  };

  return (
    <div className="flex items-center gap-2 text-xs text-zinc-500">
      <span className={`inline-block h-2 w-2 rounded-full ${colors[status]}`} />
      {labels[status]}
    </div>
  );
}
