.PHONY: run lint format test docker-build docker-up docker-down docker-logs

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff .
	black --check .

format:
	black .

test:
	pytest --cov=app --cov-report=term-missing

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
