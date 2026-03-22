import React, { useState, useEffect } from "react";

const API = "http://localhost:3001";
const apiUrl = (path: string) => {
  if (typeof window !== "undefined" && window.location.port === "5173") return path;
  return `${API}${path}`;
};

interface Provider {
  name: string;
  command: string;
  model: string;
  priority: number;
}

export default function SettingsPage() {
  const [githubToken, setGithubToken] = useState("");
  const [providers, setProviders] = useState<Provider[]>([]);
  const [activeProvider, setActiveProvider] = useState<Provider | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(apiUrl("/api/settings")).then(r => r.json()).then(data => {
      setGithubToken(data.settings?.github_token || "");
      setProviders(data.providers || []);
      setActiveProvider(data.activeProvider);
    }).catch(() => {});
  }, []);

  const save = async (key: string, value: string) => {
    await fetch(apiUrl("/api/settings"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, value }),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-8">
      <h2 className="text-2xl font-bold text-zinc-100">Settings</h2>

      {/* GitHub Token */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-zinc-400">GitHub Token</label>
        <div className="flex gap-2">
          <input type="password" value={githubToken} onChange={e => setGithubToken(e.target.value)}
            placeholder="ghp_..."
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-100 focus:border-blue-500 focus:outline-none" />
          <button onClick={() => save("github_token", githubToken)}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors">
            Save
          </button>
        </div>
        <p className="text-xs text-zinc-600">Required for fetching PR diffs and posting comments</p>
      </div>

      {/* Providers */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-zinc-400">AI Providers (auto-detected)</label>
        <div className="space-y-2">
          {providers.length === 0 && <p className="text-sm text-red-400">No AI CLI found. Install codex, claude, gemini, or opencode.</p>}
          {providers.map((p, i) => (
            <div key={p.name} className={`flex items-center gap-3 p-3 rounded-lg border ${i === 0 ? "border-blue-800 bg-blue-900/10" : "border-zinc-800 bg-zinc-900/50"}`}>
              <span className={`w-2 h-2 rounded-full ${i === 0 ? "bg-green-500" : "bg-zinc-600"}`} />
              <span className="text-sm font-medium text-zinc-200">{p.name}</span>
              <span className="text-xs text-zinc-500">{p.model}</span>
              {i === 0 && <span className="text-xs text-green-400 ml-auto">Active</span>}
            </div>
          ))}
        </div>
        <p className="text-xs text-zinc-600">Priority: codex → claude → gemini → opencode</p>
      </div>

      {saved && <p className="text-sm text-green-400">Settings saved</p>}
    </div>
  );
}
