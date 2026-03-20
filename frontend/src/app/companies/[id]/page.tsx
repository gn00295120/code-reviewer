"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProposalCard } from "@/components/company/ProposalCard";
import { CreateProposalForm } from "@/components/company/CreateProposalForm";
import { api } from "@/lib/api";
import type { AgentCompany, CompanyAgent } from "@/types/company";
import type { Proposal } from "@/types/governance";

const AGENT_STATUS_DOT: Record<string, string> = {
  active: "bg-green-400",
  idle: "bg-zinc-500",
  paused: "bg-yellow-400",
};

// Org chart tree node
function AgentNode({ agent, allAgents }: { agent: CompanyAgent; allAgents: CompanyAgent[] }) {
  const reports = allAgents.filter(a => a.reports_to === agent.id);
  return (
    <div className="pl-4 border-l border-zinc-800">
      <div className="flex items-center gap-2 py-1">
        <span className={`h-2 w-2 rounded-full shrink-0 ${AGENT_STATUS_DOT[agent.status] ?? "bg-zinc-600"}`} />
        <div>
          <span className="text-sm font-medium text-zinc-200">{agent.title}</span>
          <span className="ml-2 text-xs text-zinc-500">{agent.role}</span>
          <span className="ml-2 text-[10px] text-zinc-600">{agent.model}</span>
        </div>
      </div>
      {reports.length > 0 && (
        <div className="ml-2">
          {reports.map(r => <AgentNode key={r.id} agent={r} allAgents={allAgents} />)}
        </div>
      )}
    </div>
  );
}

function OrgChartTab({
  companyId,
  agents,
  onAgentAdded,
}: {
  companyId: string;
  agents: CompanyAgent[];
  onAgentAdded: (agent: CompanyAgent) => void;
}) {
  const [showForm, setShowForm] = useState(false);
  const [role, setRole] = useState("");
  const [title, setTitle] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Roots = agents with no reports_to or whose reports_to is not in the list
  const agentIds = new Set(agents.map(a => a.id));
  const roots = agents.filter(a => !a.reports_to || !agentIds.has(a.reports_to));

  const handleAddAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const agent = await api.companies.agents.add(companyId, { role, title, model });
      onAgentAdded(agent);
      setShowForm(false);
      setRole("");
      setTitle("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add agent");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-300">Organizational Hierarchy</h3>
        <Button size="xs" variant="outline" onClick={() => setShowForm(v => !v)}>
          {showForm ? "Cancel" : "+ Add Agent"}
        </Button>
      </div>

      {showForm && (
        <form onSubmit={handleAddAgent} className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3 space-y-3">
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-[10px] text-zinc-400 mb-1">Role</label>
              <input
                type="text"
                value={role}
                onChange={e => setRole(e.target.value)}
                required
                placeholder="engineer"
                className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] text-zinc-400 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                required
                placeholder="Senior Engineer"
                className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] text-zinc-400 mb-1">Model</label>
              <input
                type="text"
                value={model}
                onChange={e => setModel(e.target.value)}
                placeholder="gpt-4o"
                className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
              />
            </div>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
          <Button type="submit" size="xs" disabled={submitting}>
            {submitting ? "Adding..." : "Add Agent"}
          </Button>
        </form>
      )}

      {agents.length === 0 ? (
        <p className="text-xs text-zinc-500">No agents yet. Add the first one above.</p>
      ) : (
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-4 space-y-1">
          {roots.map(agent => (
            <AgentNode key={agent.id} agent={agent} allAgents={agents} />
          ))}
        </div>
      )}
    </div>
  );
}

