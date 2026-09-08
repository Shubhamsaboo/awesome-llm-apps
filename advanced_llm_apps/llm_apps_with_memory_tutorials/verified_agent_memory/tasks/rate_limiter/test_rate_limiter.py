"""Unit tests for SlidingWindowRateLimiter."""

import pytest
from problem import SlidingWindowRateLimiter


def test_initialization_validation():
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(max_requests=0, window_seconds=10.0)
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(max_requests=5, window_seconds=0)


def test_basic_capacity():
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10.0)
    t0 = 100.0

    assert limiter.allow_request("user1", current_time=t0) is True
    assert limiter.allow_request("user1", current_time=t0 + 1.0) is True
    assert limiter.allow_request("user1", current_time=t0 + 2.0) is True
    assert limiter.allow_request("user1", current_time=t0 + 3.0) is False

    assert limiter.get_remaining_requests("user1", current_time=t0 + 3.0) == 0


def test_sliding_window_boundary_behavior():
    """Fixed-window algorithms fail here:

    If window=1.0s and max=5, sending 5 requests at t=0.9 and 5 requests at t=1.1
    must trigger rejection for the t=1.1 burst, because within [0.1, 1.1] there are
    already 5 requests!
    """
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0)

    # 5 requests sent at t = 0.9
    for _ in range(5):
        assert limiter.allow_request("api_client", current_time=0.9) is True

    # At t = 1.1, the previous 5 requests (at 0.9) are still within the 1.0s sliding window (1.1 - 1.0 = 0.1 <= 0.9)
    # A naive fixed-window bucket (0.0 - 1.0 vs 1.0 - 2.0) would allow them; a true sliding window must reject!
    assert limiter.allow_request("api_client", current_time=1.1) is False
    assert limiter.get_remaining_requests("api_client", current_time=1.1) == 0

    # At t = 1.95, the 0.9 requests are older than 1.0s window (1.95 - 1.0 = 0.95 > 0.9)
    # They should now be pruned, freeing up quota!
    assert limiter.allow_request("api_client", current_time=1.95) is True
    assert limiter.get_remaining_requests("api_client", current_time=1.95) == 4


def test_multi_key_isolation():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=5.0)
    t = 50.0

    # Fill quota for user_a
    assert limiter.allow_request("user_a", current_time=t) is True
    assert limiter.allow_request("user_a", current_time=t) is True
    assert limiter.allow_request("user_a", current_time=t) is False

    # user_b should remain unaffected
    assert limiter.allow_request("user_b", current_time=t) is True
    assert limiter.allow_request("user_b", current_time=t) is True
    assert limiter.allow_request("user_b", current_time=t) is False


def test_reset():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=10.0)
    t = 10.0

    limiter.allow_request("user_1", current_time=t)
    limiter.allow_request("user_1", current_time=t)
    assert limiter.allow_request("user_1", current_time=t) is False

    # Reset single key
    limiter.reset("user_1")
    assert limiter.allow_request("user_1", current_time=t) is True

    # Reset all keys
    limiter.allow_request("user_2", current_time=t)
    limiter.reset()
    assert limiter.get_remaining_requests("user_1", current_time=t) == 2
    assert limiter.get_remaining_requests("user_2", current_time=t) == 2
