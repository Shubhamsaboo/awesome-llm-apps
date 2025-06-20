FROM python:3.12-slim-bookworm AS builder

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies into the system Python
RUN uv pip install --system -e .

# Final image - ultra slim
FROM python:3.12-slim-bookworm

# Install runtime dependencies, Node.js, PNPM, PostgreSQL client libraries, and FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl \
    libpq-dev postgresql-client ffmpeg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g pnpm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    npm cache clean --force && \
    pip install --no-cache-dir psycopg2-binary gunicorn

# Copy Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application code (only what's needed)
WORKDIR /app
COPY app/ app/
COPY agents/ agents/
COPY config/ config/
COPY models/ models/
COPY routers/ routers/
COPY services/ services/
COPY api.py server.py ./

# Create log directory with appropriate permissions
RUN mkdir -p logs && chmod 777 logs

EXPOSE 8001

# Use gunicorn with uvicorn workers
CMD ["gunicorn", "server:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001", "--timeout", "0", "--keep-alive", "5"]