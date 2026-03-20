"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { AuditLog, SecurityPolicy } from "@/types/enterprise";

const POLICY_TYPES = ["rate_limit", "secret_detection", "access_control"] as const;

const ACTION_TYPES = ["", "create", "update", "delete", "login", "deploy", "execute"];

function formatDate(s: string) {
  return new Date(s).toLocaleString();
}

export default function EnterprisePage() {
  // Audit Log state
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [auditLoading, setAuditLoading] = useState(true);
  const [filterAction, setFilterAction] = useState("");
  const [filterFrom, setFilterFrom] = useState("");
  const [filterTo, setFilterTo] = useState("");

  // Policies state
  const [policies, setPolicies] = useState<SecurityPolicy[]>([]);
  const [policiesLoading, setPoliciesLoading] = useState(true);

  // New policy form
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState<typeof POLICY_TYPES[number]>("rate_limit");
  const [newConfig, setNewConfig] = useState("{}");
  const [configError, setConfigError] = useState("");
  const [creating, setCreating] = useState(false);

  const loadAuditLogs = async () => {
    setAuditLoading(true);
    try {
      const result = await api.enterprise.auditLogs({
        action: filterAction || undefined,
        from: filterFrom || undefined,
        to: filterTo || undefined,
        limit: 100,
      });
      setAuditLogs(result.items);
    } catch {
      setAuditLogs([]);
    }
    setAuditLoading(false);
  };

  const loadPolicies = async () => {
    setPoliciesLoading(true);
    try {
      const result = await api.enterprise.policies.list();
      setPolicies(result);
    } catch {
      setPolicies([]);
    }
    setPoliciesLoading(false);
  };

  useEffect(() => {
    loadAuditLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterAction, filterFrom, filterTo]);

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleTogglePolicy = async (policy: SecurityPolicy) => {
    try {
      const updated = await api.enterprise.policies.toggle(policy.id, !policy.is_active);
      setPolicies((prev) => prev.map((p) => (p.id === policy.id ? updated : p)));
    } catch {}
  };

  const handleCreatePolicy = async () => {
    if (!newName.trim()) return;
    let parsedConfig: Record<string, unknown> = {};
    try {
      parsedConfig = JSON.parse(newConfig);
      setConfigError("");
    } catch {
      setConfigError("Invalid JSON");
      return;
    }
    setCreating(true);
    try {
      const created = await api.enterprise.policies.create({
        name: newName.trim(),
        policy_type: newType,
        config: parsedConfig,
      });
      setPolicies((prev) => [created, ...prev]);
      setNewName("");
      setNewConfig("{}");
    } catch {}
    setCreating(false);
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-zinc-100">Enterprise Guard</h2>
            <p className="mt-1 text-sm text-zinc-400">
              Audit trails and security policy management for your SwarmForge deployment
            </p>
          </div>

          <Tabs defaultValue="audit" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="audit">Audit Log</TabsTrigger>
              <TabsTrigger value="policies">Security Policies</TabsTrigger>
            </TabsList>

            {/* Audit Log tab */}
            <TabsContent value="audit" className="mt-4 space-y-4">
              {/* Filters */}
              <div className="flex gap-3 flex-wrap">
                <select
                  value={filterAction}
                  onChange={(e) => setFilterAction(e.target.value)}
                  className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
                >
                  {ACTION_TYPES.map((a) => (
                    <option key={a} value={a}>{a || "All actions"}</option>
                  ))}
                </select>
                <input
                  type="date"
                  value={filterFrom}
                  onChange={(e) => setFilterFrom(e.target.value)}
                  className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
                  placeholder="From date"
                />
                <input
                  type="date"
                  value={filterTo}
                  onChange={(e) => setFilterTo(e.target.value)}
                  className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
                  placeholder="To date"
                />
                <Button variant="outline" size="sm" className="border-zinc-700" onClick={loadAuditLogs}>
                  Refresh
                </Button>
              </div>

              {auditLoading ? (
                <p className="text-sm text-zinc-500">Loading audit log...</p>
              ) : auditLogs.length === 0 ? (
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-8 text-center">
                  <p className="text-sm text-zinc-500">No audit log entries found.</p>
                </div>
              ) : (
                <div className="rounded-lg border border-zinc-800 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-900 border-b border-zinc-800">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs text-zinc-500 font-medium">Action</th>
                        <th className="px-4 py-3 text-left text-xs text-zinc-500 font-medium">Actor</th>
                        <th className="px-4 py-3 text-left text-xs text-zinc-500 font-medium">Resource</th>
                        <th className="px-4 py-3 text-left text-xs text-zinc-500 font-medium">IP</th>
                        <th className="px-4 py-3 text-left text-xs text-zinc-500 font-medium">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {auditLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-zinc-800/30 transition-colors">
                          <td className="px-4 py-3">
                            <Badge variant="outline" className="bg-zinc-800 text-zinc-300 text-xs">
                              {log.action}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-zinc-300">{log.actor}</td>
                          <td className="px-4 py-3 text-zinc-400">
                            <span className="text-zinc-500">{log.resource_type}/</span>
                            <span className="font-mono text-xs">{log.resource_id}</span>
                          </td>
                          <td className="px-4 py-3 text-zinc-500 font-mono text-xs">{log.ip_address}</td>
                          <td className="px-4 py-3 text-zinc-500 text-xs">{formatDate(log.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TabsContent>

            {/* Security Policies tab */}
            <TabsContent value="policies" className="mt-4 space-y-4">
              {/* Create policy form */}
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
                <h3 className="text-sm font-medium text-zinc-200">New Policy</h3>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="Policy name"
                    className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
                  />
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value as typeof POLICY_TYPES[number])}
                    className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-blue-500 focus:outline-none"
                  >
                    {POLICY_TYPES.map((t) => (
                      <option key={t} value={t}>{t.replace("_", " ")}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-zinc-500 block mb-1">Config JSON</label>
                  <textarea
                    value={newConfig}
                    onChange={(e) => { setNewConfig(e.target.value); setConfigError(""); }}
                    rows={4}
                    className={`w-full rounded-lg border bg-zinc-950 px-4 py-2 text-sm font-mono text-zinc-300 focus:outline-none resize-none ${
                      configError ? "border-red-700 focus:border-red-500" : "border-zinc-800 focus:border-blue-500"
                    }`}
                  />
                  {configError && <p className="text-xs text-red-400 mt-1">{configError}</p>}
                </div>
                <Button onClick={handleCreatePolicy} disabled={creating || !newName.trim()}>
                  {creating ? "Creating..." : "Create Policy"}
                </Button>
              </div>

              {/* Existing policies */}
              {policiesLoading ? (
                <p className="text-sm text-zinc-500">Loading policies...</p>
              ) : policies.length === 0 ? (
                <p className="text-sm text-zinc-500">No policies configured.</p>
              ) : (
                <div className="space-y-2">
                  {policies.map((policy) => (
                    <div key={policy.id} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 flex items-center justify-between gap-4">
                      <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-zinc-100">{policy.name}</span>
                          <Badge
                            variant="outline"
                            className={
                              policy.policy_type === "secret_detection"
                                ? "bg-red-900/50 text-red-300 border-red-700"
                                : policy.policy_type === "rate_limit"
                                ? "bg-yellow-900/50 text-yellow-300 border-yellow-700"
                                : "bg-blue-900/50 text-blue-300 border-blue-700"
                            }
                          >
                            {policy.policy_type.replace("_", " ")}
                          </Badge>
                        </div>
                        <p className="text-xs text-zinc-500">
                          Created {formatDate(policy.created_at)}
                        </p>
                      </div>
                      <button
                        onClick={() => handleTogglePolicy(policy)}
                        className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                          policy.is_active ? "bg-blue-600" : "bg-zinc-700"
                        }`}
                        role="switch"
                        aria-checked={policy.is_active}
                      >
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform duration-200 ease-in-out ${
                            policy.is_active ? "translate-x-5" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
