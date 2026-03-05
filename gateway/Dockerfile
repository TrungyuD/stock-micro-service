# =============================================================================
# Gateway Dockerfile — multi-stage build
# Stage 1: builder  — compile TypeScript
# Stage 2: runner   — production image (no devDeps)
# =============================================================================

FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer cache)
COPY package*.json ./
RUN npm ci

# Copy source and compile
COPY tsconfig*.json nest-cli.json ./
COPY src/ ./src/
RUN npm run build

# -----------------------------------------------------------------------------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Only production deps
COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/dist ./dist

EXPOSE 3001

CMD ["node", "dist/main"]
