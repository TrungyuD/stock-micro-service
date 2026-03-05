# ─────────────────────────────────────────────────────────────────────────────
# Analytics gRPC service
# Build context: repo root  →  docker build -f services/analytics/Dockerfile .
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (Docker layer caching)
COPY services/analytics/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto definitions and generate stubs at build time
COPY protos/ ./protos/
RUN mkdir -p ./src/generated/common && \
    python -m grpc_tools.protoc \
        -I./protos \
        --python_out=./src/generated \
        --grpc_python_out=./src/generated \
        ./protos/analytics.proto && \
    # Create __init__.py files so generated stubs are importable as packages
    touch ./src/generated/__init__.py && \
    touch ./src/generated/common/__init__.py

# Copy service source (after proto gen so stub layer is cached on src changes)
COPY services/analytics/src/ ./src/

# PYTHONPATH=./src so all imports work without package install
ENV PYTHONPATH=/app/src

# Expose gRPC port (default 50052; overridable via GRPC_PORT env var)
EXPOSE 50052

CMD ["python", "src/server.py"]
