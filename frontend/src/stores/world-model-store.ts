import { create } from "zustand";
import type { PhysicsEvent, WorldModelDetail, WorldModelStatus } from "@/types/world-model";

interface WorldModelStore {
  currentModel: WorldModelDetail | null;
  setCurrentModel: (model: WorldModelDetail | null) => void;

  status: WorldModelStatus;
  setStatus: (status: WorldModelStatus) => void;

  liveEvents: PhysicsEvent[];
  addLiveEvent: (event: PhysicsEvent) => void;
  clearLiveEvents: () => void;

  currentStep: number;
  setCurrentStep: (step: number) => void;

  totalCost: number;
  updateCost: (cost: number) => void;

  // Replay
  replayStep: number | null;
  setReplayStep: (step: number | null) => void;
}

export const useWorldModelStore = create<WorldModelStore>((set) => ({
  currentModel: null,
  setCurrentModel: (model) => set({ currentModel: model }),

  status: "idle",
  setStatus: (status) => set({ status }),

  liveEvents: [],
  addLiveEvent: (event) =>
    set((state) => ({ liveEvents: [...state.liveEvents, event], currentStep: event.step })),
  clearLiveEvents: () => set({ liveEvents: [] }),

  currentStep: 0,
  setCurrentStep: (step) => set({ currentStep: step }),

  totalCost: 0,
  updateCost: (cost) => set((state) => ({ totalCost: state.totalCost + cost })),

  replayStep: null,
  setReplayStep: (step) => set({ replayStep: step }),
}));
