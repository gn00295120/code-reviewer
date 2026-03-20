"""Enterprise Guard service — audit logging, rate limiting, secret detection, policy enforcement."""

from __future__ import annotations

import re
import time
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AuditLog, SecurityPolicy

# ---------------------------------------------------------------------------
# Simple in-process rate-limit store (resets on restart — use Redis for prod).
# ---------------------------------------------------------------------------

# Structure: { (actor, action): [timestamp, ...] }
_rate_limit_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)

# Default rate limit window and max calls when no matching policy exists.
_DEFAULT_WINDOW_SECONDS = 60
_DEFAULT_MAX_CALLS = 100

# ---------------------------------------------------------------------------
# Secret patterns for detect_secrets
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[re.Pattern] = [
    # Generic API key / token patterns
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?[\w\-]{8,}['\"]?"),
    # AWS keys
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
    # GitHub / GitLab personal access tokens
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36}"),
    re.compile(r"glpat-[A-Za-z0-9\-_]{20}"),
    # Generic base64-looking secrets (≥40 chars)
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
    # Private key headers
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def log_audit(
    db: AsyncSession,
    action: str,
    resource_type: str,
    actor: str | None = None,
    resource_id: UUID | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Persist an audit event and return the created record."""
    entry = AuditLog(
        action=action,
        actor=actor,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry


async def check_rate_limit(
    db: AsyncSession,
    actor: str,
    action: str,
) -> dict[str, Any]:
    """Check whether *actor* is allowed to perform *action*.

    Consults active rate_limit policies first; falls back to module defaults.
    Returns a dict with keys: allowed (bool), remaining (int), reset_in (float seconds).
    """
    # Load applicable rate_limit policy.
    stmt = (
        select(SecurityPolicy)
        .where(SecurityPolicy.policy_type == "rate_limit", SecurityPolicy.is_active.is_(True))
        .order_by(SecurityPolicy.created_at.desc())
    )
    result = await db.execute(stmt)
    policy = result.scalars().first()

    if policy:
        window = int(policy.config.get("window_seconds", _DEFAULT_WINDOW_SECONDS))
        max_calls = int(policy.config.get("max_calls", _DEFAULT_MAX_CALLS))
    else:
        window = _DEFAULT_WINDOW_SECONDS
        max_calls = _DEFAULT_MAX_CALLS

    now = time.time()
    bucket_key = (actor, action)
    bucket = _rate_limit_buckets[bucket_key]

    # Evict timestamps outside the window.
    _rate_limit_buckets[bucket_key] = [ts for ts in bucket if now - ts < window]
    bucket = _rate_limit_buckets[bucket_key]

    if len(bucket) >= max_calls:
        oldest = min(bucket)
        reset_in = window - (now - oldest)
        return {"allowed": False, "remaining": 0, "reset_in": max(reset_in, 0.0)}

    # Record this call.
    _rate_limit_buckets[bucket_key].append(now)
    remaining = max_calls - len(_rate_limit_buckets[bucket_key])
    return {"allowed": True, "remaining": remaining, "reset_in": float(window)}


def detect_secrets(content: str) -> list[dict[str, Any]]:
    """Scan *content* for hardcoded secrets / credentials.

    Returns a list of finding dicts with keys: pattern, match, start, end.
    The actual matched text is partially redacted for safety.
    """
    findings: list[dict[str, Any]] = []
    for pattern in _SECRET_PATTERNS:
        for m in pattern.finditer(content):
            raw = m.group(0)
            # Redact middle portion of the match.
            if len(raw) > 8:
                redacted = raw[:4] + "*" * (len(raw) - 8) + raw[-4:]
            else:
                redacted = "****"
            findings.append(
                {
                    "pattern": pattern.pattern,
                    "match": redacted,
                    "start": m.start(),
                    "end": m.end(),
                }
            )
    return findings


async def enforce_policies(
    db: AsyncSession,
    action: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate all active policies against an action + context.

    Returns a summary of which policies were checked and whether any blocked.
    """
    stmt = select(SecurityPolicy).where(SecurityPolicy.is_active.is_(True))
    result = await db.execute(stmt)
    policies: list[SecurityPolicy] = list(result.scalars().all())

    violations: list[dict[str, Any]] = []
    checked: list[str] = []

    actor = context.get("actor", "unknown")
    content = context.get("content", "")

    for pol in policies:
        checked.append(pol.name)

        if pol.policy_type == "rate_limit":
            rl = await check_rate_limit(db, actor, action)
            if not rl["allowed"]:
                violations.append({"policy": pol.name, "type": "rate_limit", "detail": rl})

        elif pol.policy_type == "secret_detection" and content:
            hits = detect_secrets(str(content))
            if hits:
                violations.append({"policy": pol.name, "type": "secret_detection", "detail": hits})

        elif pol.policy_type == "access_control":
            allowed_roles: list[str] = pol.config.get("allowed_roles", [])
            actor_role: str = context.get("actor_role", "")
            if allowed_roles and actor_role not in allowed_roles:
                violations.append(
                    {
                        "policy": pol.name,
                        "type": "access_control",
                        "detail": f"Role '{actor_role}' not in {allowed_roles}",
                    }
                )

    return {
        "action": action,
        "policies_checked": checked,
        "violations": violations,
        "blocked": len(violations) > 0,
    }
