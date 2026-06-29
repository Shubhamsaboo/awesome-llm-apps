"""
Prompt Compression Demo — reduce LLM token costs by ~65%

Uses SuperCompress to score and select the most relevant lines
from a long context before sending to any LLM.
"""

import os
from supercompress import compress_context, CompressResult

# ── 1. Set up a long context ──────────────────────────────────────

long_context = """
Project: E-Commerce Platform Migration
Status: In Progress
Last Updated: 2026-06-28

Team Members:
- Alice (Frontend Lead)
- Bob (Backend Lead)
- Carol (DevOps)
- Dave (QA)

Architecture Decisions:
- Using React 19 with Server Components for the frontend
- Python/FastAPI backend with PostgreSQL
- Redis for caching and session management
- Docker/Kubernetes for deployment
- GitHub Actions for CI/CD

Current Sprint (Sprint 12):
- FR-401: Checkout flow redesign (Alice, in review)
- FR-402: Payment gateway integration (Bob, blocked on Stripe approval)
- FR-403: Database migration script (Bob, in progress)
- FR-404: Performance testing suite (Dave, completed)
- FR-405: Kubernetes Helm charts (Carol, in progress)

Blockers:
- Stripe approval is taking longer than expected (FR-402)
- PostgreSQL 17 upgrade requires schema changes (FR-403)

Previous Sprint Accomplishments:
- Completed user authentication overhaul
- Migrated from Webpack to Vite
- Set up monitoring with Datadog
- Reduced initial bundle size by 40%%

API Endpoints (v2):
- GET /api/v2/products — list products (paginated)
- GET /api/v2/products/:id — product details
- POST /api/v2/cart — add to cart
- DELETE /api/v2/cart/:item — remove from cart
- POST /api/v2/checkout — initiate checkout
- GET /api/v2/orders — order history
- POST /api/v2/webhooks/stripe — Stripe webhook receiver

Deployment Targets:
- staging: https://staging.example.com
- production: https://example.com
"""

# ── 2. Ask a question ────────────────────────────────────────────

question = "Who is leading the frontend work and what are they working on?"

# ── 3. Compress the context ───────────────────────────────────────

result: CompressResult = compress_context(
    long_context,
    question,
    budget_ratio=0.35,  # keep 35%% of total tokens
)

# ── 4. Print results ─────────────────────────────────────────────

print("=" * 60)
print("PROMPT COMPRESSION DEMO")
print("=" * 60)
print()
print(f"Question: {question}")
print()
print(f"Original tokens:  {result.original_tokens}")
print(f"Kept tokens:      {result.kept_tokens}")
print(f"KV savings:       {result.kv_savings_pct:.1f}%%")
print(f"Compression ratio: {result.compression_ratio:.2f}x")
print()
print("─" * 60)
print("ORIGINAL CONTEXT")
print("─" * 60)
print(result.original_text)
print()
print("─" * 60)
print(f"COMPRESSED CONTEXT ({result.kept_line_ratio*100:.0f}%% of lines kept)")
print("─" * 60)
print(result.compressed_text)
print()
print("─" * 60)
print("Next step: Send compressed context to your LLM instead of the original")
print("─" * 60)
