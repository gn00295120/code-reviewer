import { create } from "zustand";
import type { AgentRole, AgentState, Finding, ReviewDetail, ReviewEvent, Severity } from "@/types/review";

const AGENT_ROLES: AgentRole[] = ["logic", "security", "edge_case", "convention", "performance"];

interface ReviewStore {
  // Current review being viewed
  currentReview: ReviewDetail | null;
  setCurrentReview: (review: ReviewDetail | null) => void;

  // Live agent states (from WebSocket)
  agentStates: Record<AgentRole, AgentState>;
  updateAgentState: (role: AgentRole, update: Partial<AgentState>) => void;
  resetAgentStates: () => void;

  // Live findings stream
  liveFindings: Finding[];
  addLiveFinding: (finding: Finding) => void;
  clearLiveFindings: () => void;

  // Cost tracking
  totalCost: number;
  updateCost: (cost: number) => void;

  // Review status
  reviewStatus: string;
  setReviewStatus: (status: string) => void;
  summary: string;
  setSummary: (summary: string) => void;

  // UI state
  selectedAgent: AgentRole | null;
  setSelectedAgent: (agent: AgentRole | null) => void;
  severityFilter: Severity | null;
  setSeverityFilter: (severity: Severity | null) => void;
  terminalOpen: boolean;
  setTerminalOpen: (open: boolean) => void;

  // Replay state
  replayMode: boolean;
  setReplayMode: (mode: boolean) => void;
  replayEvents: ReviewEvent[];
  setReplayEvents: (events: ReviewEvent[]) => void;
  replayIndex: number;
  setReplayIndex: (index: number) => void;
}

const initialAgentStates = (): Record<AgentRole, AgentState> =>
  Object.fromEntries(
    AGENT_ROLES.map((role) => [
      role,
      { role, status: "idle" as const, findings_count: 0, tokens: 0, cost_usd: 0 },
    ])
  ) as Record<AgentRole, AgentState>;

export const useReviewStore = create<ReviewStore>((set) => ({
  currentReview: null,
  setCurrentReview: (review) => set({ currentReview: review }),

  agentStates: initialAgentStates(),
  updateAgentState: (role, update) =>
    set((state) => ({
      agentStates: {
        ...state.agentStates,
        [role]: { ...state.agentStates[role], ...update },
      },
    })),
  resetAgentStates: () => set({ agentStates: initialAgentStates() }),

  liveFindings: [],
  addLiveFinding: (finding) =>
    set((state) => ({ liveFindings: [...state.liveFindings, finding] })),
  clearLiveFindings: () => set({ liveFindings: [] }),

  totalCost: 0,
  updateCost: (cost) => set((state) => ({ totalCost: state.totalCost + cost })),

  reviewStatus: "idle",
  setReviewStatus: (status) => set({ reviewStatus: status }),
  summary: "",
  setSummary: (summary) => set({ summary }),

  selectedAgent: null,
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  severityFilter: null,
  setSeverityFilter: (severity) => set({ severityFilter: severity }),
  terminalOpen: false,
  setTerminalOpen: (open) => set({ terminalOpen: open }),

  replayMode: false,
  setReplayMode: (mode) => set({ replayMode: mode }),
  replayEvents: [],
  setReplayEvents: (events) => set({ replayEvents: events }),
  replayIndex: 0,
  setReplayIndex: (index) => set({ replayIndex: index }),
}));
