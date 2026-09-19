# Task: Sliding Window Rate Limiter

## Objective
Implement `SlidingWindowRateLimiter` in `problem.py` satisfying all test requirements in `test_rate_limiter.py`.

## Key Challenges & Common LLM Pitfalls
1. **Window Boundary Burst**: A common mistake is using fixed-interval buckets (`int(timestamp) // window`). When bursts occur across boundary edges (e.g. t=0.9 and t=1.1), fixed buckets permit twice the permitted limit.
2. **Timestamp Pruning**: Timestamps older than `current_time - window_seconds` must be pruned before computing available capacity.
3. **Capacity Invariant**: Failed requests (`allow_request(...) == False`) must NOT record timestamps into the window log.
