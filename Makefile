.PHONY: dev up down api fmt lint test backend-check

up:
	docker compose -f infrastructure/docker/docker-compose.yml up -d

down:
	docker compose -f infrastructure/docker/docker-compose.yml down

api:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

fmt:
	ruff format && isort .

lint:
	./scripts/check-backend.sh lint
	./scripts/check-backend.sh types

test:
	./scripts/check-backend.sh tests

# Activate the locked Python 3.11 environment first.
backend-check:
	./scripts/check-backend.sh
