from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "SwarmForge"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://swarmforge:swarmforge@localhost:5432/swarmforge"
    database_url_sync: str = "postgresql://swarmforge:swarmforge@localhost:5432/swarmforge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # GitHub
    github_token: str = ""
    github_webhook_secret: str = ""

    # LiteLLM
    litellm_proxy_url: str = "http://localhost:4000"
    litellm_master_key: str = "sk-litellm-master-key"

    # Default model
    default_model: str = "anthropic/claude-sonnet-4-6"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
