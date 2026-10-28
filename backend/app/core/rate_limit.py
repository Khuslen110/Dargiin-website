import threading
import time
from collections import deque

from app.core.config import settings


class SlidingWindowRateLimiter:
    """Нэг процессын хүрээнд ажиллах энгийн rate limiter.

    Олон instance-тай production орчинд Redis гэх мэт shared store руу
    шилжүүлэх шаардлагатай (docs/SECURITY.md).
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str) -> tuple[bool, int]:
        """True/False (зөвшөөрөх эсэх) болон retry-after секундыг буцаана."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] < cutoff:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = max(1, int(events[0] + self.window_seconds - now) + 1)
                return False, retry_after
            events.append(now)
            if len(self._events) > 10_000:
                self._drop_stale(cutoff)
            return True, 0

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def _drop_stale(self, cutoff: float) -> None:
        stale = [key for key, events in self._events.items() if not events or events[-1] < cutoff]
        for key in stale:
            self._events.pop(key, None)


login_limiter = SlidingWindowRateLimiter(
    limit=settings.login_rate_limit,
    window_seconds=settings.login_rate_window_seconds,
)
