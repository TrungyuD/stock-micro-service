# =============================================================================
# Informer gRPC service — multi-stage build
# Stage 1: builder  — install deps + generate v1 proto stubs
# Stage 2: runner   — slim production image
# Build context: repo root  →  docker build -f services/informer/Dockerfile .
# =============================================================================

FROM python:3.11-slim AS builder

WORKDIR /build

# Install dependencies into a virtual env for clean copy
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY services/informer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Generate v1 proto stubs (common, health, informer/v1)
COPY protos/ ./protos/
RUN mkdir -p ./generated/common \
             ./generated/informer/v1 \
             ./generated/analyzer/v1 && \
    python -m grpc_tools.protoc -I./protos \
        --python_out=./generated --grpc_python_out=./generated \
        ./protos/common/pagination.proto \
        ./protos/common/timestamp.proto \
        ./protos/common/error.proto \
        ./protos/health.proto \
        ./protos/informer/v1/stock.proto \
        ./protos/informer/v1/price.proto \
        ./protos/informer/v1/financial.proto && \
    # Create __init__.py at every package level
    touch ./generated/__init__.py \
          ./generated/common/__init__.py \
          ./generated/informer/__init__.py \
          ./generated/informer/v1/__init__.py \
          ./generated/analyzer/__init__.py \
          ./generated/analyzer/v1/__init__.py && \
    # Fix imports: protoc generates bare imports; rewrite to package-relative
    find ./generated \( -name "*.py" -o -name "*.pyi" \) \
      -exec sed -i \
        -e 's/^from common /from generated.common /g' \
        -e 's/^from informer\.v1 /from generated.informer.v1 /g' \
        -e 's/^from analyzer\.v1 /from generated.analyzer.v1 /g' \
        -e 's/^import health_pb2/from generated import health_pb2/g' \
      {} +

# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy only the virtual env (no pip, no build tools)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy generated proto stubs
COPY --from=builder /build/generated/ ./src/generated/

# Copy service source
COPY services/informer/src/ ./src/

# Non-root user for security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser
USER appuser

EXPOSE 5302

CMD ["python", "src/server.py"]
