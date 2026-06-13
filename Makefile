# HELIOS — Synaptic Four unified local lifecycle

.PHONY: help install up down destroy dashboard logs

help:
	@echo "HELIOS — local lifecycle"
	@echo ""
	@echo "  make install     pip install -e . (or: pip install helios-audit)"
	@echo "  make up          Start optional audit dashboard (Docker)"
	@echo "  make down        Stop dashboard; keep volumes"
	@echo "  make destroy     Stop dashboard; remove volumes"
	@echo ""
	@echo "CLI-only (no Docker): helios init && helios run --pipeline nextflow ..."

install:
	pip install -e .

up: dashboard

dashboard:
	docker compose up -d --build
	@echo "HELIOS dashboard: http://localhost:8765"

down:
	docker compose down --remove-orphans

destroy:
	docker compose down -v --remove-orphans
	@echo "HELIOS dashboard stack destroyed."

logs:
	docker compose logs -f
