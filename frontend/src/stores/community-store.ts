import { create } from "zustand";
import type { AgentOrg, AgentPost } from "@/types/community";

interface CommunityStore {
  orgs: AgentOrg[];
  setOrgs: (orgs: AgentOrg[]) => void;

  feed: AgentPost[];
  setFeed: (posts: AgentPost[]) => void;
  addPost: (post: AgentPost) => void;

  selectedOrg: AgentOrg | null;
  setSelectedOrg: (org: AgentOrg | null) => void;

  templates: AgentOrg[];
  setTemplates: (templates: AgentOrg[]) => void;
}

export const useCommunityStore = create<CommunityStore>((set) => ({
  orgs: [],
  setOrgs: (orgs) => set({ orgs }),

  feed: [],
  setFeed: (posts) => set({ feed: posts }),
  addPost: (post) => set((state) => ({ feed: [post, ...state.feed] })),

  selectedOrg: null,
  setSelectedOrg: (org) => set({ selectedOrg: org }),

  templates: [],
  setTemplates: (templates) => set({ templates }),
}));
