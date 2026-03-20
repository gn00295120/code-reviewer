"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Template {
  id: string;
  name: string;
  description: string | null;
}

interface Props {
  onSelect: (templateId: string | null) => void;
}

export function TemplateSelector({ onSelect }: Props) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    api.templates.list().then(setTemplates).catch(() => {});
  }, []);

  if (templates.length === 0) return null;

  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-zinc-500">Template:</label>
      <select
        value={selected || ""}
        onChange={(e) => {
          const val = e.target.value || null;
          setSelected(val);
          onSelect(val);
        }}
        className="rounded border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs text-zinc-300 focus:border-blue-500 focus:outline-none"
      >
        <option value="">None (default)</option>
        {templates.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
    </div>
  );
}