function BudgetTab({ companyId, company }: { companyId: string; company: AgentCompany }) {
  const [budget, setBudget] = useState<{
    budget_usd: number;
    spent_usd: number;
    remaining_usd: number;
    per_agent: Record<string, number>;
  } | null>(null);

  useEffect(() => {
    api.companies.budget(companyId).then(setBudget).catch(() => {});
  }, [companyId]);

  const spentPercent = company.budget_usd > 0
    ? Math.min(100, Math.round((company.spent_usd / company.budget_usd) * 100))
    : 0;

  return (
    <div className="space-y-4">
      {/* Overall spend */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
        <h3 className="text-sm font-medium text-zinc-300">Budget Overview</h3>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <p className="text-lg font-bold text-zinc-100">${company.budget_usd.toFixed(2)}</p>
            <p className="text-[10px] text-zinc-500">Total Budget</p>
          </div>
          <div>
            <p className="text-lg font-bold text-yellow-400">${company.spent_usd.toFixed(2)}</p>
            <p className="text-[10px] text-zinc-500">Spent</p>
          </div>
          <div>
            <p className="text-lg font-bold text-green-400">
              ${(company.budget_usd - company.spent_usd).toFixed(2)}
            </p>
            <p className="text-[10px] text-zinc-500">Remaining</p>
          </div>
        </div>
        <div className="space-y-1">
          <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${spentPercent >= 90 ? "bg-red-500" : spentPercent >= 70 ? "bg-yellow-500" : "bg-blue-500"}`}
              style={{ width: `${spentPercent}%` }}
            />
          </div>
          <p className="text-[10px] text-zinc-500 text-right">{spentPercent}% used</p>
        </div>
      </div>

      {/* Per-agent breakdown */}
      {budget && Object.keys(budget.per_agent).length > 0 && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
          <h3 className="text-sm font-medium text-zinc-300">Per-Agent Cost Breakdown</h3>
          {Object.entries(budget.per_agent).map(([agentId, cost]) => (
            <div key={agentId} className="flex items-center justify-between text-xs">
              <span className="text-zinc-400 font-mono truncate max-w-xs">{agentId}</span>
              <span className="text-zinc-300">${(cost as number).toFixed(4)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;

  const [company, setCompany] = useState<AgentCompany | null>(null);
  const [agents, setAgents] = useState<CompanyAgent[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showProposalForm, setShowProposalForm] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [co, ag, pr] = await Promise.all([
        api.companies.get(companyId),
        api.companies.agents.list(companyId).catch(() => []),
        api.governance.proposals.list(companyId).catch(() => []),
      ]);
      setCompany(co);
      setAgents(ag);
      setProposals(pr);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load company");
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-zinc-500">Loading company...</p>
        </main>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-red-400">{error || "Company not found"}</p>
        </main>
      </div>
    );
  }

  const STATUS_COLORS: Record<string, string> = {
    active: "bg-green-900/50 text-green-300 border-green-800",
    paused: "bg-yellow-900/50 text-yellow-300 border-yellow-800",
    archived: "bg-zinc-700 text-zinc-400",
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-bold text-zinc-100">{company.name}</h2>
                <Badge variant="outline" className={STATUS_COLORS[company.status]}>
                  {company.status}
                </Badge>
              </div>
              {company.description && (
                <p className="mt-1 text-sm text-zinc-400">{company.description}</p>
              )}
              <p className="mt-0.5 text-xs text-zinc-600">
                {company.agent_count} agents &middot; owner: {company.owner}
              </p>
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="org-chart" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="org-chart">Org Chart</TabsTrigger>
              <TabsTrigger value="proposals">Proposals</TabsTrigger>
              <TabsTrigger value="budget">Budget</TabsTrigger>
            </TabsList>

            <TabsContent value="org-chart" className="mt-4">
              <OrgChartTab
                companyId={companyId}
                agents={agents}
                onAgentAdded={agent => setAgents(prev => [...prev, agent])}
              />
            </TabsContent>

            <TabsContent value="proposals" className="mt-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-zinc-300">DAO Proposals</h3>
                  <Button size="xs" variant="outline" onClick={() => setShowProposalForm(v => !v)}>
                    {showProposalForm ? "Cancel" : "+ New Proposal"}
                  </Button>
                </div>
                {showProposalForm && (
                  <div className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-4">
                    <CreateProposalForm
                      companyId={companyId}
                      onCreated={p => {
                        setProposals(prev => [p, ...prev]);
                        setShowProposalForm(false);
                      }}
                      onCancel={() => setShowProposalForm(false)}
                    />
                  </div>
                )}
                {proposals.length === 0 ? (
                  <p className="text-xs text-zinc-500">No proposals yet.</p>
                ) : (
                  <div className="space-y-3">
                    {proposals.map(p => (
                      <ProposalCard
                        key={p.id}
                        proposal={p}
                        onUpdate={updated =>
                          setProposals(prev => prev.map(x => x.id === updated.id ? updated : x))
                        }
                      />
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="budget" className="mt-4">
              <BudgetTab companyId={companyId} company={company} />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
