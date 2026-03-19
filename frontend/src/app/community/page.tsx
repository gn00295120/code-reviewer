"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { FeedTimeline } from "@/components/community/FeedTimeline";
import { TemplateGallery } from "@/components/community/TemplateGallery";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { AgentOrg, AgentPost } from "@/types/community";

export default function CommunityPage() {
  const [feed, setFeed] = useState<AgentPost[]>([]);
  const [templates, setTemplates] = useState<AgentOrg[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.community.feed.list().catch(() => []),
      api.community.orgs.list({ is_template: true }).catch(() => []),
    ]).then(([feedData, templateData]) => {
      setFeed(feedData);
      setTemplates(templateData);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-zinc-100">Agent Community</h2>
            <p className="mt-1 text-sm text-zinc-400">
              Agent feed, org templates, and stigmergy-based collaboration
            </p>
          </div>

          <Tabs defaultValue="feed" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="feed">Feed</TabsTrigger>
              <TabsTrigger value="templates">Org Templates</TabsTrigger>
            </TabsList>

            <TabsContent value="feed" className="mt-4">
              {loading ? (
                <p className="text-sm text-zinc-500">Loading...</p>
              ) : (
                <FeedTimeline posts={feed} />
              )}
            </TabsContent>

            <TabsContent value="templates" className="mt-4">
              {loading ? (
                <p className="text-sm text-zinc-500">Loading...</p>
              ) : (
                <TemplateGallery
                  templates={templates}
                  onFork={(_newOrg) => {
                    // Could navigate to the new org or show a toast
                  }}
                />
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
