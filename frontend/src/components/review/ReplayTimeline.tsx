"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useReviewStore } from "@/stores/review-store";
import type { AgentRole, ReviewEvent } from "@/types/review";

const PLAY_INTERVAL_MS = 500;

type StoreState = ReturnType<typeof useReviewStore.getState>;

function applyEventToStore(
  event: ReviewEvent,
  updateAgentState: StoreState["updateAgentState"],
  addLiveFinding: StoreState["addLiveFinding"],
  setReviewStatus: StoreState["setReviewStatus"],
  setSummary: StoreState["setSummary"],
) {
  const { event_type, event_data } = event;

  switch (event_type) {
    case "review:started":
      setReviewStatus("running");
      break;

    case "review:agent:started": {
      const role = event_data.agent as string;
      if (role && role !== "fetch_diff") {
        updateAgentState(role as AgentRole, { status: "running" });
      }
      break;
    }

    case "review:agent:completed": {
      const role = event_data.agent as string;
      if (role && role !== "fetch_diff") {
        updateAgentState(role as AgentRole, {
          status: "completed",
          findings_count: (event_data.findings_count as number) || 0,
          tokens: (event_data.tokens_used as number) || 0,
          cost_usd: (event_data.cost_usd as number) || 0,
        });
      }
      break;
    }

    case "review:finding": {
      const finding = event_data as unknown as Parameters<typeof addLiveFinding>[0];
      if (finding && finding.id) {
        addLiveFinding(finding);
      }
      break;
    }

    case "review:completed":
      setReviewStatus("completed");
      if (event_data.summary) {
        setSummary(event_data.summary as string);
      }
      break;

    case "review:failed":
      setReviewStatus("failed");
      break;

    default:
      break;
  }
}

export function ReplayTimeline() {
  const {
    replayEvents,
    replayIndex,
    setReplayIndex,
    replayMode,
    setReplayMode,
    updateAgentState,
    resetAgentStates,
    addLiveFinding,
    clearLiveFindings,
    setReviewStatus,
    setSummary,
  } = useReviewStore();

  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const total = replayEvents.length;

  // Apply all events up to (and including) targetIndex
  const applyUpTo = useCallback(
    (targetIndex: number) => {
      resetAgentStates();
      clearLiveFindings();
      setReviewStatus("idle");
      setSummary("");

      for (let i = 0; i <= targetIndex && i < total; i++) {
        applyEventToStore(
          replayEvents[i],
          updateAgentState,
          addLiveFinding,
          setReviewStatus,
          setSummary,
        );
      }
      setReplayIndex(targetIndex);
    },
    [
      replayEvents,
      total,
      resetAgentStates,
      clearLiveFindings,
      setReviewStatus,
      setSummary,
      updateAgentState,
      addLiveFinding,
      setReplayIndex,
    ],
  );

  // Advance one step
  const stepForward = useCallback(() => {
    const next = replayIndex + 1;
    if (next < total) {
      applyUpTo(next);
    } else {
      setIsPlaying(false);
    }
  }, [replayIndex, total, applyUpTo]);

  const stepBackward = useCallback(() => {
    if (replayIndex > 0) {
      applyUpTo(replayIndex - 1);
    }
  }, [replayIndex, applyUpTo]);

  // Auto-play loop
  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(() => {
        const prev = useReviewStore.getState().replayIndex;
        const next = prev + 1;
        if (next >= total) {
          setIsPlaying(false);
          return;
        }
        applyUpTo(next);
        setReplayIndex(next);
      }, PLAY_INTERVAL_MS);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, total, applyUpTo, setReplayIndex]);

  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const idx = Number(e.target.value);
      setIsPlaying(false);
      applyUpTo(idx);
    },
    [applyUpTo],
  );

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    applyUpTo(0);
  }, [applyUpTo]);

  const handleExitReplay = useCallback(() => {
    setIsPlaying(false);
    setReplayMode(false);
    resetAgentStates();
    clearLiveFindings();
  }, [setReplayMode, resetAgentStates, clearLiveFindings]);

  if (!replayMode || total === 0) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950 p-8 text-zinc-500">
        {total === 0 ? "No timeline events recorded for this review." : "Replay not active."}
      </div>
    );
  }

  const currentEvent = replayEvents[replayIndex];
  const progressPct = total > 1 ? Math.round((replayIndex / (total - 1)) * 100) : 100;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-200">Historical Replay</h3>
        <button
          onClick={handleExitReplay}
          className="text-xs text-zinc-500 hover:text-zinc-300 underline"
        >
          Exit Replay
        </button>
      </div>

      {/* Current event info */}
      <div className="rounded bg-zinc-900 px-3 py-2 text-xs font-mono text-zinc-400">
        <span className="text-zinc-500">Step {replayIndex + 1}/{total}</span>
        {currentEvent && (
          <>
            <span className="mx-2 text-zinc-700">|</span>
            <span className="text-blue-400">{currentEvent.event_type}</span>
            <span className="mx-2 text-zinc-700">|</span>
            <span className="text-zinc-500">
              {new Date(currentEvent.timestamp).toLocaleTimeString()}
            </span>
          </>
        )}
      </div>

      {/* Slider */}
      <div className="space-y-1">
        <input
          type="range"
          min={0}
          max={Math.max(0, total - 1)}
          value={replayIndex}
          onChange={handleSliderChange}
          className="w-full accent-blue-500 cursor-pointer"
        />
        <div className="flex justify-between text-xs text-zinc-600">
          <span>0%</span>
          <span>{progressPct}%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleReset}
          disabled={replayIndex === 0}
          className="rounded bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Reset
        </button>
        <button
          onClick={stepBackward}
          disabled={replayIndex === 0}
          className="rounded bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Step Back
        </button>
        <button
          onClick={() => setIsPlaying((p) => !p)}
          disabled={replayIndex >= total - 1}
          className="rounded bg-blue-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
        <button
          onClick={stepForward}
          disabled={replayIndex >= total - 1}
          className="rounded bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Step Forward
        </button>

        {/* Event list preview */}
        <div className="ml-auto flex gap-1 flex-wrap max-w-xs">
          {replayEvents.slice(0, 12).map((ev, i) => (
            <button
              key={ev.id}
              onClick={() => { setIsPlaying(false); applyUpTo(i); }}
              title={ev.event_type}
              className={`h-2 w-2 rounded-full transition-colors ${
                i <= replayIndex ? "bg-blue-500" : "bg-zinc-700"
              }`}
            />
          ))}
          {total > 12 && (
            <span className="text-xs text-zinc-600">+{total - 12}</span>
          )}
        </div>
      </div>
    </div>
  );
}
