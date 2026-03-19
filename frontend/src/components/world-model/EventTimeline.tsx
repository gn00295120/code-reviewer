"use client";

import { useWorldModelStore } from "@/stores/world-model-store";
import { ScrollArea } from "@/components/ui/scroll-area";

export function EventTimeline() {
  const { liveEvents, currentModel, setReplayStep, replayStep } = useWorldModelStore();

  const events = currentModel?.events?.length ? currentModel.events : liveEvents;
  const displayEvents = [...events].reverse().slice(0, 100);

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-zinc-200">Event Timeline</h3>
      <ScrollArea className="h-[300px]">
        <div className="space-y-1.5 pr-4">
          {displayEvents.length === 0 ? (
            <p className="text-xs text-zinc-500 text-center py-4">No events yet. Start the simulation.</p>
          ) : (
            displayEvents.map((event) => (
              <button
                key={event.id || event.step}
                onClick={() => setReplayStep(event.step)}
                className={`w-full text-left rounded border px-3 py-2 text-xs transition-colors ${
                  replayStep === event.step
                    ? "border-blue-500 bg-blue-950/30"
                    : "border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-zinc-300 font-mono">Step {event.step}</span>
                  <div className="flex items-center gap-2">
                    <span className={`${event.reward > 0 ? "text-green-400" : event.reward < 0 ? "text-red-400" : "text-zinc-500"}`}>
                      R: {event.reward.toFixed(2)}
                    </span>
                    <span className="text-zinc-600">${Number(event.cost_usd).toFixed(4)}</span>
                  </div>
                </div>
                {event.agent_reasoning && (
                  <p className="mt-1 text-zinc-500 truncate">{event.agent_reasoning}</p>
                )}
                <div className="mt-1 flex gap-2 text-zinc-600">
                  <span>Action: {JSON.stringify(event.action).slice(0, 40)}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
