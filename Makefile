# Makefile — Top-level commands for the stock-micro-service monorepo.

.PHONY: proto help

# Regenerate protobuf stubs for all Python services
proto:
	@./protos/scripts/generate.sh

help:
	@echo "Available targets:"
	@echo "  make proto   — Regenerate protobuf stubs for informer + analytics"
	@echo "  make help    — Show this help message"
