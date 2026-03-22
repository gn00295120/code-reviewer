"""In-memory review queue for desktop mode (replaces Redis-based queue)."""

import threading

MAX_CONCURRENT = 10
_active: set[str] = set()
_lock = threading.Lock()


def enqueue_review(review_id: str) -> bool:
    """Add review to active set. Returns False if at capacity."""
    with _lock:
        if len(_active) >= MAX_CONCURRENT:
            return False
        _active.add(review_id)
        return True


def dequeue_review(review_id: str):
    """Remove review from active set (on completion or failure)."""
    with _lock:
        _active.discard(review_id)


def active_count() -> int:
    """Get number of currently running reviews."""
    return len(_active)


def active_reviews() -> set[str]:
    """Get set of active review IDs."""
    return set(_active)
