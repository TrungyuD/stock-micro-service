# =============================================================================
# Informer gRPC service — multi-stage build
# Stage 1: builder  — install deps + generate proto stubs
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

# Generate proto stubs
COPY protos/ ./protos/
RUN mkdir -p ./generated/common && \
    python -m grpc_tools.protoc \
        -I./protos \
        --python_out=./generated \
        --grpc_python_out=./generated \
        ./protos/informer.proto \
        ./protos/common/types.proto && \
    touch ./generated/__init__.py && \
    touch ./generated/common/__init__.py

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

EXPOSE 50051

CMD ["python", "src/server.py"]
