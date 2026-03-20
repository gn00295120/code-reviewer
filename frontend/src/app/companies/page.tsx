"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { AgentCompany } from "@/types/company";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-900/50 text-green-300 border-green-800",
  paused: "bg-yellow-900/50 text-yellow-300 border-yellow-800",
  archived: "bg-zinc-700 text-zinc-400",
};

function CreateCompanyForm({ onCreated }: { onCreated: (c: AgentCompany) => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [budget, setBudget] = useState("1000");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const company = await api.companies.create({
        name,
        description: description || undefined,
        budget_usd: parseFloat(budget),
      });
      onCreated(company);
      setName("");
      setDescription("");
      setBudget("1000");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create company");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-4 space-y-3">
      <h3 className="text-sm font-medium text-zinc-200">New Agent Company</h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            required
            placeholder="Acme AI Corp"
            className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Budget (USD)</label>
          <input
            type="number"
            value={budget}
            onChange={e => setBudget(e.target.value)}
            min="0"
            step="0.01"
            className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:border-zinc-500 focus:outline-none"
          />
        </div>
      </div>
      <div>
        <label className="block text-xs text-zinc-400 mb-1">Description</label>
        <input
          type="text"
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="What does this company do?"
          className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <Button type="submit" size="sm" disabled={submitting}>
        {submitting ? "Creating..." : "Create Company"}
      </Button>
    </form>
  );
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<AgentCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    api.companies.list().then(setCompanies).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleCreated = (company: AgentCompany) => {
    setCompanies(prev => [company, ...prev]);
    setShowForm(false);
  };

  const handleActivate = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    setActionLoading(id + "-activate");
    try {
      const updated = await api.companies.activate(id);
      setCompanies(prev => prev.map(c => c.id === id ? updated : c));
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const handlePause = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    setActionLoading(id + "-pause");
    try {
      const updated = await api.companies.pause(id);
      setCompanies(prev => prev.map(c => c.id === id ? updated : c));
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-zinc-100">Agent Companies</h2>
              <p className="mt-1 text-sm text-zinc-400">
                Orchestrated AI agent organizations with shared budgets and governance
              </p>
            </div>
            <Button size="sm" onClick={() => setShowForm(v => !v)}>
              {showForm ? "Cancel" : "+ New Company"}
            </Button>
          </div>

          {showForm && <CreateCompanyForm onCreated={handleCreated} />}

          <div className="space-y-3">
            {loading ? (
              <p className="text-sm text-zinc-500">Loading...</p>
            ) : companies.length === 0 ? (
              <p className="text-sm text-zinc-500">No companies yet. Create one to get started.</p>
            ) : (
              companies.map(company => {
                const spentPercent = company.budget_usd > 0
                  ? Math.min(100, Math.round((company.spent_usd / company.budget_usd) * 100))
                  : 0;
                return (
                  <Link
                    key={company.id}
                    href={`/companies/${company.id}`}
                    className="block rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 hover:bg-zinc-800/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0 space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold text-zinc-100">{company.name}</span>
                          <Badge variant="outline" className={STATUS_COLORS[company.status]}>
                            {company.status}
                          </Badge>
                          <span className="text-xs text-zinc-500">{company.agent_count} agents</span>
                        </div>
                        {company.description && (
                          <p className="text-xs text-zinc-400 truncate">{company.description}</p>
                        )}
                        {/* Budget progress bar */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[10px] text-zinc-500">
                            <span>${company.spent_usd.toFixed(2)} spent</span>
                            <span>${company.budget_usd.toFixed(2)} budget</span>
                          </div>
                          <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${spentPercent >= 90 ? "bg-red-500" : spentPercent >= 70 ? "bg-yellow-500" : "bg-blue-500"}`}
                              style={{ width: `${spentPercent}%` }}
                            />
                          </div>
                        </div>
                      </div>
                      {/* Actions */}
                      <div className="flex items-center gap-2 shrink-0">
                        {company.status !== "active" && (
                          <Button
                            size="xs"
                            variant="ghost"
                            className="text-green-400 hover:text-green-300 hover:bg-green-900/30"
                            onClick={e => handleActivate(company.id, e)}
                            disabled={actionLoading === company.id + "-activate"}
                          >
                            Activate
                          </Button>
                        )}
                        {company.status === "active" && (
                          <Button
                            size="xs"
                            variant="ghost"
                            className="text-yellow-400 hover:text-yellow-300 hover:bg-yellow-900/30"
                            onClick={e => handlePause(company.id, e)}
                            disabled={actionLoading === company.id + "-pause"}
                          >
                            Pause
                          </Button>
                        )}
                      </div>
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
