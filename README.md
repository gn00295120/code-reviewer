# SwarmForge

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
# Edit .env: add GITHUB_TOKEN, ANTHROPIC_API_KEY

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
| Webhooks | `POST /api/webhooks/github` |
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

## License

MIT
