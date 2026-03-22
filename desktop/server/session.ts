import { v4 as uuid } from "uuid";
import { WebSocket } from "ws";
import { fetchPRDiff } from "./github-service";
import { getSetting, updateReview, addFinding, createReview } from "./db";
import * as db from "./db";
import { getBestProvider } from "./providers";
import { spawn } from "child_process";

const AGENT_PROMPTS: Record<string, string> = {
  logic: `You are an expert code reviewer specializing in LOGIC and CORRECTNESS.
Review for: logical errors, off-by-one, incorrect conditions, null checks, race conditions.`,

  security: `You are an expert code reviewer specializing in SECURITY.
Review for: SQL injection, XSS, auth flaws, secret exposure, CSRF, SSRF.`,

  edge_case: `You are an expert code reviewer specializing in EDGE CASES and ROBUSTNESS.
Review for: unhandled edge cases, missing error handling, input validation, resource leaks.`,

  convention: `You are an expert code reviewer specializing in CODE CONVENTIONS.
Review for: naming violations, inconsistent style, dead code, DRY/SOLID violations.`,

  performance: `You are an expert code reviewer specializing in PERFORMANCE.
Review for: N+1 queries, missing indexes, memory issues, blocking async, inefficient algorithms.`,
};

const FINDING_INSTRUCTION = `
Respond with ONLY a JSON object (no markdown, no explanation):
{"findings": [{"severity": "high|medium|low|info", "file_path": "path", "line_number": 42, "title": "Short title", "description": "Detailed explanation", "suggested_fix": "suggestion or null", "confidence": 0.9}]}
If no issues: {"findings": []}`;

export interface NormalizedFinding {
  agent_role: string;
  severity: string;
  file_path: string;
  line_number: number | null;
  title: string;
  description: string;
  suggested_fix: string | null;
  confidence: number;
}

export class ReviewSession {
  id: string;
  prUrl: string;
  subscribers: Set<WebSocket> = new Set();
  running = false;

  constructor(id: string, prUrl: string) {
    this.id = id;
    this.prUrl = prUrl;
  }

  subscribe(ws: WebSocket): void {
    this.subscribers.add(ws);
  }

  unsubscribe(ws: WebSocket): void {
    this.subscribers.delete(ws);
  }

  broadcast(type: string, data: Record<string, unknown>): void {
    const msg = JSON.stringify({ type, reviewId: this.id, ...data });
    for (const ws of this.subscribers) {
      try {
        ws.send(msg);
      } catch {
        this.subscribers.delete(ws);
      }
    }
  }

  async run(): Promise<void> {
    if (this.running) return;
    this.running = true;

    const token =
      getSetting("github_token") || process.env.GITHUB_TOKEN || "";
    if (!token) {
      this.broadcast("error", { error: "GitHub token not configured" });
      db.updateReview(this.id, {
        status: "failed",
        error_message: "GitHub token not configured",
      });
      this.running = false;
      return;
    }

    try {
      db.updateReview(this.id, { status: "running" });
      this.broadcast("review:started", {});

      // 1. Fetch PR diff
      this.broadcast("agent:started", { agent: "fetch_diff" });
      const diff = await fetchPRDiff(this.prUrl, token);
      this.broadcast("agent:completed", {
        agent: "fetch_diff",
        filesCount: diff.files.length,
      });

      if (!diff.files.length) {
        db.updateReview(this.id, {
          status: "completed",
          total_issues: 0,
          completed_at: new Date().toISOString(),
        });
        this.broadcast("review:completed", { totalIssues: 0 });
        this.running = false;
        return;
      }

      const diffContext = diff.files
        .map((f) => `### ${f.filename}\n\`\`\`diff\n${f.patch}\n\`\`\``)
        .join("\n\n");

      // 2. Run all 5 specialist agents
      const allFindings: NormalizedFinding[] = [];

      for (const [role, prompt] of Object.entries(AGENT_PROMPTS)) {
        this.broadcast("agent:started", { agent: role });
        try {
          const findings = await this.runAgent(role, prompt, diffContext);
          allFindings.push(...findings);
          this.broadcast("agent:completed", {
            agent: role,
            findingsCount: findings.length,
          });

          for (const f of findings) {
            const fid = uuid();
            db.addFinding({ id: fid, review_id: this.id, ...f });
            this.broadcast("finding", { finding: { id: fid, ...f } });
          }
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : String(err);
          this.broadcast("agent:error", { agent: role, error: message });
        }
      }

      // 3. Complete
      db.updateReview(this.id, {
        status: "completed",
        total_issues: allFindings.length,
        completed_at: new Date().toISOString(),
      });
      this.broadcast("review:completed", { totalIssues: allFindings.length });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      db.updateReview(this.id, {
        status: "failed",
        error_message: message,
        completed_at: new Date().toISOString(),
      });
      this.broadcast("error", { error: message });
    } finally {
      this.running = false;
    }
  }

