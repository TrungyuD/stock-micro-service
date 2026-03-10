#!/usr/bin/env bash
# generate.sh — Regenerate protobuf stubs for all Python services from the
# single proto source of truth in /protos/.
# Usage: ./protos/scripts/generate.sh   (or `make proto` from repo root)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PROTO_DIR/.." && pwd)"

INFORMER_OUT="$REPO_ROOT/services/informer/src/generated"
ANALYTICS_OUT="$REPO_ROOT/services/analytics/src/generated"

# Detect python command: prefer informer venv (has grpc_tools installed),
# fall back to PYTHON env var or system python3.
INFORMER_VENV="$REPO_ROOT/services/informer/.venv/bin/python3"
if [ -x "$INFORMER_VENV" ]; then
    PYTHON="$INFORMER_VENV"
else
    PYTHON="${PYTHON:-python3}"
fi

echo "Proto source: $PROTO_DIR"
echo "Informer out: $INFORMER_OUT"
echo "Analytics out: $ANALYTICS_OUT"

# Clean old generated files (keep __init__.py)
for OUT_DIR in "$INFORMER_OUT" "$ANALYTICS_OUT"; do
    find "$OUT_DIR" -name '*_pb2.py' -o -name '*_pb2_grpc.py' | xargs rm -f 2>/dev/null || true
done

# Ensure output dirs exist
mkdir -p "$INFORMER_OUT/common"
mkdir -p "$ANALYTICS_OUT/common"

# Ensure __init__.py exists for Python package resolution
touch "$INFORMER_OUT/__init__.py"
touch "$INFORMER_OUT/common/__init__.py"
touch "$ANALYTICS_OUT/__init__.py"
touch "$ANALYTICS_OUT/common/__init__.py"

echo ""
echo "=== Generating Informer stubs ==="
$PYTHON -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$INFORMER_OUT" \
    --grpc_python_out="$INFORMER_OUT" \
    common/types.proto common/health.proto informer.proto

echo "=== Generating Analytics stubs ==="
$PYTHON -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$ANALYTICS_OUT" \
    --grpc_python_out="$ANALYTICS_OUT" \
    common/types.proto common/health.proto analytics.proto

echo ""
echo "Done. Stubs generated for both services."
