# SwarmForge

[![CI](https://github.com/longweiwang/code-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/longweiwang/code-reviewer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)

**Command Center IDE** — Visual, forkable Agent Command Center with enterprise-grade AI code review.

## Modules

| Module | Description |
|--------|-------------|
| **Code Review Dashboard** | 5 specialist AI agents review PRs in parallel (logic, security, edge cases, convention, performance) |
| **World Model Sandbox** | LLM-driven physics simulation with MuJoCo + Three.js |
| **Agent Community Feed** | Agent orgs, stigmergy collaboration, one-click fork |
| **Command Center** | Visual management of agent teams with React Flow |

## Quick Start

```bash
# 1. Configure
cp .env.example .env
# Edit .env: add GITHUB_TOKEN and/or GITLAB_TOKEN, ANTHROPIC_API_KEY

# 2. Start infrastructure
make up

# 3. Run migrations
make migrate

# 4. Start frontend
cd frontend && npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **LiteLLM Proxy**: http://localhost:4000

## Platform Support

SwarmForge supports both **GitHub** and **GitLab** (including self-hosted instances).

### GitHub Setup

1. Set `GITHUB_TOKEN` in `.env` — a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope.
2. (Optional) Set `GITHUB_WEBHOOK_SECRET` for auto-triggering reviews on PR events.

### GitLab Setup

1. Set `GITLAB_TOKEN` in `.env` — a [Personal Access Token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) with `api` scope.
2. (Optional) Set `GITLAB_WEBHOOK_SECRET` for auto-triggering reviews on MR events.
3. Self-hosted GitLab works automatically — the platform is detected from the URL.

### Manual Review

Paste a PR/MR URL in the review input on the dashboard:

```
# GitHub
https://github.com/owner/repo/pull/123

# GitLab (gitlab.com)
https://gitlab.com/group/project/-/merge_requests/456

# GitLab (self-hosted)
https://gitlab.company.com/team/project/-/merge_requests/789
```

### Webhook Auto-Trigger

Configure webhooks so reviews start automatically when PRs/MRs are opened or updated.

**GitHub** — Go to repo Settings → Webhooks → Add webhook:

| Field | Value |
|-------|-------|
| Payload URL | `https://<your-host>:8000/api/webhooks/github` |
| Content type | `application/json` |
| Secret | Same as `GITHUB_WEBHOOK_SECRET` in `.env` |
| Events | Select "Pull requests" |

**GitLab** — Go to project Settings → Webhooks:

| Field | Value |
|-------|-------|
| URL | `https://<your-host>:8000/api/webhooks/gitlab` |
| Secret token | Same as `GITLAB_WEBHOOK_SECRET` in `.env` |
| Trigger | Check "Merge request events" |

### Post Results Back

After a review completes, click **"Post to GitHub"** or **"Post to GitLab"** to send findings as inline comments on the PR/MR. You can also call the API directly:

```bash
curl -X POST http://localhost:8000/api/reviews/{review_id}/post-to-github?severity_threshold=medium
```

### API Examples

```bash
# Create a review (GitHub)
curl -X POST http://localhost:8000/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"pr_url": "https://github.com/owner/repo/pull/123"}'

# Create a review (GitLab)
curl -X POST http://localhost:8000/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"pr_url": "https://gitlab.com/group/project/-/merge_requests/456"}'

# List reviews (filter by platform)
curl http://localhost:8000/api/reviews?platform=gitlab

# Check review status
curl http://localhost:8000/api/reviews/{review_id}
```

## Architecture

```
Next.js 15 ──WebSocket──► FastAPI ──Celery──► LangGraph Pipeline
  (React Flow,              (REST API,         (5 Review Agents,
   Three.js,                 WebSocket,          Physics Agent)
   Zustand)                  Redis pub/sub)
                                │
                          PostgreSQL + Redis + LiteLLM
```

## Tech Stack

- **Frontend**: Next.js 15, React Flow, Three.js, shadcn/ui, Zustand, TanStack Query
- **Backend**: FastAPI, Celery, SQLAlchemy (async), Alembic
- **AI**: LangGraph multi-agent pipelines, LiteLLM proxy (Claude Sonnet 4.6 default)
- **Infra**: Docker Compose, PostgreSQL 16, Redis 7

## API Endpoints

| Module | Endpoints |
|--------|-----------|
| Reviews | `POST/GET /api/reviews`, `POST /api/reviews/{id}/post-to-github` |
| Webhooks | `POST /api/webhooks/github`, `POST /api/webhooks/gitlab` |
| World Models | `POST/GET /api/world-models`, `POST /{id}/start/pause/step/reset` |
| Community | `POST/GET /api/orgs`, `POST /{id}/fork`, `GET /api/feed` |
| Stats | `GET /api/stats/queue`, `GET /api/stats/overview` |

## Development

```bash
make up          # Start Docker services
make down        # Stop Docker services
make migrate     # Run database migrations
make test        # Run all tests
make lint        # Run linters
make logs        # Tail Docker logs
```

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository and create a feature branch from `main`.
2. Install dependencies and confirm the test suite passes locally (`make test`).
3. Write or update tests to cover your changes — the CI pipeline enforces this.
4. Open a pull request against `main`. The CI jobs (backend tests + frontend build) must be green before review.
5. A maintainer will review and merge. For large changes, open an issue first to discuss the approach.

Please follow the existing code style and keep commits focused and conventional (e.g. `feat:`, `fix:`, `docs:`).

## License

MIT
