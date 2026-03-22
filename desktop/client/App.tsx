import React, { useState, useEffect, useCallback } from "react";
import useWebSocket from "react-use-websocket";
import Sidebar from "./components/Sidebar";
import PRInputForm from "./components/PRInputForm";
import ReviewPanel from "./components/ReviewPanel";
import SettingsPage from "./components/SettingsPage";

const API = "http://localhost:3001";
const WS = "ws://localhost:3001/ws";

// When running behind Vite proxy, use relative URLs
const apiUrl = (path: string) => {
  if (typeof window !== "undefined" && window.location.port === "5173") return path;
  return `${API}${path}`;
};

interface Review {
  id: string;
  pr_url: string;
  repo_name: string;
  pr_number: number;
  platform: string;
  status: string;
  total_issues: number;
  created_at: string;
  completed_at: string | null;
}

interface Finding {
  id: string;
  agent_role: string;
  severity: string;
  file_path: string;
  line_number: number | null;
  title: string;
  description: string;
  suggested_fix: string | null;
  confidence: number;
}

export default function App() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [agentStates, setAgentStates] = useState<Record<string, string>>({});
  const [isReviewing, setIsReviewing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState("");

  // Fetch reviews on mount
  useEffect(() => {
    fetch(apiUrl("/api/reviews")).then(r => r.json()).then(d => setReviews(d.items || [])).catch(() => {});
  }, []);

  // WebSocket
  const { sendJsonMessage, lastJsonMessage } = useWebSocket(WS, {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  });

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastJsonMessage) return;
    const msg = lastJsonMessage as any;

    switch (msg.type) {
      case "agent:started":
        setAgentStates(prev => ({ ...prev, [msg.agent]: "running" }));
        break;
      case "agent:completed":
        setAgentStates(prev => ({ ...prev, [msg.agent]: "completed" }));
        break;
      case "agent:error":
        setAgentStates(prev => ({ ...prev, [msg.agent]: "error" }));
        break;
      case "finding":
        if (msg.finding) setFindings(prev => [...prev, msg.finding]);
        break;
      case "review:completed":
        setIsReviewing(false);
        // Refresh review list
        fetch(apiUrl("/api/reviews")).then(r => r.json()).then(d => setReviews(d.items || []));
        break;
      case "error":
        setError(msg.error || "Unknown error");
        setIsReviewing(false);
        break;
    }
  }, [lastJsonMessage]);

  const createReview = useCallback(async (prUrl: string) => {
    setError("");
    setFindings([]);
    setAgentStates({});
    setIsReviewing(true);

    try {
      const res = await fetch(apiUrl("/api/reviews"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pr_url: prUrl }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Failed to create review");
      }
      const review = await res.json();
      setSelectedId(review.id);
      setReviews(prev => [review, ...prev]);

      // Subscribe to WebSocket
      sendJsonMessage({ type: "subscribe", reviewId: review.id });
    } catch (err: any) {
      setError(err.message);
      setIsReviewing(false);
    }
  }, [sendJsonMessage]);

  const selectReview = useCallback(async (id: string) => {
    setSelectedId(id);
    setShowSettings(false);
    setError("");
    try {
      const res = await fetch(apiUrl(`/api/reviews/${id}`));
      const data = await res.json();
      setFindings(data.findings || []);
      if (data.status === "running") {
        setIsReviewing(true);
        sendJsonMessage({ type: "subscribe", reviewId: id });
      } else {
        setIsReviewing(false);
      }
    } catch { /* ignore */ }
  }, [sendJsonMessage]);

  return (
    <div className="flex h-screen">
      <Sidebar
        reviews={reviews}
        selectedId={selectedId}
        onSelect={selectReview}
        onNewReview={() => { setSelectedId(null); setShowSettings(false); setFindings([]); }}
        onSettings={() => setShowSettings(true)}
      />
      <main className="flex-1 overflow-auto">
        {showSettings ? (
          <SettingsPage />
        ) : selectedId ? (
          <ReviewPanel
            reviewId={selectedId}
            findings={findings}
            agentStates={agentStates}
            isReviewing={isReviewing}
            error={error}
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-8 p-8">
            <h1 className="text-3xl font-bold text-zinc-100">SwarmForge</h1>
            <p className="text-zinc-400">AI-powered code review with 5 specialist agents</p>
            <PRInputForm onSubmit={createReview} isLoading={isReviewing} />
          </div>
        )}
      </main>
    </div>
  );
}