  private async runAgent(
    role: string,
    systemPrompt: string,
    diffContext: string
  ): Promise<NormalizedFinding[]> {
    // Combine system + user into a single user message because the SDK routes
    // all content through the CLI which accepts a single prompt string.
    const combinedPrompt =
      systemPrompt +
      "\n\n" +
      FINDING_INSTRUCTION +
      "\n\nReview this PR diff and respond with ONLY the JSON findings:\n\n" +
      diffContext;

    let text = "";
    try {
      text = await this.runViaClaude(combinedPrompt);
    } catch {
      text = await this.runViaSubprocess(combinedPrompt);
    }

    return this.parseFindings(role, text);
  }

  private async runViaClaude(combinedPrompt: string): Promise<string> {
    const ClaudeCodeModule = await import("claude-code-sdk");
    const ClaudeCode = ClaudeCodeModule.default;
    const client = new ClaudeCode();
    const response = await client.messages.create({
      model: "claude-opus-4-5",
      messages: [{ role: "user", content: combinedPrompt }],
      max_tokens: 4096,
    });
    let text = "";
    for (const block of response.content) {
      if (block.text) text += block.text;
    }
    return text;
  }

  private async runViaSubprocess(combinedPrompt: string): Promise<string> {
    const provider = getBestProvider();
    if (!provider) throw new Error("No AI CLI available");

    const fullPrompt = combinedPrompt;

    return new Promise((resolve, reject) => {
      let stdout = "";

      const args =
        provider.name === "codex"
          ? ["exec", "--full-auto", "-q", fullPrompt]
          : ["-p", fullPrompt];

      const proc = spawn(provider.command, args, { timeout: 120_000 });
      proc.stdout?.on("data", (d: Buffer) => {
        stdout += d.toString();
      });
      proc.on("close", () => resolve(stdout));
      proc.on("error", reject);
    });
  }

  private parseFindings(role: string, text: string): NormalizedFinding[] {
    const normalize = (findings: unknown[]): NormalizedFinding[] =>
      findings.map((f: unknown) => {
        const item = f as Record<string, unknown>;
        return {
          agent_role: role,
          severity: (item.severity as string) || "info",
          file_path: (item.file_path as string) || "",
          line_number: (item.line_number as number | null) ?? null,
          title: (item.title as string) || "",
          description: (item.description as string) || "",
          suggested_fix: (item.suggested_fix as string | null) ?? null,
          confidence: (item.confidence as number) || 0.5,
        };
      });

    if (!text) return [];

    try {
      const result = JSON.parse(text) as { findings?: unknown[] };
      return normalize(result.findings || []);
    } catch {
      // Attempt to extract embedded JSON
      const match = text.match(/\{[\s\S]*"findings"[\s\S]*\}/);
      if (match) {
        try {
          const result = JSON.parse(match[0]) as { findings?: unknown[] };
          return normalize(result.findings || []);
        } catch {
          return [];
        }
      }
      return [];
    }
  }
}
