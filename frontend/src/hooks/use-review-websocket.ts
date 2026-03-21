"use client";

import { useEffect, useRef, useCallback } from "react";
import { useReviewStore } from "@/stores/review-store";
import type { AgentRole, Finding, WSEvent } from "@/types/review";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL
  || (typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
    : "ws://localhost:8000");
const RECONNECT_DELAY = 3000;

export function useReviewWebSocket(reviewId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const {
    updateAgentState,
    addLiveFinding,
    updateCost,
    setReviewStatus,
    setSummary,
    resetAgentStates,
    clearLiveFindings,
  } = useReviewStore();

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      let msg: WSEvent;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return; // Ignore non-JSON frames (ping/pong, malformed)
      }

      switch (msg.event) {
        case "review:started":
          setReviewStatus("running");
          resetAgentStates();
          clearLiveFindings();
          break;

        case "review:agent:started":
          updateAgentState(msg.data.agent as AgentRole, { status: "running" });
          break;

        case "review:agent:completed":
          updateAgentState(msg.data.agent as AgentRole, {
            status: "completed",
            findings_count: msg.data.findings_count as number,
            tokens: msg.data.tokens as number,
            cost_usd: msg.data.cost_usd as number,
          });
          updateCost(msg.data.cost_usd as number);
          break;

        case "review:agent:error":
          updateAgentState(msg.data.agent as AgentRole, { status: "error" });
          break;

        case "review:finding":
          addLiveFinding(msg.data as unknown as Finding);
          break;

        case "review:completed":
          setReviewStatus("completed");
          setSummary(msg.data.summary as string);
          break;

        case "review:failed":
          setReviewStatus("failed");
          break;
      }
    },
    [updateAgentState, addLiveFinding, updateCost, setReviewStatus, setSummary, resetAgentStates, clearLiveFindings]
  );

  useEffect(() => {
    if (!reviewId) return;

    function connect() {
      const ws = new WebSocket(`${WS_URL}/ws/reviews/${reviewId}`);
      wsRef.current = ws;

      ws.onmessage = handleMessage;

      ws.onerror = () => {
        // Error fires before close — handled in onclose for reconnection
      };

      ws.onclose = () => {
        wsRef.current = null;
        // Auto-reconnect unless intentionally closed
        const status = useReviewStore.getState().reviewStatus;
        if (status === "running" || status === "pending") {
          reconnectRef.current = setTimeout(connect, RECONNECT_DELAY);
        }
      };
    }

    connect();

    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect on intentional close
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [reviewId, handleMessage]);
}
