"""
🧠 Entroly Context Optimization Demo
=====================================
Interactive Streamlit app showing how Entroly compresses LLM context
by 70-95% while preserving accuracy — zero API keys required.

Run: streamlit run entroly_demo.py
"""

import time
import streamlit as st
from entroly import compress, compress_messages

# ── Sample Data ──────────────────────────────────────────────────────────

SAMPLE_CODE = '''
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    host: str = "localhost"
    port: int = 5432
    database: str = "myapp"
    username: str = "admin"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False

    def connection_string(self) -> str:
        """Generate a SQLAlchemy connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def validate(self) -> List[str]:
        """Validate the configuration and return any errors."""
        errors = []
        if not self.host:
            errors.append("Database host is required")
        if self.port < 1 or self.port > 65535:
            errors.append(f"Invalid port: {self.port}")
        if not self.database:
            errors.append("Database name is required")
        if self.pool_size < 1:
            errors.append("Pool size must be at least 1")
        if self.max_overflow < 0:
            errors.append("Max overflow cannot be negative")
        return errors


@dataclass
class CacheConfig:
    """Configuration for caching layer."""
    backend: str = "redis"
    host: str = "localhost"
    port: int = 6379
    ttl: int = 3600
    max_connections: int = 50
    key_prefix: str = "myapp:"
    serializer: str = "json"

    def validate(self) -> List[str]:
        errors = []
        if self.backend not in ("redis", "memcached", "local"):
            errors.append(f"Unknown cache backend: {self.backend}")
        if self.ttl < 0:
            errors.append("TTL cannot be negative")
        return errors


@dataclass
class AppConfig:
    """Main application configuration."""
    app_name: str = "MyApp"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = ""
    allowed_hosts: List[str] = field(default_factory=lambda: ["*"])
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        config = cls()
        config.app_name = os.getenv("APP_NAME", config.app_name)
        config.debug = os.getenv("DEBUG", "false").lower() == "true"
        config.log_level = os.getenv("LOG_LEVEL", config.log_level)
        config.secret_key = os.getenv("SECRET_KEY", config.secret_key)
        config.database.host = os.getenv("DB_HOST", config.database.host)
        config.database.port = int(os.getenv("DB_PORT", str(config.database.port)))
        config.database.database = os.getenv("DB_NAME", config.database.database)
        config.database.username = os.getenv("DB_USER", config.database.username)
        config.database.password = os.getenv("DB_PASS", config.database.password)
        config.cache.host = os.getenv("CACHE_HOST", config.cache.host)
        config.cache.port = int(os.getenv("CACHE_PORT", str(config.cache.port)))
        return config

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        """Load configuration from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        config = cls()
        for key, value in data.items():
            if key == "database":
                config.database = DatabaseConfig(**value)
            elif key == "cache":
                config.cache = CacheConfig(**value)
            elif hasattr(config, key):
                setattr(config, key, value)
        return config

    def validate(self) -> List[str]:
        """Validate the entire configuration."""
        errors = []
        if not self.secret_key and not self.debug:
            errors.append("SECRET_KEY is required in production")
        errors.extend(self.database.validate())
        errors.extend(self.cache.validate())
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a dictionary."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "log_level": self.log_level,
            "allowed_hosts": self.allowed_hosts,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "pool_size": self.database.pool_size,
            },
            "cache": {
                "backend": self.cache.backend,
                "host": self.cache.host,
                "port": self.cache.port,
                "ttl": self.cache.ttl,
            },
        }
'''.strip()

