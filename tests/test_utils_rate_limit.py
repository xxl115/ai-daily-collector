"""Tests for utils/rate_limit.py"""

import pytest
import time
import threading
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rate_limit import (
    RateLimiter,
    SemaphoreLimiter,
    rate_limited,
    concurrent_limited,
)


class TestRateLimiter:
    """Test RateLimiter class"""

    def test_allows_within_limit(self):
        """Test allows calls within rate limit"""
        limiter = RateLimiter(max_calls=5, period=1.0)

        results = [limiter.acquire() for _ in range(5)]
        assert all(results), "Should allow up to max_calls"

    def test_blocks_over_limit(self):
        """Test blocks calls over rate limit"""
        limiter = RateLimiter(max_calls=2, period=1.0)

        assert limiter.acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire() is False

    def test_wait_and_acquire_blocks(self):
        """Test wait_and_acquire blocks until available"""
        limiter = RateLimiter(max_calls=1, period=0.5)

        start = time.time()
        limiter.acquire()  # First call
        limiter.wait_and_acquire()  # Should wait
        elapsed = time.time() - start

        assert elapsed >= 0.4, "Should wait for rate limit window"

    def test_sliding_window(self):
        """Test sliding window clears old entries"""
        limiter = RateLimiter(max_calls=2, period=0.3)

        limiter.acquire()
        limiter.acquire()
        assert limiter.acquire() is False

        time.sleep(0.35)

        assert limiter.acquire() is True, "Old entries should be cleared"


class TestSemaphoreLimiter:
    """Test SemaphoreLimiter class"""

    def test_allows_within_limit(self):
        """Test allows concurrent calls within limit"""
        limiter = SemaphoreLimiter(max_concurrent=2)

        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is False

    def test_context_manager(self):
        """Test context manager acquires and releases"""
        limiter = SemaphoreLimiter(max_concurrent=1)

        with limiter:
            assert limiter.semaphore._value == 0

        assert limiter.semaphore._value == 1

    def test_concurrent_access(self):
        """Test concurrent access is properly limited"""
        limiter = SemaphoreLimiter(max_concurrent=2)
        active_count = 0
        max_seen = 0
        lock = threading.Lock()

        def worker():
            nonlocal active_count, max_seen
            with limiter:
                with lock:
                    active_count += 1
                    max_seen = max(max_seen, active_count)
                time.sleep(0.1)
                with lock:
                    active_count -= 1

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert max_seen <= 2, "Should not exceed concurrent limit"


class TestDecorators:
    """Test rate_limited and concurrent_limited decorators"""

    def test_rate_limited_decorator(self):
        """Test rate_limited decorator"""
        call_times = []

        @rate_limited(max_calls=3, period=1.0)
        def limited_func():
            call_times.append(time.time())
            return "ok"

        for _ in range(3):
            limited_func()

        # 4th call should trigger rate limiting
        with pytest.raises(Exception):
            limited_func()

    def test_concurrent_limited_decorator(self):
        """Test concurrent_limited decorator"""
        active = 0
        max_active = 0
        lock = threading.Lock()

        @concurrent_limited(max_concurrent=2)
        def concurrent_func():
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.05)
            with lock:
                active -= 1
            return "ok"

        threads = [threading.Thread(target=concurrent_func) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert max_active <= 2


class TestRateLimiterEdgeCases:
    """Test edge cases"""

    def test_zero_max_calls(self):
        """Test with zero max calls"""
        limiter = RateLimiter(max_calls=0, period=1.0)
        assert limiter.acquire() is False

    def test_zero_period(self):
        """Test with zero period"""
        limiter = RateLimiter(max_calls=5, period=0.0)
        # Should behave reasonably
        for _ in range(3):
            limiter.acquire()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
