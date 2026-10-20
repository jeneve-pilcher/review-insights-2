"""A small per-key limit on how many times something can be done in an hour (kept in memory, so it resets
when the backend restarts and is counted per backend process)."""
import os
import threading
import time
from collections import defaultdict, deque

_hits = defaultdict(deque)
_lock = threading.Lock()


def analyze_limit() -> int:
    try:
        return max(1, int(os.environ.get("ANALYZE_PER_HOUR", "5")))
    except ValueError:
        return 5


def take(key: str, limit: int, now=None):
    """Counts one use. Returns (True, 0) if allowed, or (False, seconds_until_the_next_one_is_free)."""
    now = now if now is not None else time.time()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - 3600:
            q.popleft()
        if len(q) >= limit:
            return False, int(q[0] + 3600 - now) + 1
        q.append(now)
        return True, 0
