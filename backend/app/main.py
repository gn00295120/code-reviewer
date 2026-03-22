import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.community import router as community_router
from app.api.company import router as company_router
from app.api.enterprise import router as enterprise_router
from app.api.governance import router as governance_router
from app.api.governance import proposal_router
from app.api.marketplace import router as marketplace_router
from app.api.memory import router as memory_router
from app.api.org_deploy import router as org_deploy_router
from app.api.org_templates_api import router as org_templates_router
from app.api.reviews import router as reviews_router
from app.api.science import router as science_router
from app.api.templates import router as templates_router
from app.api.webhooks import router as webhooks_router
from app.api.github_actions import router as github_actions_router
from app.api.stats import router as stats_router
from app.api.ws import router as ws_router
from app.api.world_model import router as world_model_router
from app.core.config import get_settings
from app.core.websocket import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.desktop_mode:
        from app.core.database import init_db
        await init_db()
    await ws_manager.startup()
    yield
    await ws_manager.shutdown()


app = FastAPI(
    title="SwarmForge",
    description="AI-powered multi-agent code review platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
_settings = get_settings()
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
if _settings.desktop_mode:
    origins.append("tauri://localhost")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(community_router)
app.include_router(company_router)
app.include_router(enterprise_router)
app.include_router(governance_router)
app.include_router(proposal_router)
app.include_router(marketplace_router)
app.include_router(memory_router)
app.include_router(org_deploy_router)
app.include_router(org_templates_router)
app.include_router(reviews_router)
app.include_router(science_router)
app.include_router(templates_router)
app.include_router(webhooks_router)
app.include_router(github_actions_router)
app.include_router(stats_router)
app.include_router(ws_router)
app.include_router(world_model_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "swarmforge"}