SAMPLE_LOG = """2026-05-10 08:00:01 INFO  [main] Application starting up...
2026-05-10 08:00:01 INFO  [main] Loading configuration from /etc/myapp/config.json
2026-05-10 08:00:02 INFO  [db] Connecting to database at localhost:5432
2026-05-10 08:00:02 INFO  [db] Connection pool initialized (size=10)
2026-05-10 08:00:02 INFO  [cache] Connecting to Redis at localhost:6379
2026-05-10 08:00:03 INFO  [cache] Redis connection established
2026-05-10 08:00:03 INFO  [http] Starting HTTP server on 0.0.0.0:8080
2026-05-10 08:00:03 INFO  [http] Server ready to accept connections
2026-05-10 08:01:15 INFO  [http] GET /api/users 200 45ms
2026-05-10 08:01:16 INFO  [http] GET /api/users 200 12ms (cache hit)
2026-05-10 08:01:17 INFO  [http] GET /api/users 200 11ms (cache hit)
2026-05-10 08:01:18 INFO  [http] GET /api/users 200 13ms (cache hit)
2026-05-10 08:01:20 INFO  [http] POST /api/users 201 89ms
2026-05-10 08:01:21 INFO  [cache] Cache invalidated: myapp:users:*
2026-05-10 08:01:25 INFO  [http] GET /api/users 200 42ms
2026-05-10 08:01:30 INFO  [http] GET /api/products 200 67ms
2026-05-10 08:01:31 INFO  [http] GET /api/products 200 9ms (cache hit)
2026-05-10 08:01:32 INFO  [http] GET /api/products 200 10ms (cache hit)
2026-05-10 08:01:33 INFO  [http] GET /api/products 200 11ms (cache hit)
2026-05-10 08:02:00 WARN  [db] Slow query detected: SELECT * FROM orders WHERE... (1523ms)
2026-05-10 08:02:01 INFO  [http] GET /api/orders 200 1534ms
2026-05-10 08:02:15 ERROR [payment] Payment processing failed for order #4521
2026-05-10 08:02:15 ERROR [payment] Traceback: ConnectionRefusedError: payment-gateway:443
2026-05-10 08:02:16 INFO  [payment] Retrying payment for order #4521 (attempt 2/3)
2026-05-10 08:02:17 INFO  [payment] Payment successful for order #4521 on retry
2026-05-10 08:02:30 INFO  [http] GET /api/products 200 8ms (cache hit)
2026-05-10 08:02:31 INFO  [http] GET /api/products 200 9ms (cache hit)
2026-05-10 08:02:32 INFO  [http] GET /api/products 200 10ms (cache hit)
2026-05-10 08:03:00 INFO  [health] Health check OK: db=up cache=up payment=up
2026-05-10 08:03:00 INFO  [health] Health check OK: db=up cache=up payment=up
2026-05-10 08:03:00 INFO  [health] Health check OK: db=up cache=up payment=up"""

SAMPLE_JSON = """{
  "users": [
    {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin", "created": "2026-01-15", "last_login": "2026-05-09", "preferences": {"theme": "dark", "language": "en", "notifications": true}},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user", "created": "2026-02-20", "last_login": "2026-05-08", "preferences": {"theme": "light", "language": "en", "notifications": false}},
    {"id": 3, "name": "Carol Davis", "email": "carol@example.com", "role": "user", "created": "2026-03-10", "last_login": "2026-05-10", "preferences": {"theme": "dark", "language": "fr", "notifications": true}},
    {"id": 4, "name": "Dan Wilson", "email": "dan@example.com", "role": "moderator", "created": "2026-03-15", "last_login": "2026-05-07", "preferences": {"theme": "system", "language": "en", "notifications": true}},
    {"id": 5, "name": "Eve Brown", "email": "eve@example.com", "role": "user", "created": "2026-04-01", "last_login": "2026-05-10", "preferences": {"theme": "dark", "language": "de", "notifications": false}}
  ],
  "metadata": {"total": 5, "page": 1, "per_page": 20, "total_pages": 1},
  "permissions": {"admin": ["read", "write", "delete", "manage_users"], "moderator": ["read", "write", "delete"], "user": ["read", "write"]}
}"""

SAMPLE_CONVERSATION = [
    {"role": "system", "content": "You are a senior software engineer helping debug a production issue. You have access to logs, code, and monitoring data. Be thorough but concise."},
    {"role": "user", "content": "Our payment service is failing intermittently. Can you look at the logs?"},
    {"role": "assistant", "content": f"I've analyzed the logs. Here's what I found:\n\n{SAMPLE_LOG}\n\nKey findings:\n1. Payment gateway connection refused at 08:02:15\n2. Retry succeeded on attempt 2\n3. Slow query on orders table (1523ms)\n4. Cache is working well for reads"},
    {"role": "user", "content": "What's the root cause and how do we fix it?"},
]

# ── Streamlit App ────────────────────────────────────────────────────────

st.set_page_config(page_title="Entroly Context Optimizer", page_icon="🧠", layout="wide")

st.title("🧠 Entroly — Context Compression Demo")
st.markdown(
    "Compress LLM context by **70–95%** while preserving accuracy. "
    "No API keys needed — everything runs locally in <10ms."
)

