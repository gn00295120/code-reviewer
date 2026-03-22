import { Router, Request, Response } from "express";
import { getAllSettings, getSetting, setSetting } from "../db";
import { detectProviders, getBestProvider } from "../providers";

const router = Router();

// GET /api/settings
router.get("/", (_req: Request, res: Response) => {
  const settings = getAllSettings();
  const providers = detectProviders();
  const best = getBestProvider();
  res.json({ settings, providers, activeProvider: best });
});

// POST /api/settings
router.post("/", (req: Request, res: Response) => {
  const { key, value } = req.body as { key?: string; value?: string };
  if (!key) {
    res.status(400).json({ error: "key required" });
    return;
  }
  setSetting(key, value ?? "");
  res.json({ ok: true });
});

// GET /api/settings/providers
router.get("/providers", (_req: Request, res: Response) => {
  const providers = detectProviders();
  const active = getBestProvider();
  res.json({ providers, active });
});

export default router;
