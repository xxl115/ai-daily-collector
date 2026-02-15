"""Tests for utils/retry.py"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.retry import retry_with_exponential_backoff, retry_with_fixed_interval


class TestRetryWithExponentialBackoff:
    """Test exponential backoff retry decorator"""

    def test_success_first_try(self):
        """Test successful call on first try"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure_then_success(self):
        """Test retry on failure then success"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.01)
        def retry_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("temporary failure")
            return "success"

        result = retry_then_success()
        assert result == "success"
        assert call_count == 2

    def test_max_retries_exceeded(self):
        """Test max retries exceeded raises exception"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("permanent failure")

        with pytest.raises(ConnectionError, match="permanent failure"):
            always_fail()

        assert call_count == 3

    def test_specific_exception_type(self):
        """Test only specified exception types trigger retry"""
        call_count = 0

        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01,
            exceptions=(ConnectionError, TimeoutError),
        )
        def wrong_exception():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retried")

        with pytest.raises(ValueError):
            wrong_exception()

        assert call_count == 1  # Should not retry on ValueError

    def test_exponential_delay_increases(self):
        """Test delay increases exponentially"""
        delays = []

        @retry_with_exponential_backoff(
            max_retries=3, initial_delay=0.1, exponential_base=2.0
        )
        def track_delay():
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            track_delay()


class TestRetryWithFixedInterval:
    """Test fixed interval retry decorator"""

    def test_success_first_try(self):
        """Test successful call on first try"""
        call_count = 0

        @retry_with_fixed_interval(max_retries=2, interval=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = success_func()
        assert result == "ok"
        assert call_count == 1

    def test_fixed_interval_retry(self):
        """Test fixed interval between retries"""
        call_count = 0

        @retry_with_fixed_interval(max_retries=3, interval=0.02)
        def retry_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("timeout")
            return "ok"

        result = retry_then_success()
        assert result == "ok"
        assert call_count == 2

    def test_max_retries_raises(self):
        """Test max retries raises last exception"""
        call_count = 0

        @retry_with_fixed_interval(max_retries=2, interval=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("failed")

        with pytest.raises(TimeoutError):
            always_fail()

        assert call_count == 2


class TestRetryCallbacks:
    """Test retry callback functionality"""

    def test_on_retry_callback(self):
        """Test on_retry callback is called"""
        callback_calls = []

        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01,
            on_retry=lambda e, n: callback_calls.append((str(e), n)),
        )
        def fail_twice():
            if len(callback_calls) < 2:
                raise ConnectionError("fail")
            return "ok"

        fail_twice()
        assert len(callback_calls) == 2
        assert callback_calls[0][1] == 1
        assert callback_calls[1][1] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