tab1, tab2, tab3 = st.tabs(["📄 Single Content", "💬 Conversation", "📊 Benchmark"])

# ── Tab 1: Single content compression ───────────────────────────────────

with tab1:
    st.subheader("Compress any content type")
    content_type = st.selectbox("Sample content", ["Python Code", "Server Logs", "JSON API Response", "Custom"])

    if content_type == "Python Code":
        input_text = st.text_area("Input", SAMPLE_CODE, height=300)
    elif content_type == "Server Logs":
        input_text = st.text_area("Input", SAMPLE_LOG, height=300)
    elif content_type == "JSON API Response":
        input_text = st.text_area("Input", SAMPLE_JSON, height=300)
    else:
        input_text = st.text_area("Input (paste anything)", "", height=300)

    budget = st.slider("Token budget", 100, 5000, 500, step=50)

    if st.button("🚀 Compress", type="primary") and input_text:
        start = time.perf_counter()
        result = compress(input_text, budget=budget)
        elapsed_ms = (time.perf_counter() - start) * 1000

        orig_tokens = len(input_text) // 4
        comp_tokens = len(result) // 4
        savings = max(0, (1 - comp_tokens / max(orig_tokens, 1))) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Original tokens", f"{orig_tokens:,}")
        c2.metric("Compressed tokens", f"{comp_tokens:,}")
        c3.metric("Savings", f"{savings:.1f}%")
        c4.metric("Latency", f"{elapsed_ms:.1f}ms")

        st.text_area("Compressed output", result, height=300)

# ── Tab 2: Conversation compression ─────────────────────────────────────

with tab2:
    st.subheader("Compress a full LLM conversation")
    st.markdown("Simulates a 4-message debugging session with logs embedded in assistant responses.")

    conv_budget = st.slider("Conversation token budget", 500, 10000, 2000, step=100)

    if st.button("🚀 Compress Conversation", type="primary"):
        orig_tokens = sum(len(m.get("content", "")) // 4 for m in SAMPLE_CONVERSATION)

        start = time.perf_counter()
        compressed_msgs = compress_messages(SAMPLE_CONVERSATION, budget=conv_budget)
        elapsed_ms = (time.perf_counter() - start) * 1000

        comp_tokens = sum(len(m.get("content", "")) // 4 for m in compressed_msgs)
        savings = max(0, (1 - comp_tokens / max(orig_tokens, 1))) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Original tokens", f"{orig_tokens:,}")
        c2.metric("After compression", f"{comp_tokens:,}")
        c3.metric("Savings", f"{savings:.1f}%")
        c4.metric("Latency", f"{elapsed_ms:.1f}ms")

        for msg in compressed_msgs:
            role = msg["role"]
            icon = {"system": "⚙️", "user": "👤", "assistant": "🤖"}.get(role, "💬")
            with st.expander(f"{icon} {role}", expanded=(role == "assistant")):
                st.text(msg.get("content", "")[:2000])

# ── Tab 3: Benchmark ────────────────────────────────────────────────────

with tab3:
    st.subheader("Quick benchmark — compress at multiple budgets")

    if st.button("▶️ Run Benchmark", type="primary"):
        budgets = [100, 250, 500, 1000, 2000, 5000]
        rows = []
        for b in budgets:
            start = time.perf_counter()
            result = compress(SAMPLE_CODE, budget=b)
            elapsed = (time.perf_counter() - start) * 1000
            orig = len(SAMPLE_CODE) // 4
            comp = len(result) // 4
            savings = max(0, (1 - comp / max(orig, 1))) * 100
            rows.append({"Budget": b, "Output tokens": comp, "Savings %": f"{savings:.1f}", "Latency (ms)": f"{elapsed:.1f}"})
        st.table(rows)

    st.markdown("---")
    st.markdown(
        "**How it works:** Entroly uses information-theoretic selection — TF-IDF extractive summarization "
        "with greedy submodular maximization (Nemhauser-Wolsey-Fisher 1978). No neural networks, no GPU, "
        "no API calls. Deterministic and runs in <10ms.\n\n"
        "📦 [GitHub](https://github.com/juyterman1000/entroly) · "
        "📄 [PyPI](https://pypi.org/project/entroly/) · "
        "📜 Apache 2.0 License"
    )
