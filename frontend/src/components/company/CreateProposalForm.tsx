"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Proposal } from "@/types/governance";

interface CreateProposalFormProps {
  companyId: string;
  onCreated?: (proposal: Proposal) => void;
  onCancel?: () => void;
}

const PROPOSAL_TYPES = ["budget", "role_change", "process", "policy"] as const;

export function CreateProposalForm({ companyId, onCreated, onCancel }: CreateProposalFormProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState<typeof PROPOSAL_TYPES[number]>("policy");
  const [changesJson, setChangesJson] = useState("{}");
  const [jsonError, setJsonError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChangesChange = (value: string) => {
    setChangesJson(value);
    try {
      JSON.parse(value);
      setJsonError("");
    } catch {
      setJsonError("Invalid JSON");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (jsonError) return;
    setSubmitting(true);
    setError("");
    try {
      const proposed_changes = JSON.parse(changesJson);
      const proposal = await api.governance.proposals.create(companyId, {
        title,
        description,
        proposal_type: type,
        proposed_changes,
      });
      onCreated?.(proposal);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create proposal");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-zinc-400 mb-1">Title</label>
        <input
          type="text"
          value={title}
          onChange={e => setTitle(e.target.value)}
          required
          placeholder="Proposal title"
          className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-zinc-400 mb-1">Description</label>
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value)}
          required
          rows={3}
          placeholder="Describe the proposal and its rationale"
          className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none resize-none"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-zinc-400 mb-1">Type</label>
        <select
          value={type}
          onChange={e => setType(e.target.value as typeof PROPOSAL_TYPES[number])}
          className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-zinc-500 focus:outline-none"
        >
          {PROPOSAL_TYPES.map(t => (
            <option key={t} value={t}>{t.replace("_", " ")}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-zinc-400 mb-1">
          Proposed Changes (JSON)
          {jsonError && <span className="ml-2 text-red-400">{jsonError}</span>}
        </label>
        <textarea
          value={changesJson}
          onChange={e => handleChangesChange(e.target.value)}
          rows={5}
          className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none resize-none"
        />
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <div className="flex items-center gap-2 justify-end">
        {onCancel && (
          <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          size="sm"
          disabled={submitting || !!jsonError}
        >
          {submitting ? "Creating..." : "Create Proposal"}
        </Button>
      </div>
    </form>
  );
}
