# ── Stage 1: install deps ─────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /build

COPY package.json package-lock.json ./

RUN npm ci --omit=dev


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

RUN addgroup -S app && adduser -S -G app app

WORKDIR /app

# copy only production node_modules from builder
COPY --from=builder /build/node_modules ./node_modules

# copy application source (no .env, no secrets)
COPY app.js .
COPY views ./views

USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "app.js"]
