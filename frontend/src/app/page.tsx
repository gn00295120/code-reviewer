"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { PRInputForm } from "@/components/review/PRInputForm";

export default function HomePage() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-4xl space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-zinc-100">SwarmForge</h1>
            <p className="mt-2 text-zinc-400">
              AI-powered multi-agent code review. Paste a PR URL to start.
            </p>
          </div>

          <PRInputForm />

          <div className="grid grid-cols-3 gap-4 pt-4">
            {[
              { title: "5 Specialist Agents", desc: "Logic, Security, Edge Cases, Convention, Performance" },
              { title: "Real-time Visual Flow", desc: "Watch agents analyze your code in real-time via React Flow" },
              { title: "GitHub Integration", desc: "Auto-post inline comments with suggested fixes" },
            ].map((card) => (
              <div key={card.title} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
                <h3 className="text-sm font-medium text-zinc-200">{card.title}</h3>
                <p className="mt-1 text-xs text-zinc-500">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
