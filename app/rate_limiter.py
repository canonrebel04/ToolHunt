import time
from collections import defaultdict

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self, max_requests=30, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        # Prune old entries for this IP
        self._requests[ip] = [t for t in self._requests[ip] if t > window_start]
        if len(self._requests[ip]) >= self.max_requests:
            return False
        self._requests[ip].append(now)
        return True

    def cleanup(self):
        """Periodic cleanup to prevent memory leaks."""
        now = time.time()
        window_start = now - self.window_seconds
        for ip in list(self._requests.keys()):
            self._requests[ip] = [t for t in self._requests[ip] if t > window_start]
            if not self._requests[ip]:
                del self._requests[ip]

rate_limiter = RateLimiter()
