#!/bin/bash
# generate-proto-python.sh — Generate Python gRPC stubs from proto definitions.
# Run from stock-micro-service/ directory:
#   bash scripts/generate-proto-python.sh
#
# Requires grpcio-tools installed in each service's virtualenv.
# Activate one of the service venvs before running:
#   source services/informer/.venv/bin/activate

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PROTO_DIR="$ROOT_DIR/protos"
INFORMER_OUT="$ROOT_DIR/services/informer/src/generated"
ANALYTICS_OUT="$ROOT_DIR/services/analytics/src/generated"

echo "=== Generating Python gRPC stubs ==="
echo "Proto dir    : $PROTO_DIR"
echo "Informer out : $INFORMER_OUT"
echo "Analytics out: $ANALYTICS_OUT"
echo ""

# Clean and recreate output dirs
rm -rf "$INFORMER_OUT" "$ANALYTICS_OUT"
mkdir -p "$INFORMER_OUT" "$ANALYTICS_OUT"

# ---------------------------------------------------------------------------
# Helper: create __init__.py files at every package level for a given base dir
# ---------------------------------------------------------------------------
init_packages() {
  local base="$1"
  touch "$base/__init__.py"
  touch "$base/common/__init__.py"
  mkdir -p "$base/informer/v1" && touch "$base/informer/__init__.py" "$base/informer/v1/__init__.py"
  mkdir -p "$base/analyzer/v1" && touch "$base/analyzer/__init__.py" "$base/analyzer/v1/__init__.py"
}

# ---------------------------------------------------------------------------
# Legacy stubs — keep until Phase 3+4+5 migration completes
# ---------------------------------------------------------------------------
echo "→ Generating legacy Informer stubs..."
python3 -m grpc_tools.protoc -I"$PROTO_DIR" \
  --python_out="$INFORMER_OUT" --grpc_python_out="$INFORMER_OUT" --pyi_out="$INFORMER_OUT" \
  "$PROTO_DIR/common/types.proto" "$PROTO_DIR/common/health.proto" "$PROTO_DIR/informer.proto"

echo "→ Generating legacy Analytics stubs..."
python3 -m grpc_tools.protoc -I"$PROTO_DIR" \
  --python_out="$ANALYTICS_OUT" --grpc_python_out="$ANALYTICS_OUT" --pyi_out="$ANALYTICS_OUT" \
  "$PROTO_DIR/common/types.proto" "$PROTO_DIR/common/health.proto" "$PROTO_DIR/analytics.proto"

# ---------------------------------------------------------------------------
# New versioned stubs — common, health, informer/v1
# ---------------------------------------------------------------------------
echo "→ Generating new Informer v1 stubs..."
python3 -m grpc_tools.protoc -I"$PROTO_DIR" \
  --python_out="$INFORMER_OUT" --grpc_python_out="$INFORMER_OUT" --pyi_out="$INFORMER_OUT" \
  "$PROTO_DIR/common/pagination.proto" \
  "$PROTO_DIR/common/timestamp.proto" \
  "$PROTO_DIR/common/error.proto" \
  "$PROTO_DIR/health.proto" \
  "$PROTO_DIR/informer/v1/stock.proto" \
  "$PROTO_DIR/informer/v1/price.proto" \
  "$PROTO_DIR/informer/v1/financial.proto"

# New versioned stubs — common, health, analyzer/v1
echo "→ Generating new Analytics v1 stubs..."
python3 -m grpc_tools.protoc -I"$PROTO_DIR" \
  --python_out="$ANALYTICS_OUT" --grpc_python_out="$ANALYTICS_OUT" --pyi_out="$ANALYTICS_OUT" \
  "$PROTO_DIR/common/pagination.proto" \
  "$PROTO_DIR/common/timestamp.proto" \
  "$PROTO_DIR/common/error.proto" \
  "$PROTO_DIR/health.proto" \
  "$PROTO_DIR/analyzer/v1/technical.proto" \
  "$PROTO_DIR/analyzer/v1/fundamental.proto" \
  "$PROTO_DIR/analyzer/v1/screening.proto" \
  "$PROTO_DIR/analyzer/v1/scoring.proto"

# ---------------------------------------------------------------------------
# Ensure __init__.py at every package level
# ---------------------------------------------------------------------------
init_packages "$INFORMER_OUT"
init_packages "$ANALYTICS_OUT"

# ---------------------------------------------------------------------------
# Fix imports: protoc generates bare imports; rewrite to be package-relative.
# Patterns:
#   from common import ...       → from generated.common import ...
#   from informer.v1 import ...  → from generated.informer.v1 import ...
#   from analyzer.v1 import ...  → from generated.analyzer.v1 import ...
#   ^import health_pb2           → from generated import health_pb2
# ---------------------------------------------------------------------------
echo "→ Fixing imports in generated files..."
fix_imports() {
  local dir="$1"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    find "$dir" \( -name "*.py" -o -name "*.pyi" \) \
      -exec sed -i '' \
        -e 's/^from common /from generated.common /g' \
        -e 's/^from informer\.v1 /from generated.informer.v1 /g' \
        -e 's/^from analyzer\.v1 /from generated.analyzer.v1 /g' \
        -e 's/^import health_pb2/from generated import health_pb2/g' \
        -e 's/^import informer_pb2/from generated import informer_pb2/g' \
        -e 's/^import analytics_pb2/from generated import analytics_pb2/g' \
      {} +
  else
    find "$dir" \( -name "*.py" -o -name "*.pyi" \) \
      -exec sed -i \
        -e 's/^from common /from generated.common /g' \
        -e 's/^from informer\.v1 /from generated.informer.v1 /g' \
        -e 's/^from analyzer\.v1 /from generated.analyzer.v1 /g' \
        -e 's/^import health_pb2/from generated import health_pb2/g' \
        -e 's/^import informer_pb2/from generated import informer_pb2/g' \
        -e 's/^import analytics_pb2/from generated import analytics_pb2/g' \
      {} +
  fi
}

fix_imports "$INFORMER_OUT"
fix_imports "$ANALYTICS_OUT"

echo ""
echo "=== Done! ==="
echo "Informer stubs : $INFORMER_OUT"
echo "Analytics stubs: $ANALYTICS_OUT"
echo ""
echo "Generated files:"
find "$INFORMER_OUT" "$ANALYTICS_OUT" -type f \( -name "*.py" -o -name "*.pyi" \) | sort
