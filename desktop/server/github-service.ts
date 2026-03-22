import { Octokit } from "@octokit/rest";

export interface FileDiff {
  filename: string;
  patch: string;
  additions: number;
  deletions: number;
  status: string;
}

export interface PRDiff {
  repoName: string;
  prNumber: number;
  title: string;
  body: string;
  baseBranch: string;
  headBranch: string;
  files: FileDiff[];
  totalAdditions: number;
  totalDeletions: number;
}

export interface ParsedPRUrl {
  owner: string;
  repo: string;
  number: number;
  platform: string;
}

const SKIP_PATTERNS = [
  ".lock",
  ".sum",
  "package-lock.json",
  "yarn.lock",
  ".min.js",
  ".min.css",
  ".map",
  ".png",
  ".jpg",
  ".svg",
  ".ico",
  ".woff",
  ".woff2",
];

function shouldSkip(filename: string): boolean {
  return SKIP_PATTERNS.some((ext) => filename.endsWith(ext));
}

export function parsePRUrl(url: string): ParsedPRUrl | null {
  // GitHub
  const ghMatch = url.match(
    /https?:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/
  );
  if (ghMatch) {
    return {
      owner: ghMatch[1],
      repo: ghMatch[2],
      number: parseInt(ghMatch[3], 10),
      platform: "github",
    };
  }

  // GitLab (basic — for display only, not API)
  const glMatch = url.match(
    /https?:\/\/[^/]+\/(.+?)\/-\/merge_requests\/(\d+)/
  );
  if (glMatch) {
    return {
      owner: "",
      repo: glMatch[1],
      number: parseInt(glMatch[2], 10),
      platform: "gitlab",
    };
  }

  return null;
}

export async function fetchPRDiff(
  prUrl: string,
  token: string
): Promise<PRDiff> {
  const parsed = parsePRUrl(prUrl);
  if (!parsed || parsed.platform !== "github") {
    throw new Error("Only GitHub PRs supported in desktop mode");
  }

  const octokit = new Octokit({ auth: token });

  const { data: pr } = await octokit.pulls.get({
    owner: parsed.owner,
    repo: parsed.repo,
    pull_number: parsed.number,
  });

  const { data: prFiles } = await octokit.pulls.listFiles({
    owner: parsed.owner,
    repo: parsed.repo,
    pull_number: parsed.number,
    per_page: 100,
  });

  const files: FileDiff[] = [];
  let totalAdditions = 0;
  let totalDeletions = 0;

  for (const f of prFiles) {
    if (shouldSkip(f.filename) || !f.patch) continue;
    files.push({
      filename: f.filename,
      patch: f.patch,
      additions: f.additions,
      deletions: f.deletions,
      status: f.status,
    });
    totalAdditions += f.additions;
    totalDeletions += f.deletions;
  }

  return {
    repoName: `${parsed.owner}/${parsed.repo}`,
    prNumber: parsed.number,
    title: pr.title,
    body: pr.body || "",
    baseBranch: pr.base.ref,
    headBranch: pr.head.ref,
    files,
    totalAdditions,
    totalDeletions,
  };
}

export interface Finding {
  severity: string;
  file_path: string;
  line_number?: number | null;
  title: string;
  description: string;
  suggested_fix?: string | null;
  agent_role?: string;
  confidence?: number;
}

export async function postInlineComments(
  prUrl: string,
  token: string,
  findings: Finding[]
): Promise<number> {
  const parsed = parsePRUrl(prUrl);
  if (!parsed || parsed.platform !== "github") return 0;

  const octokit = new Octokit({ auth: token });

  const comments = findings
    .filter((f) => f.file_path)
    .map((f) => {
      let body = `**[${f.severity.toUpperCase()}]** ${f.title}\n\n${f.description}`;
      if (f.suggested_fix) {
        body += `\n\n\`\`\`suggestion\n${f.suggested_fix}\n\`\`\``;
      }
      body += `\n\n_Agent: ${f.agent_role ?? "unknown"} | Confidence: ${Math.round((f.confidence ?? 0.5) * 100)}%_`;

      const comment: Record<string, unknown> = {
        path: f.file_path,
        body,
      };
      if (f.line_number) {
        comment.line = f.line_number;
        comment.side = "RIGHT";
      }
      return comment;
    });

  if (!comments.length) return 0;

  const uniqueFiles = new Set(comments.map((c) => c.path as string)).size;

  type ReviewComment = NonNullable<
    Parameters<typeof octokit.pulls.createReview>[0]["comments"]
  >[number];

  await octokit.pulls.createReview({
    owner: parsed.owner,
    repo: parsed.repo,
    pull_number: parsed.number,
    body: `## SwarmForge Code Review\n\nFound **${comments.length}** issues across ${uniqueFiles} files.`,
    event: "COMMENT",
    comments: comments as ReviewComment[],
  });

  return comments.length;
}
