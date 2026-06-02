# ── Stage 1: Install + Build ──────────────────────────────────────────────────
FROM node:22-alpine AS builder

RUN corepack enable && corepack prepare pnpm@10.13.1 --activate

WORKDIR /app

# Copy workspace root manifests first (cache layer)
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml turbo.json ./
COPY .env.example .env.example
COPY apps/web/package.json apps/web/package.json
COPY apps/mcp-use-server/package.json apps/mcp-use-server/package.json
COPY apps/threejs-server/package.json apps/threejs-server/package.json

RUN pnpm install --frozen-lockfile

# Copy full source
COPY . .

# Build the web app (turbo runs prebuild → next build with standalone output)
RUN pnpm turbo run build --filter=web

# ── Stage 2: Production runner ────────────────────────────────────────────────
FROM node:22-alpine AS runner

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

WORKDIR /app

# Copy Next.js standalone output
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static

# Copy the download-kit artifact (used by /api/workspace/download)
COPY --from=builder /app/apps/web/.download-kit ./apps/web/.download-kit

USER nextjs

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["node", "apps/web/server.js"]
