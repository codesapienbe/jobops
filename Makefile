# JobOps Makefile
# Build and run modules: api, tray, clipper
# Usage:
#   make build <module>
#   make run <module>
#
# Modules: api, tray, clipper
#
# - api: FastAPI backend (Python, src/jobops_api)
# - tray: Tray desktop app (Python, src/jobops_tray)
# - clipper: Chrome extension (Node/TypeScript, src/jobops_clipper)
#
# Output: dist/<module>/

.PHONY: help build run build-api build-tray build-clipper run-api run-tray

MODULES := api tray clipper

help:
	@echo "Usage: make build <module> | make run <module>"
	@echo "Modules: api, tray, clipper"
	@echo "  build api     - Build JobOps API wheel (dist/jobops_api/)"
	@echo "  build tray    - Build JobOps Tray wheel (dist/jobops_tray/)"
	@echo "  build clipper - Build JobOps Clipper extension (dist/jobops_clipper/)"
	@echo "  run api       - Run JobOps API (FastAPI, uvicorn)"
	@echo "  run tray      - Run JobOps Tray desktop app"

# --- Build targets ---
build: build-$(filter $(word 2,$(MAKECMDGOALS)), $(MODULES))
	@:

build-api:
	cd src/jobops_api && uv sync && uv pip install -e .
	cd src/jobops_api && uv build --out-dir ../../dist/jobops_api/

build-tray:
	cd src/jobops_tray && uv sync && uv pip install -e .
	cd src/jobops_tray && uv build --out-dir ../../dist/jobops_tray/

build-clipper:
	cd src/jobops_clipper && npm install
	cd src/jobops_clipper && npm run build

# --- Run targets ---
run: run-$(filter $(word 2,$(MAKECMDGOALS)), $(MODULES))
	@:

run-api:
	cd src/jobops_api && uv run jobops_api

run-tray:
	cd src/jobops_tray && uv run jobops_tray

# --- Error handling for unknown targets ---
$(filter-out $(MODULES),$(word 2,$(MAKECMDGOALS))):
	@echo "Unknown module: '$(word 2,$(MAKECMDGOALS))'" >&2; exit 1 