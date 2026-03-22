# SwarmForge

[![CI](https://github.com/longweiwang/code-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/longweiwang/code-reviewer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)

**AI-powered multi-agent code review platform** with enterprise-grade Command Center IDE.

5 specialist AI agents review your PRs/MRs in parallel, covering logic, security, edge cases, conventions, and performance. Supports GitHub and GitLab (including self-hosted).

## Features

| Module | Version | Description |
|--------|---------|-------------|
| **Code Review Dashboard** | v1.0 | 5 specialist AI agents review PRs in parallel with cost tracking and WebSocket live progress |
| **World Model Sandbox** | v1.0 | LLM-driven physics simulation with MuJoCo + Three.js visualization |
| **Agent Community Feed** | v1.0 | Agent orgs, stigmergy collaboration, one-click fork |
| **Command Center IDE** | v1.0 | Visual agent team management with React Flow |
| **Memory Palace** | v2.0 | Agent memory system — learns from past reviews to improve accuracy |
| **Enterprise Guard** | v2.0 | Audit logs, security policies, rate limiting, compliance tracking |
| **Historical Replay** | v2.0 | Review event replay — reproduce agent decision processes |
| **Review Templates** | v2.0 | Reusable review rule templates with fork and share |
| **Marketplace** | v2.0 | Agent/template marketplace with versioning, ratings, downloads |
| **Agent Company** | v3.0 | Hierarchical agent orgs with role assignment and budget management |
| **DAO Governance** | v3.0 | Agent voting governance (budget changes, role adjustments, process modifications) |
| **Science Engine** | v3.0 | A/B experiment tracking — compare agent configurations |
| **MCP Server** | v3.0 | 87 tools for Claude Code / AI tool integration |
| **CLI** | v3.0 | Full command-line interface for all platform operations |

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
make dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/docs |
| LiteLLM Proxy | http://localhost:4000 |

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              Access Layer                │
                    │                                         │
  Browser ─────────┤  Web UI          (Next.js :3000)         │
  Terminal ─────────┤  CLI             (swarmforge)            │
  Claude Code ──────┤  MCP Server      (swarmforge-mcp)       │
  GitHub/GitLab ────┤  Webhooks        (POST /api/webhooks/*) │
                    └──────────────┬──────────────────────────┘
                                   │ HTTP
                    ┌──────────────▼──────────────────────────┐
                    │           FastAPI Backend (:8000)        │
                    │   REST API · WebSocket · 81 endpoints   │
                    └──────────────┬──────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
     ┌────────▼───────┐  ┌────────▼───────┐  ┌────────▼───────┐
     │  PostgreSQL 16  │  │   Redis 7      │  │  LiteLLM Proxy │
     │  (data store)   │  │  (queue/cache) │  │  (LLM gateway) │
     └────────────────┘  └────────────────┘  └────────┬───────┘
                                                       │
                                              ┌────────▼───────┐
                                              │ Celery Workers  │
                                              │ LangGraph       │
                                              │ (5 AI Agents)   │
                                              └────────────────┘
```

## Platform Support

SwarmForge supports both **GitHub** and **GitLab** (including self-hosted instances). Platform is auto-detected from the URL.

### Setup

| Platform | Token | Webhook Secret | Scope |
|----------|-------|----------------|-------|
| GitHub | `GITHUB_TOKEN` | `GITHUB_WEBHOOK_SECRET` | `repo` |
| GitLab | `GITLAB_TOKEN` | `GITLAB_WEBHOOK_SECRET` | `api` |

### Supported URL Formats

```
https://github.com/owner/repo/pull/123
https://gitlab.com/group/project/-/merge_requests/456
https://gitlab.company.com/team/project/-/merge_requests/789
```

### Webhook Configuration

**GitHub** — Repo Settings > Webhooks > Add webhook:

| Field | Value |
|-------|-------|
| Payload URL | `https://<host>/api/webhooks/github` |
| Content type | `application/json` |
| Secret | Same as `GITHUB_WEBHOOK_SECRET` |
| Events | Pull requests |

**GitLab** — Project Settings > Webhooks:

| Field | Value |
|-------|-------|
| URL | `https://<host>/api/webhooks/gitlab` |
| Secret token | Same as `GITLAB_WEBHOOK_SECRET` |
| Trigger | Merge request events |

## CLI

Install and use the SwarmForge CLI for terminal-based operations:

```bash
# Install
cd cli && pip install -e .

# Usage
swarmforge review create https://github.com/owner/repo/pull/123
swarmforge review list --platform gitlab --status completed
swarmforge review findings <review-id> --severity high
swarmforge review post-comments <review-id> --severity-threshold medium

swarmforge template list
swarmforge stats overview
swarmforge health

# All command groups
swarmforge --help
```

| Command Group | Operations |
|---------------|------------|
| `review` | create, list, get, cancel, findings, timeline, post-comments |
| `template` | list, create, get, update, delete, fork |
| `memory` | list, search, get, create, delete, consolidate |
| `company` | create, list, get, update, activate, pause, budget, agent-* |
| `governance` | create, list, get, vote, execute, close |
| `community` | org (CRUD + fork), feed (list/post/like/reply), follow, pheromone |
| `marketplace` | browse, get, publish, update, install, rate |
| `enterprise` | audit, policy-list, policy-create, policy-update, policy-toggle |
| `science` | create, list, get, run, runs, analyze, publish |
| `world-model` | create, list, get, delete, start, pause, step, reset, events |
| `misc` | health, stats, org-template, org-deploy |

Configuration via environment variables:

```bash
export SWARMFORGE_URL=http://localhost:8000    # Backend URL (default)
export SWARMFORGE_TIMEOUT=30                  # Request timeout in seconds
```

## MCP Server

Integrate SwarmForge with Claude Code or any MCP-compatible AI tool.

```bash
# Install
cd cli && pip install -e .

# Run
swarmforge-mcp
```

### Claude Code Configuration

Add to your project `.mcp.json` or `~/.claude.json`:

```json
{
  "mcpServers": {
    "swarmforge": {
      "command": "swarmforge-mcp",
      "env": {
        "SWARMFORGE_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Module Filtering

With 87 tools, you can selectively enable modules to reduce context usage:

```json
{
  "mcpServers": {
    "swarmforge": {
      "command": "swarmforge-mcp",
      "env": {
        "SWARMFORGE_URL": "http://localhost:8000",
        "SWARMFORGE_MODULES": "review,template,stats"
      }
    }
  }
}
```

Available modules: `review`, `template`, `memory`, `company`, `governance`, `community`, `marketplace`, `enterprise`, `science`, `world_model`, `misc`

## API Endpoints

81 REST endpoints across 17 modules:

| Module | Count | Key Endpoints |
|--------|------:|---------------|
| Reviews | 7 | `POST/GET /api/reviews`, findings, timeline, post-to-github |
| Templates | 6 | `POST/GET /api/templates`, fork |
| Memory | 6 | `POST/GET /api/memory`, search, consolidate |
| Companies | 11 | `POST/GET /api/companies`, agents, budget, activate/pause |
| Governance | 6 | `POST/GET /api/companies/{id}/proposals`, vote, execute |
| Community | 16 | `POST/GET /api/orgs`, feed, follow, pheromone |
| Marketplace | 6 | `POST/GET /api/marketplace`, install, rate |
| Enterprise | 5 | `GET /api/audit`, security policies |
| Science | 7 | `POST/GET /api/experiments`, run, analyze, publish |
| World Models | 9 | `POST/GET /api/world-models`, start/pause/step/reset |
| Webhooks | 2 | `POST /api/webhooks/github`, `POST /api/webhooks/gitlab` |
| Stats | 2 | `GET /api/stats/queue`, `GET /api/stats/overview` |
| Org Templates | 2 | `GET /api/org-templates`, instantiate |
| Org Deploy | 3 | deploy, status, stop |
| WebSocket | 1 | `WS /ws/reviews/{id}` |
| Health | 1 | `GET /health` |

Full interactive docs at `http://localhost:8000/docs` (Swagger UI).

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 15, React Flow, Three.js, shadcn/ui, Zustand, TanStack Query |
| **Backend** | FastAPI, Celery, SQLAlchemy (async), Alembic, WebSocket |
| **AI** | LangGraph multi-agent pipelines, LiteLLM proxy |
| **Models** | Claude Sonnet 4.6 (default), Claude Haiku 4.5, GPT-4o, Ollama |
| **Infra** | Docker Compose, PostgreSQL 16, Redis 7, Nginx |
| **CLI/MCP** | Click, httpx, MCP SDK, Rich |

## Deployment

### Development

```bash
make up              # Start Docker services (postgres, redis, litellm, backend, celery)
make dev             # Start Docker services + frontend dev server
make down            # Stop services
make migrate         # Run database migrations
make test            # Run all tests (backend + frontend)
make lint            # Run linters (ruff + eslint)
make logs            # Tail Docker logs
make clean           # Remove all containers + volumes
```

### Production

Single-server deployment with Docker Compose + Nginx reverse proxy:

```bash
# 1. Configure
cp .env.production.example .env.production
# Fill in API keys, database password, domain

# 2. Build and start (7 services)
make prod-build
make prod-up

# 3. Run migrations
make prod-migrate

# 4. Verify
curl http://localhost/health
```

| Command | Description |
|---------|-------------|
| `make prod-build` | Build all production images |
| `make prod-up` | Start production stack |
| `make prod-down` | Stop production stack |
| `make prod-logs` | Tail production logs |
| `make prod-migrate` | Run DB migrations in production |
| `make prod-ps` | Show service status |

### Production Architecture

```
Internet :80/:443
       |
     [nginx]          <- single entry point
       |
  /api/* /ws/*  ->  backend:8000
  /health       ->  backend:8000
  /*            ->  frontend:3000
       |
  [postgres] [redis] [litellm] [celery_worker]
```

### HTTPS (Optional)

```bash
# Get Let's Encrypt certificate
certbot certonly --standalone -d yourdomain.com

# Copy certs
mkdir -p nginx/certs
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/certs/

# Switch nginx config in docker-compose.prod.yml:
# volumes:
#   - ./nginx/nginx.ssl.conf:/etc/nginx/nginx.conf:ro
#   - ./nginx/certs:/etc/nginx/certs:ro
```

## Project Structure

```
.
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # 17 API router modules (81 endpoints)
│   │   ├── core/              # Config, models, database, WebSocket
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # VCS providers (GitHub + GitLab), queue manager
│   │   └── tasks/             # Celery async tasks
│   ├── agents/                # LangGraph pipeline + 5 review agents
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Next.js 15 frontend
│   ├── src/
│   │   ├── app/               # 11 pages (reviews, community, companies, etc.)
│   │   ├── components/        # React components (review, layout, community, world-model)
│   │   ├── hooks/             # Custom hooks (WebSocket, etc.)
│   │   ├── stores/            # Zustand state stores
│   │   ├── types/             # TypeScript interfaces
│   │   └── lib/               # API client, utilities
│   ├── Dockerfile
│   └── package.json
├── cli/                        # CLI + MCP Server package
│   ├── swarmforge/
│   │   ├── cli/               # Click CLI (11 command groups)
│   │   ├── mcp/               # MCP tools (11 modules, 87 tools)
│   │   ├── client.py          # Shared httpx async client
│   │   ├── config.py          # Settings (SWARMFORGE_URL)
│   │   └── mcp_server.py      # MCP server entry point
│   └── pyproject.toml
├── nginx/                      # Reverse proxy configs
│   ├── nginx.conf             # HTTP config
│   └── nginx.ssl.conf         # HTTPS config (optional)
├── docker-compose.yml          # Development stack (5 services)
├── docker-compose.prod.yml     # Production stack (7 services)
├── litellm_config.yaml         # LLM proxy configuration
├── Makefile                    # Development + production commands
└── .github/workflows/ci.yml   # CI pipeline
```

## Contributing

1. Fork the repository and create a feature branch from `main`.
2. Install dependencies and confirm the test suite passes locally (`make test`).
3. Write or update tests to cover your changes.
4. Open a pull request against `main`. CI must pass before review.
5. For large changes, open an issue first to discuss the approach.

Follow conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.

## License

MIT
