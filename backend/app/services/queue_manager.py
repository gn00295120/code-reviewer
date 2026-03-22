"""Review queue management — max 10 concurrent reviews."""

from app.core.config import get_settings

settings = get_settings()

if settings.desktop_mode:
    # Desktop mode: use in-memory queue backed by threading primitives
    from app.services.in_memory_queue import (
        enqueue_review,
        dequeue_review,
        active_count,
        active_reviews,
    )
else:
    import redis

    QUEUE_KEY = "swarmforge:active_reviews"
    MAX_CONCURRENT = 10

    def get_redis():
        return redis.from_url(settings.redis_url, decode_responses=True)

    def can_enqueue() -> bool:
        """Check if there's capacity for another review."""
        r = get_redis()
        return r.scard(QUEUE_KEY) < MAX_CONCURRENT

    def enqueue_review(review_id: str) -> bool:
        """Add review to active set. Returns False if at capacity."""
        r = get_redis()
        if r.scard(QUEUE_KEY) >= MAX_CONCURRENT:
            return False
        r.sadd(QUEUE_KEY, review_id)
        # Auto-expire after 15 min (safety net for stuck reviews)
        r.expire(QUEUE_KEY, 900)
        return True

    def dequeue_review(review_id: str):
        """Remove review from active set (on completion or failure)."""
        r = get_redis()
        r.srem(QUEUE_KEY, review_id)

    def active_count() -> int:
        """Get number of currently running reviews."""
        r = get_redis()
        return r.scard(QUEUE_KEY)

    def active_reviews() -> set[str]:
        """Get set of active review IDs."""
        r = get_redis()
        return r.smembers(QUEUE_KEY)
