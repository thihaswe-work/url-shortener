import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._records: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        now = time.time()

        cutoff = now - self.window_seconds
        self._records[key] = [t for t in self._records[key] if t > cutoff]

        if len(self._records[key]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
            )

        self._records[key].append(now)


rate_limit_shorten = RateLimiter(max_requests=30, window_seconds=60)
rate_limit_auth = RateLimiter(max_requests=20, window_seconds=60)
