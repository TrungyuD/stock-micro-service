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

# Clean previous output
rm -rf "$INFORMER_OUT" "$ANALYTICS_OUT"
mkdir -p "$INFORMER_OUT" "$ANALYTICS_OUT"

# Generate Informer stubs (pb2, grpc, pyi)
echo "→ Generating Informer service stubs..."
python3 -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$INFORMER_OUT" \
  --grpc_python_out="$INFORMER_OUT" \
  --pyi_out="$INFORMER_OUT" \
  "$PROTO_DIR/common/types.proto" \
  "$PROTO_DIR/informer.proto"

# Generate Analytics stubs (pb2, grpc, pyi)
echo "→ Generating Analytics service stubs..."
python3 -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$ANALYTICS_OUT" \
  --grpc_python_out="$ANALYTICS_OUT" \
  --pyi_out="$ANALYTICS_OUT" \
  "$PROTO_DIR/common/types.proto" \
  "$PROTO_DIR/analytics.proto"

# Create __init__.py so generated dirs are importable packages
touch "$INFORMER_OUT/__init__.py"
touch "$INFORMER_OUT/common/__init__.py" 2>/dev/null || true
touch "$ANALYTICS_OUT/__init__.py"
touch "$ANALYTICS_OUT/common/__init__.py" 2>/dev/null || true

# Fix relative imports: protoc generates bare imports that don't work
# when the generated dir is used as a Python package.
# 1. "from common import ..." → "from generated.common import ..."
# 2. "import informer_pb2" → "from generated import informer_pb2"
# 3. "import analytics_pb2" → "from generated import analytics_pb2"
echo "→ Fixing imports in generated files..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS sed requires '' after -i
  find "$INFORMER_OUT" -name "*.py" -o -name "*.pyi" | xargs sed -i '' 's/from common/from generated.common/g'
  find "$INFORMER_OUT" -name "*.py" | xargs sed -i '' 's/^import informer_pb2/from generated import informer_pb2/g'
  find "$ANALYTICS_OUT" -name "*.py" -o -name "*.pyi" | xargs sed -i '' 's/from common/from generated.common/g'
  find "$ANALYTICS_OUT" -name "*.py" | xargs sed -i '' 's/^import analytics_pb2/from generated import analytics_pb2/g'
else
  # Linux sed
  find "$INFORMER_OUT" -name "*.py" -o -name "*.pyi" | xargs sed -i 's/from common/from generated.common/g'
  find "$INFORMER_OUT" -name "*.py" | xargs sed -i 's/^import informer_pb2/from generated import informer_pb2/g'
  find "$ANALYTICS_OUT" -name "*.py" -o -name "*.pyi" | xargs sed -i 's/from common/from generated.common/g'
  find "$ANALYTICS_OUT" -name "*.py" | xargs sed -i 's/^import analytics_pb2/from generated import analytics_pb2/g'
fi

echo ""
echo "=== Done! ==="
echo "Informer stubs : $INFORMER_OUT"
echo "Analytics stubs: $ANALYTICS_OUT"
echo ""
echo "Generated files:"
find "$INFORMER_OUT" "$ANALYTICS_OUT" -type f -name "*.py" -o -name "*.pyi" | sort
