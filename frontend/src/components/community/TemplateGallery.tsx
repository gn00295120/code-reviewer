"use client";

import { OrgCard } from "./OrgCard";
import type { AgentOrg } from "@/types/community";

interface Props {
  templates: AgentOrg[];
  onFork?: (newOrg: AgentOrg) => void;
}

export function TemplateGallery({ templates, onFork }: Props) {
  if (templates.length === 0) {
    return (
      <p className="text-sm text-zinc-500 text-center py-6">
        No org templates available yet.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      {templates.map((template) => (
        <OrgCard key={template.id} org={template} onFork={onFork} />
      ))}
    </div>
  );
}
