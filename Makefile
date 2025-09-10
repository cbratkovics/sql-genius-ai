.PHONY: dev up down api fmt lint test

up:
	docker compose -f infrastructure/docker/docker-compose.yml up -d

down:
	docker compose -f infrastructure/docker/docker-compose.yml down

api:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

fmt:
	ruff format && isort .

lint:
	ruff check . && mypy backend

test:
	pytest -q