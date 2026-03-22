import Database from "better-sqlite3";
import path from "path";
import os from "os";
import fs from "fs";

function getDbPath(): string {
  const dataDir =
    process.env.SWARMFORGE_DATA_DIR || path.join(os.homedir(), ".swarmforge");
  fs.mkdirSync(dataDir, { recursive: true, mode: 0o700 });
  return path.join(dataDir, "swarmforge.db");
}

const db = new Database(getDbPath());
db.pragma("journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    pr_url TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    pr_number INTEGER,
    platform TEXT DEFAULT 'github',
    provider TEXT DEFAULT 'auto',
    status TEXT DEFAULT 'pending',
    total_issues INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
  );

  CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    agent_role TEXT NOT NULL,
    severity TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    suggested_fix TEXT,
    confidence REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
  );

  CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT,
    agent_role TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  );
`);

export { db };

// Settings CRUD

export function getSetting(key: string): string | null {
  const row = db
    .prepare("SELECT value FROM settings WHERE key = ?")
    .get(key) as { value: string } | undefined;
  return row?.value ?? null;
}

export function setSetting(key: string, value: string): void {
  db.prepare(
    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
  ).run(key, value);
}

export function getAllSettings(): Record<string, string> {
  const rows = db
    .prepare("SELECT key, value FROM settings")
    .all() as { key: string; value: string }[];
  return Object.fromEntries(rows.map((r) => [r.key, r.value]));
}

// Review CRUD

export interface CreateReviewData {
  id: string;
  pr_url: string;
  repo_name: string;
  pr_number: number;
  platform: string;
  provider: string;
}

export function createReview(data: CreateReviewData): void {
  db.prepare(
    `INSERT INTO reviews (id, pr_url, repo_name, pr_number, platform, provider, status)
     VALUES (?, ?, ?, ?, ?, ?, 'pending')`
  ).run(
    data.id,
    data.pr_url,
    data.repo_name,
    data.pr_number,
    data.platform,
    data.provider
  );
}

export function updateReview(id: string, updates: Record<string, unknown>): void {
  const sets = Object.keys(updates)
    .map((k) => `${k} = ?`)
    .join(", ");
  db.prepare(`UPDATE reviews SET ${sets} WHERE id = ?`).run(
    ...Object.values(updates),
    id
  );
}

export function getReview(id: string): unknown {
  return db.prepare("SELECT * FROM reviews WHERE id = ?").get(id);
}

export function listReviews(limit = 50): unknown[] {
  return db
    .prepare("SELECT * FROM reviews ORDER BY created_at DESC LIMIT ?")
    .all(limit);
}

// Finding CRUD

export interface AddFindingData {
  id: string;
  review_id: string;
  agent_role: string;
  severity: string;
  file_path: string;
  line_number?: number | null;
  title: string;
  description: string;
  suggested_fix?: string | null;
  confidence: number;
}

export function addFinding(data: AddFindingData): void {
  db.prepare(
    `INSERT INTO findings (id, review_id, agent_role, severity, file_path, line_number, title, description, suggested_fix, confidence)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).run(
    data.id,
    data.review_id,
    data.agent_role,
    data.severity,
    data.file_path,
    data.line_number ?? null,
    data.title,
    data.description,
    data.suggested_fix ?? null,
    data.confidence
  );
}

export function getFindings(reviewId: string): unknown[] {
  return db
    .prepare(
      "SELECT * FROM findings WHERE review_id = ? ORDER BY created_at"
    )
    .all(reviewId);
}

// Message CRUD

export interface AddMessageData {
  id: string;
  review_id: string;
  role: string;
  content: string;
  agent_role?: string;
}

export function addMessage(data: AddMessageData): void {
  db.prepare(
    `INSERT INTO messages (id, review_id, role, content, agent_role)
     VALUES (?, ?, ?, ?, ?)`
  ).run(
    data.id,
    data.review_id,
    data.role,
    data.content,
    data.agent_role ?? null
  );
}
