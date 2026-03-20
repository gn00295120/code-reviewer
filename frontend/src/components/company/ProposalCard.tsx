"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Proposal } from "@/types/governance";

const TYPE_COLORS: Record<string, string> = {
  budget: "bg-blue-900/50 text-blue-300 border-blue-800",
  role_change: "bg-purple-900/50 text-purple-300 border-purple-800",
  process: "bg-yellow-900/50 text-yellow-300 border-yellow-800",
  policy: "bg-orange-900/50 text-orange-300 border-orange-800",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-zinc-700 text-zinc-300",
  passed: "bg-green-900/50 text-green-300",
  rejected: "bg-red-900/50 text-red-300",
  executed: "bg-blue-900/50 text-blue-300",
};

interface ProposalCardProps {
  proposal: Proposal;
  onUpdate?: (updated: Proposal) => void;
}

export function ProposalCard({ proposal, onUpdate }: ProposalCardProps) {
  const [voting, setVoting] = useState(false);
  const [executing, setExecuting] = useState(false);

  const totalVotes = proposal.votes_for + proposal.votes_against;
  const forPercent = totalVotes > 0 ? Math.round((proposal.votes_for / totalVotes) * 100) : 0;
  const quorumMet = totalVotes >= proposal.quorum_required;

  const handleVote = async (vote: "for" | "against" | "abstain") => {
    setVoting(true);
    try {
      await api.governance.vote(proposal.id, { vote });
      // Optimistic update of vote counts
      if (onUpdate) {
        const updated = { ...proposal };
        if (vote === "for") updated.votes_for += 1;
        else if (vote === "against") updated.votes_against += 1;
        onUpdate(updated);
      }
    } catch (err) {
      console.error("Vote failed:", err);
    } finally {
      setVoting(false);
    }
  };

  const handleExecute = async () => {
    setExecuting(true);
    try {
      const updated = await api.governance.execute(proposal.id);
      onUpdate?.(updated);
    } catch (err) {
      console.error("Execute failed:", err);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-zinc-100 truncate">{proposal.title}</span>
            <Badge variant="outline" className={TYPE_COLORS[proposal.proposal_type]}>
              {proposal.proposal_type.replace("_", " ")}
            </Badge>
            <Badge variant="outline" className={STATUS_COLORS[proposal.status]}>
              {proposal.status}
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 line-clamp-2">{proposal.description}</p>
          <p className="text-[10px] text-zinc-600">
            by {proposal.proposed_by} &middot; deadline {new Date(proposal.deadline).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Votes progress bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-[10px] text-zinc-500">
          <span>{proposal.votes_for} for</span>
          <span className={quorumMet ? "text-green-400" : ""}>
            {totalVotes}/{proposal.quorum_required} quorum {quorumMet ? "met" : "required"}
          </span>
          <span>{proposal.votes_against} against</span>
        </div>
        <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden flex">
          <div
            className="h-full bg-green-500 transition-all"
            style={{ width: `${forPercent}%` }}
          />
          <div
            className="h-full bg-red-500 transition-all"
            style={{ width: `${100 - forPercent}%` }}
          />
        </div>
      </div>

      {/* Action buttons */}
      {proposal.status === "open" && (
        <div className="flex items-center gap-2">
          <Button
            size="xs"
            variant="ghost"
            className="text-green-400 hover:text-green-300 hover:bg-green-900/30"
            onClick={() => handleVote("for")}
            disabled={voting}
          >
            For
          </Button>
          <Button
            size="xs"
            variant="ghost"
            className="text-red-400 hover:text-red-300 hover:bg-red-900/30"
            onClick={() => handleVote("against")}
            disabled={voting}
          >
            Against
          </Button>
          <Button
            size="xs"
            variant="ghost"
            className="text-zinc-400 hover:text-zinc-300"
            onClick={() => handleVote("abstain")}
            disabled={voting}
          >
            Abstain
          </Button>
        </div>
      )}

      {proposal.status === "passed" && (
        <Button
          size="xs"
          variant="outline"
          className="border-blue-800 text-blue-300 hover:bg-blue-900/30"
          onClick={handleExecute}
          disabled={executing}
        >
          {executing ? "Executing..." : "Execute"}
        </Button>
      )}
    </div>
  );
}
