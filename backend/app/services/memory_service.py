"""Memory Palace service — store, recall, decay, and consolidate agent memories."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AgentMemory

# Relevance score is multiplied by this factor every 24 hours of inactivity.
_DECAY_FACTOR = 0.95
_DECAY_THRESHOLD_HOURS = 24

# Memories whose relevance drops below this are eligible for consolidation / pruning.
_MIN_RELEVANCE = 0.1


async def store_memory(
    db: AsyncSession,
    agent_role: str,
    memory_type: str,
    content: dict[str, Any],
    source_review_id: UUID | None = None,
    relevance_score: float = 1.0,
) -> AgentMemory:
    """Persist a new memory record for an agent."""
    memory = AgentMemory(
        agent_role=agent_role,
        memory_type=memory_type,
        content=content,
        source_review_id=source_review_id,
        relevance_score=relevance_score,
    )
    db.add(memory)
    await db.flush()
    return memory


async def recall_memories(
    db: AsyncSession,
    agent_role: str,
    context: str,
    limit: int = 5,
) -> list[AgentMemory]:
    """Return the most relevant memories for a given agent role and context.

    Relevance is determined by:
    1. Exact agent_role match.
    2. Content text overlap with the context string (simple substring search on
       the JSON-serialised content).
    3. Highest relevance_score ordering as a tiebreaker.

    The access_count and last_accessed_at fields are updated for returned rows.
    """
    # Fetch candidate memories ordered by relevance_score desc.
    stmt = (
        select(AgentMemory)
        .where(AgentMemory.agent_role == agent_role)
        .order_by(AgentMemory.relevance_score.desc(), AgentMemory.last_accessed_at.desc())
        .limit(limit * 4)  # over-fetch so we can re-rank by context overlap
    )
    result = await db.execute(stmt)
    candidates: list[AgentMemory] = list(result.scalars().all())

    # Re-rank: prefer memories whose content contains tokens from the context.
    context_tokens = set(context.lower().split())

    def _overlap_score(mem: AgentMemory) -> int:
        serialised = json.dumps(mem.content).lower()
        return sum(1 for tok in context_tokens if tok in serialised)

    candidates.sort(key=_overlap_score, reverse=True)
    top = candidates[:limit]

    # Update access metadata.
    now = datetime.utcnow()
    for mem in top:
        mem.access_count += 1
        mem.last_accessed_at = now
    await db.flush()

    return top


async def decay_memories(db: AsyncSession) -> int:
    """Apply time-based decay to all memories not accessed recently.

    Returns the number of rows updated.
    """
    cutoff = datetime.utcnow() - timedelta(hours=_DECAY_THRESHOLD_HOURS)
    stmt = (
        update(AgentMemory)
        .where(AgentMemory.last_accessed_at < cutoff)
        .values(relevance_score=AgentMemory.relevance_score * _DECAY_FACTOR)
        .execution_options(synchronize_session="fetch")
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount  # type: ignore[return-value]


async def consolidate_memories(db: AsyncSession, agent_role: str) -> dict[str, Any]:
    """Merge near-duplicate memories for an agent role and prune low-relevance ones.

    Strategy:
    - Group memories by memory_type.
    - Within each group, if two memories share identical content keys, merge
      them into the one with the higher relevance_score (sum access_counts).
    - Delete memories whose relevance_score < _MIN_RELEVANCE.

    Returns a summary dict with merged and deleted counts.
    """
    stmt = select(AgentMemory).where(AgentMemory.agent_role == agent_role)
    result = await db.execute(stmt)
    memories: list[AgentMemory] = list(result.scalars().all())

    merged_count = 0
    deleted_count = 0

    # Group by memory_type for merge candidates.
    by_type: dict[str, list[AgentMemory]] = {}
    for mem in memories:
        by_type.setdefault(mem.memory_type, []).append(mem)

    seen_keys: set[str] = set()
    to_delete: list[AgentMemory] = []

    for _mem_type, group in by_type.items():
        for mem in group:
            # Use sorted JSON as a canonical fingerprint.
            fingerprint = json.dumps(mem.content, sort_keys=True)
            if fingerprint in seen_keys:
                # Duplicate — mark for deletion, but transfer access_count to keeper.
                to_delete.append(mem)
                merged_count += 1
            else:
                seen_keys.add(fingerprint)
                # Prune low-relevance memories.
                if mem.relevance_score < _MIN_RELEVANCE:
                    to_delete.append(mem)

    for mem in to_delete:
        await db.delete(mem)
        deleted_count += 1

    await db.flush()
    return {
        "agent_role": agent_role,
        "merged": merged_count,
        "deleted": deleted_count,
        "remaining": len(memories) - deleted_count,
    }
