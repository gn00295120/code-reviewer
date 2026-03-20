export interface MarketplaceListing {
  id: string;
  listing_type: "template" | "org" | "agent";
  title: string;
  description: string;
  author: string;
  version: string;
  config: Record<string, unknown>;
  tags: string[];
  downloads: number;
  rating: number;
  rating_count: number;
  is_published: boolean;
  created_at: string;
}
