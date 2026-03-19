"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  const webhookUrl = typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:8000/api/webhooks/github`
    : "http://localhost:8000/api/webhooks/github";

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-3xl space-y-6">
          <h2 className="text-2xl font-bold text-zinc-100">Settings</h2>

          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardHeader>
              <CardTitle className="text-lg text-zinc-100">GitHub Webhook Setup</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-zinc-400">
                Configure a GitHub webhook to auto-trigger reviews when PRs are opened or updated.
              </p>

              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-zinc-400">Payload URL</label>
                  <div className="mt-1 flex items-center gap-2">
                    <code className="flex-1 rounded bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-zinc-300 font-mono">
                      {webhookUrl}
                    </code>
                    <button
                      onClick={() => navigator.clipboard.writeText(webhookUrl)}
                      className="rounded px-3 py-2 text-xs text-zinc-400 hover:text-zinc-200 bg-zinc-800 hover:bg-zinc-700"
                    >
                      Copy
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-zinc-400">Content type</label>
                  <p className="text-sm text-zinc-300 mt-1">application/json</p>
                </div>

                <div>
                  <label className="text-xs font-medium text-zinc-400">Events</label>
                  <p className="text-sm text-zinc-300 mt-1">Pull requests (opened, synchronize, reopened)</p>
                </div>

                <div className="rounded-lg bg-zinc-950 border border-zinc-800 p-4 text-xs text-zinc-400 space-y-2">
                  <p className="font-medium text-zinc-300">Setup steps:</p>
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Go to your repo Settings &rarr; Webhooks &rarr; Add webhook</li>
                    <li>Set Payload URL to the URL above</li>
                    <li>Set Content type to application/json</li>
                    <li>Set Secret to match your GITHUB_WEBHOOK_SECRET env var</li>
                    <li>Select &ldquo;Let me select individual events&rdquo; &rarr; check &ldquo;Pull requests&rdquo;</li>
                    <li>Click Add webhook</li>
                  </ol>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardHeader>
              <CardTitle className="text-lg text-zinc-100">LLM Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-zinc-400">
                Configured via environment variables and litellm_config.yaml.
              </p>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-zinc-500">Default Model:</span>
                  <span className="ml-2 text-zinc-300">Claude Sonnet 4.6</span>
                </div>
                <div>
                  <span className="text-zinc-500">LiteLLM Proxy:</span>
                  <span className="ml-2 text-zinc-300">localhost:4000</span>
                </div>
                <div>
                  <span className="text-zinc-500">Cost Tracking:</span>
                  <span className="ml-2 text-green-400">Enabled</span>
                </div>
                <div>
                  <span className="text-zinc-500">Agents:</span>
                  <span className="ml-2 text-zinc-300">5 specialist reviewers</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
