import { Router, Request, Response } from "express";
import { v4 as uuid } from "uuid";
import { parsePRUrl, postInlineComments, Finding } from "../github-service";
import { ReviewSession } from "../session";
import * as db from "../db";

const router = Router();

// Active sessions indexed by review id
export const activeSessions = new Map<string, ReviewSession>();

// GET /api/reviews
router.get("/", (req: Request, res: Response) => {
  const limit = parseInt(String(req.query.limit ?? "50"), 10) || 50;
  const reviews = db.listReviews(limit);
  res.json({ items: reviews, total: reviews.length });
});

// GET /api/reviews/:id
router.get("/:id", (req: Request<{ id: string }>, res: Response) => {
  const review = db.getReview(req.params.id);
  if (!review) {
    res.status(404).json({ error: "Not found" });
    return;
  }
  const findings = db.getFindings(req.params.id);
  res.json({ ...(review as Record<string, unknown>), findings });
});

// POST /api/reviews
router.post("/", (req: Request, res: Response) => {
  const { pr_url } = req.body as { pr_url?: string };
  if (!pr_url) {
    res.status(400).json({ error: "pr_url required" });
    return;
  }

  const parsed = parsePRUrl(pr_url);
  if (!parsed) {
    res.status(400).json({ error: "Invalid PR URL" });
    return;
  }

  const id = uuid();
  db.createReview({
    id,
    pr_url,
    repo_name:
      parsed.platform === "github"
        ? `${parsed.owner}/${parsed.repo}`
        : parsed.repo,
    pr_number: parsed.number,
    platform: parsed.platform,
    provider: "auto",
  });

  const session = new ReviewSession(id, pr_url);
  activeSessions.set(id, session);

  session.run().finally(() => {
    // Retain session for late WebSocket subscribers for 5 minutes
    setTimeout(() => activeSessions.delete(id), 300_000);
  });

  const review = db.getReview(id);
  res.status(201).json(review);
});

// DELETE /api/reviews/:id
router.delete("/:id", (req: Request<{ id: string }>, res: Response) => {
  const session = activeSessions.get(req.params.id);
  if (session) session.running = false;
  db.updateReview(req.params.id, { status: "cancelled" });
  res.status(204).end();
});

// GET /api/reviews/:id/findings
router.get(
  "/:id/findings",
  (req: Request<{ id: string }>, res: Response) => {
    let findings = db.getFindings(req.params.id) as Record<
      string,
      unknown
    >[];

    const severityFilter = req.query.severity;
    if (severityFilter) {
      const sv = String(severityFilter);
      findings = findings.filter((f) => f.severity === sv);
    }
    const roleFilter = req.query.agent_role;
    if (roleFilter) {
      const rl = String(roleFilter);
      findings = findings.filter((f) => f.agent_role === rl);
    }

    res.json(findings);
  }
);

// POST /api/reviews/:id/post-to-github
router.post(
  "/:id/post-to-github",
  async (req: Request<{ id: string }>, res: Response) => {
    const review = db.getReview(req.params.id) as
      | Record<string, unknown>
      | undefined;
    if (!review) {
      res.status(404).json({ error: "Not found" });
      return;
    }

    const token =
      db.getSetting("github_token") || process.env.GITHUB_TOKEN || "";
    if (!token) {
      res.status(400).json({ error: "GitHub token not configured" });
      return;
    }

    const findings = db.getFindings(req.params.id) as Finding[];
    try {
      const posted = await postInlineComments(
        review.pr_url as string,
        token,
        findings
      );
      res.json({ posted, message: `Posted ${posted} comments to GitHub` });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      res.status(502).json({ error: message });
    }
  }
);

export default router;
