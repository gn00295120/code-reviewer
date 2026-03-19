from dataclasses import dataclass

import litellm

from app.core.config import get_settings

settings = get_settings()

# Configure LiteLLM to use proxy
litellm.api_base = settings.litellm_proxy_url
litellm.api_key = settings.litellm_master_key


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    model: str


async def call_llm(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    response_format: dict | None = None,
) -> LLMResponse:
    """Call LLM via LiteLLM with cost tracking."""
    model = model or settings.default_model

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    response = await litellm.acompletion(**kwargs)

    usage = response.usage
    cost = litellm.completion_cost(completion_response=response)

    return LLMResponse(
        content=response.choices[0].message.content,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        cost_usd=cost,
        model=model,
    )
