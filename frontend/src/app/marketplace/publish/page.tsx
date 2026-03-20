"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

const LISTING_TYPES = ["template", "org", "agent"] as const;

type ListingType = typeof LISTING_TYPES[number];

export default function PublishPage() {
  const router = useRouter();

  const [type, setType] = useState<ListingType>("template");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [tagsInput, setTagsInput] = useState("");
  const [config, setConfig] = useState("{}");
  const [configError, setConfigError] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState("");

  const tags = tagsInput
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  const handlePublish = async () => {
    setPublishError("");
    setConfigError("");

    let parsedConfig: Record<string, unknown> = {};
    try {
      parsedConfig = JSON.parse(config);
    } catch {
      setConfigError("Invalid JSON — please check your config.");
      return;
    }

    if (!title.trim()) {
      setPublishError("Title is required.");
      return;
    }
    if (!version.trim()) {
      setPublishError("Version is required.");
      return;
    }

    setPublishing(true);
    try {
      const listing = await api.marketplace.publish({
        listing_type: type,
        title: title.trim(),
        description: description.trim(),
        version: version.trim(),
        tags,
        config: parsedConfig,
      });
      router.push(`/marketplace/${listing.id}`);
    } catch (err) {
      setPublishError(err instanceof Error ? err.message : "Publish failed. Please try again.");
    }
    setPublishing(false);
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-zinc-100">Publish to Marketplace</h2>
              <p className="mt-1 text-sm text-zinc-400">
                Share your template, org, or agent with the SwarmForge community
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="border-zinc-700"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
          </div>

          {publishError && (
            <div className="rounded-lg border border-red-800 bg-red-900/20 px-4 py-3">
              <p className="text-sm text-red-400">{publishError}</p>
            </div>
          )}

          {/* Type selector */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Listing Type
            </label>
            <div className="flex gap-2">
              {LISTING_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => setType(t)}
                  className={`rounded-lg border px-4 py-2 text-sm capitalize transition-colors ${
                    type === t
                      ? "border-blue-600 bg-blue-900/30 text-blue-300"
                      : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Security-First Review Template"
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this listing does and who it's for..."
              rows={4}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none resize-none"
            />
          </div>

          {/* Version + Tags row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
                Version <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0.0"
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="security, typescript, strict"
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Tags preview */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {tags.map((tag) => (
                <span key={tag} className="rounded px-2 py-0.5 text-xs bg-zinc-800 text-zinc-400">
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Config JSON editor */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Configuration (JSON)
            </label>
            <textarea
              value={config}
              onChange={(e) => { setConfig(e.target.value); setConfigError(""); }}
              rows={10}
              className={`w-full rounded-lg border bg-zinc-950 px-4 py-3 text-sm font-mono text-zinc-300 placeholder-zinc-600 focus:outline-none resize-none ${
                configError
                  ? "border-red-700 focus:border-red-500"
                  : "border-zinc-800 focus:border-blue-500"
              }`}
              spellCheck={false}
            />
            {configError && (
              <p className="text-xs text-red-400">{configError}</p>
            )}
            <p className="text-xs text-zinc-600">
              Paste your template rules, org topology, or agent config as JSON.
            </p>
          </div>

          {/* Submit */}
          <div className="flex justify-end">
            <Button
              onClick={handlePublish}
              disabled={publishing || !title.trim()}
              className="bg-blue-600 hover:bg-blue-500 text-white px-6"
            >
              {publishing ? "Publishing..." : "Publish"}
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
