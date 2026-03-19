"""5 specialist review agent nodes."""

import json
import asyncio

import redis

from app.core.config import get_settings
from app.services.litellm_service import call_llm
from agents.state import ReviewState

settings = get_settings()
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


AGENT_PROMPTS = {
    "logic": """You are an expert code reviewer specializing in LOGIC and CORRECTNESS.
Review the code diff for:
- Logical errors, off-by-one errors, incorrect conditions
- Missing null/undefined checks where needed
- Race conditions or concurrency issues
- Incorrect algorithm implementations
- Wrong variable usage or scope issues

For each issue found, respond with a JSON array of findings.""",

    "security": """You are an expert code reviewer specializing in SECURITY.
Review the code diff for:
- SQL injection, XSS, command injection vulnerabilities
- Authentication/authorization flaws
- Sensitive data exposure (hardcoded secrets, logging PII)
- Insecure cryptographic usage
- CSRF, SSRF, path traversal vulnerabilities
- Dependency vulnerabilities

For each issue found, respond with a JSON array of findings.""",

    "edge_case": """You are an expert code reviewer specializing in EDGE CASES and ROBUSTNESS.
Review the code diff for:
- Unhandled edge cases (empty inputs, boundary values, overflow)
- Missing error handling for expected failure modes
- Incomplete input validation at system boundaries
- Resource leaks (unclosed connections, file handles)
- Timeout and retry logic gaps

For each issue found, respond with a JSON array of findings.""",

    "convention": """You are an expert code reviewer specializing in CODE CONVENTIONS and MAINTAINABILITY.
Review the code diff for:
- Naming convention violations
- Inconsistent code style within the codebase context
- Dead code or unnecessary complexity
- Missing or misleading documentation on public APIs
- Violations of DRY, SOLID, or other design principles
- Type safety issues

For each issue found, respond with a JSON array of findings.""",

    "performance": """You are an expert code reviewer specializing in PERFORMANCE.
Review the code diff for:
- N+1 query patterns or unnecessary database calls
- Missing indexes for queried fields
- Unnecessary memory allocations or copies
- Blocking operations in async contexts
- Missing caching opportunities for expensive operations
- Inefficient algorithms (O(n²) where O(n) is possible)

For each issue found, respond with a JSON array of findings.""",
}

FINDING_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "review_findings",
        "schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "severity": {"type": "string", "enum": ["high", "medium", "low", "info"]},
                            "file_path": {"type": "string"},
                            "line_number": {"type": "integer"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "suggested_fix": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["severity", "file_path", "title", "description", "confidence"],
                    },
                }
            },
            "required": ["findings"],
        },
    },
}


def _publish_ws(review_id: str, event: str, data: dict):
    payload = json.dumps({"room": f"review:{review_id}", "event": event, "data": data})
    _get_redis().publish("ws:events", payload)


def _build_diff_context(files: list[dict]) -> str:
    """Build a concise diff context string for the LLM."""
    parts = []
    for f in files:
        parts.append(f"### {f['filename']}\n```diff\n{f['patch']}\n```")
    return "\n\n".join(parts)


def _make_review_node(agent_role: str):
    """Factory: create a LangGraph node function for a specific review agent."""

    def node(state: ReviewState) -> dict:
        review_id = state["review_id"]
        files = state["files"]

        if not files:
            return {"findings": [], "total_tokens": 0, "total_cost_usd": 0}

        _publish_ws(review_id, "review:agent:started", {
            "agent": agent_role,
            "status": "running",
        })

        diff_context = _build_diff_context(files)
        system_prompt = AGENT_PROMPTS[agent_role]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review this PR diff:\n\n{diff_context}"},
        ]

        try:
            # Run async call_llm in sync context (Celery)
            loop = asyncio.new_event_loop()
            try:
                response = loop.run_until_complete(
                    call_llm(messages, response_format=FINDING_SCHEMA)
                )
            finally:
                loop.close()

            result = json.loads(response.content)
            findings = result.get("findings", [])

            # Annotate each finding with agent role and cost
            per_finding_cost = response.cost_usd / max(len(findings), 1)
            for f in findings:
                f["agent_role"] = agent_role
                f["tokens_used"] = response.total_tokens // max(len(findings), 1)
                f["cost_usd"] = per_finding_cost

            _publish_ws(review_id, "review:agent:completed", {
                "agent": agent_role,
                "findings_count": len(findings),
                "tokens": response.total_tokens,
                "cost_usd": response.cost_usd,
            })

            # Emit individual findings for live UI
            for f in findings:
                _publish_ws(review_id, "review:finding", f)

            return {
                "findings": findings,
                "total_tokens": response.total_tokens,
                "total_cost_usd": response.cost_usd,
            }

        except Exception as e:
            _publish_ws(review_id, "review:agent:error", {
                "agent": agent_role,
                "error": str(e),
            })
            return {"findings": [], "total_tokens": 0, "total_cost_usd": 0}

    node.__name__ = f"{agent_role}_node"
    return node


# Create the 5 specialist agent nodes
logic_node = _make_review_node("logic")
security_node = _make_review_node("security")
edge_case_node = _make_review_node("edge_case")
convention_node = _make_review_node("convention")
performance_node = _make_review_node("performance")
