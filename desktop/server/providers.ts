import which from "which";

export interface Provider {
  name: string;
  command: string;
  model: string;
  priority: number;
}

const PROVIDERS: Provider[] = [
  { name: "codex", command: "codex", model: "gpt-5.4", priority: 1 },
  { name: "claude", command: "claude", model: "opus", priority: 2 },
  { name: "gemini", command: "gemini", model: "gemini-3", priority: 3 },
  { name: "opencode", command: "opencode", model: "opencode", priority: 4 },
];

export function detectProviders(): Provider[] {
  return PROVIDERS.filter((p) => {
    try {
      which.sync(p.command);
      return true;
    } catch {
      return false;
    }
  }).sort((a, b) => a.priority - b.priority);
}

export function getBestProvider(): Provider | null {
  const available = detectProviders();
  return available[0] ?? null;
}
