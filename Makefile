# HELIOS — Synaptic Four unified local lifecycle

.PHONY: help install up down destroy dashboard logs solum-clinical-evidence test lint fmt

help:
	@echo "HELIOS — local lifecycle"
	@echo ""
	@echo "  make install     pip install -e '.[dev]'"
	@echo "  make test        ruff + mypy + pytest (CI parity)"
	@echo "  make lint        ruff check + format check + mypy"
	@echo "  make fmt         ruff --fix + format"
	@echo "  make up          Start optional audit dashboard (Docker; needs API key)"
	@echo "  make down        Stop dashboard; keep volumes"
	@echo "  make destroy     Stop dashboard; remove volumes"
	@echo "  make solum-clinical-evidence EXPORT=path.json"
	@echo ""
	@echo "Dashboard auth: export HELIOS_DASHBOARD_API_KEY=\$$(openssl rand -hex 32)"
	@echo "Signing keys:   export HELIOS_KEY_PASSPHRASE=... && helios key generate"

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/
	mypy src/helios/

test: lint
	pytest tests/ -v --tb=short --cov=helios --cov-report=term-missing --cov-fail-under=80

fmt:
	ruff check --fix src/ tests/
	ruff format src/ tests/

up: dashboard

dashboard:
	@if [ -z "$$HELIOS_DASHBOARD_API_KEY" ]; then \
		echo "ERROR: Set HELIOS_DASHBOARD_API_KEY before starting the dashboard."; \
		echo "  export HELIOS_DASHBOARD_API_KEY=\$$(openssl rand -hex 32)"; \
		echo "Or copy .env.example to .env and edit the value."; \
		exit 1; \
	fi
	docker compose up -d --build
	@echo "HELIOS dashboard: http://127.0.0.1:8765/static/index.html"
	@echo "Authenticate with the X-API-Key header (or the browser prompt)."

down:
	docker compose down --remove-orphans

destroy:
	docker compose down -v --remove-orphans
	@echo "HELIOS dashboard stack destroyed."

logs:
	docker compose logs -f

# Usage: make solum-clinical-evidence EXPORT=/path/to/pilot.solum-audit-helios-chain.json
solum-clinical-evidence:
	@if [ -z "$(EXPORT)" ]; then \
		echo "Usage: make solum-clinical-evidence EXPORT=/path/to/solum-audit-helios-chain.json"; \
		exit 1; \
	fi
	helios solum-audit --export "$(EXPORT)" $(if $(CONFIG),--config "$(CONFIG)",)
