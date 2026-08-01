# HELIOS — Synaptic Four unified local lifecycle

.PHONY: help install up down destroy dashboard logs

help:
	@echo "HELIOS — local lifecycle"
	@echo ""
	@echo "  make install     pip install -e . (from source; PyPI after v0.1.0)"
	@echo "  make up          Start optional audit dashboard (Docker; needs API key)"
	@echo "  make down        Stop dashboard; keep volumes"
	@echo "  make destroy     Stop dashboard; remove volumes"
	@echo ""
	@echo "Dashboard auth: export HELIOS_DASHBOARD_API_KEY=\$$(openssl rand -hex 32)"
	@echo "CLI-only (no Docker): helios init && helios run --pipeline nextflow ..."

install:
	pip install -e .

up: dashboard

dashboard:
	@if [ -z "$$HELIOS_DASHBOARD_API_KEY" ]; then \
		echo "ERROR: Set HELIOS_DASHBOARD_API_KEY before starting the dashboard."; \
		echo "  export HELIOS_DASHBOARD_API_KEY=\$$(openssl rand -hex 32)"; \
		echo "Or copy .env.example to .env and edit the value."; \
		exit 1; \
	fi
	docker compose up -d --build
	@echo "HELIOS dashboard: http://localhost:8765/static/index.html"
	@echo "Authenticate with the X-API-Key header (or the browser prompt)."

down:
	docker compose down --remove-orphans

destroy:
	docker compose down -v --remove-orphans
	@echo "HELIOS dashboard stack destroyed."

logs:
	docker compose logs -f
