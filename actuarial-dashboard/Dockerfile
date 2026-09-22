# ──────────────────────────────────────────────────────────────
# Stage 1: Dependencies
# ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

# ──────────────────────────────────────────────────────────────
# Stage 2: Build
# ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Backend URL untuk rewrites (Docker service name)
ENV BACKEND_URL=http://actuarial-engine:8000

RUN npm run build

# ──────────────────────────────────────────────────────────────
# Stage 3: Runtime – minimal production image
# ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

WORKDIR /app

# Non-root user untuk keamanan
RUN addgroup --system dashboard && adduser --system --ingroup dashboard dashuser

# Copy standalone output dari Next.js
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

USER dashuser

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
