import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.community import router as community_router
from app.api.reviews import router as reviews_router
from app.api.webhooks import router as webhooks_router
from app.api.github_actions import router as github_actions_router
from app.api.stats import router as stats_router
from app.api.ws import router as ws_router
from app.api.world_model import router as world_model_router
from app.core.websocket import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await ws_manager.startup()
    yield
    # Shutdown
    await ws_manager.shutdown()


app = FastAPI(
    title="SwarmForge",
    description="AI-powered multi-agent code review platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(community_router)
app.include_router(reviews_router)
app.include_router(webhooks_router)
app.include_router(github_actions_router)
app.include_router(stats_router)
app.include_router(ws_router)
app.include_router(world_model_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "swarmforge"}
