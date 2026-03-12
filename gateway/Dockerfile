# =============================================================================
# Gateway Dockerfile — multi-stage build
# Stage 1: builder  — compile TypeScript
# Stage 2: runner   — production image (no devDeps)
# Build context: repo root  →  docker build -f gateway/Dockerfile .
# =============================================================================

FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer cache)
COPY gateway/package.json gateway/yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy source and compile
COPY gateway/tsconfig*.json gateway/nest-cli.json ./
COPY gateway/src/ ./src/

RUN yarn build

# -----------------------------------------------------------------------------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Non-root user for security
RUN addgroup --system --gid 1001 nestjs && \
    adduser --system --uid 1001 nestjs

# Only production deps
COPY gateway/package.json gateway/yarn.lock ./
RUN yarn install --frozen-lockfile --production && yarn cache clean

COPY --from=builder /app/dist ./dist

# Proto files needed at runtime by @grpc/proto-loader
COPY protos/ ./protos/

USER nestjs

EXPOSE 5301

CMD ["node", "dist/main"]
